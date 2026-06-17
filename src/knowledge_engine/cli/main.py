import asyncio
import uuid

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from knowledge_engine.db.repository import Repository
from knowledge_engine.db.session import async_session_factory
from knowledge_engine.index import KnowledgeIndex
from knowledge_engine.models.document import Document
from knowledge_engine.models.source import Source

console = Console()


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--url", required=True, help="Source URL")
@click.option("--type", "source_type", default="url",
              type=click.Choice(["url", "telegram"]))
@click.option("--name", default=None, help="Optional source name")
def add_source(url: str, source_type: str, name: str | None) -> None:
    """Add a new knowledge source (URL or Telegram)."""
    async def _run() -> None:
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
    """Synchronize a source (fetch, index, build graph)."""
    async def _run() -> None:
        from knowledge_engine.connectors.sync_service import SyncService
        from knowledge_engine.connectors.url import URLConnector
        factory = async_session_factory()
        async with factory() as s:
            repo = Repository(s, Source)
            src = await repo.get(uuid.UUID(source_id))
            if src is None:
                console.print("[red]Source not found[/]")
                return
            connector = URLConnector(src, s)
            index = KnowledgeIndex()
            service = SyncService(s, index)
            result = await service.sync_source(connector)
            await s.commit()
            console.print(f"[green]Sync complete:[/] {result.documents_created} created, {result.documents_skipped} skipped")
            if result.errors:
                for err in result.errors:
                    console.print(f"[red]Error:[/] {err}")
    asyncio.run(_run())


@cli.command()
@click.argument("query_str")
def query(query_str: str) -> None:
    """Ask a question against the knowledge base."""
    index = KnowledgeIndex()
    answer = index.query(query_str)
    console.print(f"[bold green]Answer:[/] {answer}")


@cli.command()
@click.option("--entity", required=True, help="Entity name to explore")
@click.option("--depth", default=2, help="Graph traversal depth")
def graph_explore(entity: str, depth: int) -> None:
    """Explore entity connections in the knowledge graph."""
    index = KnowledgeIndex()
    store = index._index.property_graph_store
    if not hasattr(store, "graph") or not store.graph:
        console.print("[yellow]No graph data available.[/]")
        return
    nodes = [n for n in store.graph.nodes if entity.lower() in n.lower()]
    if not nodes:
        console.print(f"[yellow]No entities found matching '{entity}'[/]")
        return
    table = Table(title=f"Entity: {entity}")
    table.add_column("Entity", style="cyan")
    table.add_column("Connected To", style="green")
    table.add_column("Relation")
    for n in nodes:
        for edge in store.graph.edges(n, data=True):
            table.add_row(n, edge[1], edge[2].get("label", "related"))
    console.print(table)


@cli.command()
def list_sources() -> None:
    """List all configured sources."""
    async def _run() -> None:
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
    async def _run() -> None:
        factory = async_session_factory()
        async with factory() as s:
            source_repo = Repository(s, Source)
            doc_repo = Repository(s, Document)

            src_count = await source_repo.count()
            doc_count = await doc_repo.count()

        index = KnowledgeIndex()
        idx_stats = index.stats

        panel = Panel.fit(
            f"[bold]Knowledge Engine Status[/]\n\n"
            f"Sources:          {src_count}\n"
            f"Documents:        {doc_count}\n"
            f"Graph Nodes:      {idx_stats['nodes']}\n"
            f"Graph Relations:  {idx_stats['relations']}",
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

    index = KnowledgeIndex()
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
            answer = index.query(question)
            history.append({"role": "assistant", "content": answer})
            console.print(f"[bold green]KE:[/] {answer}\n")

    asyncio.run(_advise_loop())


if __name__ == "__main__":
    cli()
