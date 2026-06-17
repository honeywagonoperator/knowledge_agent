import asyncio
from uuid import UUID
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from knowledge_engine.db.engine import dispose_engine
from knowledge_engine.db.session import async_session_factory
from knowledge_engine.db.repository import Repository
from knowledge_engine.models.source import Source
from knowledge_engine.models.document import Document
from knowledge_engine.models.knowledge_unit import KnowledgeUnit
from knowledge_engine.models.entity import Entity, EntityType
from knowledge_engine.models.relation import Relation

console = Console()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--url", required=True, help="Source URL")
@click.option("--type", "source_type", default="url",
              type=click.Choice(["url", "telegram"]))
@click.option("--name", default=None, help="Optional source name")
def add_source(url: str, source_type: str, name: str | None) -> None:
    """Add a new knowledge source (URL or Telegram)."""
    async def _run():
        from knowledge_engine.models.source import SourceType as ST
        factory = async_session_factory()
        async with factory() as s:
            repo = Repository(s, Source)
            src = Source(type=ST(source_type), name=name or url, url=url)
            await repo.add(src)
            await s.commit()
            console.print(f"[green]Source added:[/] {src.id} ({src.name})")
    asyncio.run(_run())


@cli.command()
@click.option("--source-id", required=True, help="Source UUID to sync")
def sync(source_id: str) -> None:
    """Synchronize a source (fetch, chunk, extract, graph)."""
    console.print("[yellow]Sync requires the full pipeline. Use feat/url-connector branch.[/]")
    console.print(f"Source ID: {source_id}")


@cli.command()
@click.argument("query_str")
@click.option("--expand/--no-expand", default=True)
@click.option("--depth", default=1, help="Graph expansion depth")
def query(query_str: str, expand: bool, depth: int) -> None:
    """Ask a question against the knowledge base."""
    console.print("[yellow]Query requires feat/hybrid-retrieval branch for full pipeline.[/]")
    console.print(f"Question: {query_str}")


@cli.command()
@click.option("--entity", required=True, help="Entity name to explore")
@click.option("--depth", default=2, help="Graph traversal depth")
def graph_explore(entity: str, depth: int) -> None:
    """Explore entity connections in the knowledge graph."""
    async def _run():
        factory = async_session_factory()
        async with factory() as s:
            from sqlalchemy import select, or_
            entity_result = await s.execute(
                select(Entity).where(Entity.name.ilike(f"%{entity}%"))
            )
            entities = entity_result.scalars().all()

            if not entities:
                console.print(f"[yellow]No entities found matching '{entity}'[/]")
                return

            table = Table(title=f"Entity: {entity}")
            table.add_column("Entity ID", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Name")
            table.add_column("Relations", style="green")

            for ent in entities:
                rel_result = await s.execute(
                    select(Relation).where(
                        or_(Relation.from_entity_id == ent.id,
                            Relation.to_entity_id == ent.id)
                    ).limit(10)
                )
                relations = rel_result.scalars().all()
                rel_summary = ", ".join(
                    f"{r.relation_type.value}" for r in relations
                ) or "none"

                table.add_row(ent.id, ent.type.value, ent.name, rel_summary)

            console.print(table)
    asyncio.run(_run())


@cli.command()
def list_sources() -> None:
    """List all configured sources."""
    async def _run():
        factory = async_session_factory()
        async with factory() as s:
            repo = Repository(s, Source)
            sources = await repo.list()
            if not sources:
                console.print("[yellow]No sources configured.[/]")
                return
            table = Table(title="Sources")
            table.add_column("ID", style="dim")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("Enabled")
            table.add_column("Last Sync")
            for src in sources:
                table.add_row(
                    str(src.id)[:8],
                    src.name,
                    src.type.value,
                    "yes" if src.enabled else "no",
                    str(src.last_sync or "never"),
                )
            console.print(table)
    asyncio.run(_run())


@cli.command()
def status() -> None:
    """Show knowledge base statistics."""
    async def _run():
        factory = async_session_factory()
        async with factory() as s:
            source_repo = Repository(s, Source)
            doc_repo = Repository(s, Document)
            unit_repo = Repository(s, KnowledgeUnit)

            from knowledge_engine.db.repository import Repository as Repo
            entity_repo = Repo(s, Entity)
            rel_repo = Repo(s, Relation)

            src_count = await source_repo.count()
            doc_count = await doc_repo.count()
            unit_count = await unit_repo.count()
            ent_count = await entity_repo.count()
            rel_count = await rel_repo.count()

            panel = Panel.fit(
                f"[bold]Knowledge Engine Status[/]\n\n"
                f"Sources:          {src_count}\n"
                f"Documents:        {doc_count}\n"
                f"Knowledge Units:  {unit_count}\n"
                f"Entities:         {ent_count}\n"
                f"Relations:        {rel_count}",
                border_style="green",
            )
            console.print(panel)
    asyncio.run(_run())


@cli.command()
@click.option("--model", default="gpt-4o-mini",
              help="LLM model for responses")
def advise(model: str) -> None:
    """Interactive multi-turn Q&A session."""
    console.print("[bold green]Knowledge Engine — Advise Mode[/]")
    console.print("[dim]Type 'exit' or 'quit' to end.[/]\n")

    history: list[dict] = []

    async def _advise_loop():
        loop = asyncio.get_running_loop()
        while True:
            question = await loop.run_in_executor(
                None, lambda: console.input("[bold cyan]You:[/] ")
            )
            if question.lower() in ("exit", "quit"):
                break

            history.append({"role": "user", "content": question})
            answer = await _do_answer(question)
            history.append({"role": "assistant", "content": answer})
            console.print(f"[bold green]KE:[/] {answer}\n")

    async def _do_answer(q: str) -> str:
        factory = async_session_factory()
        async with factory() as s:
            from sqlalchemy import select
            result = await s.execute(
                select(KnowledgeUnit).where(
                    KnowledgeUnit.content.ilike(f"%{q}%")
                ).limit(3)
            )
            units = result.scalars().all()
            if units:
                ctx = "\n\n".join(
                    f"[{u.domain}] {u.content[:300]}" for u in units
                )
                return f"Found {len(units)} relevant knowledge units.\n\n{ctx}"
            return "No relevant knowledge found. Try adding a source first."

    asyncio.run(_advise_loop())


if __name__ == "__main__":
    cli()
