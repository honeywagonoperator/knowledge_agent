import asyncio; from uuid import UUID
import click
from knowledge_engine.db.session import async_session_factory
from knowledge_engine.db.engine import dispose_engine
from knowledge_engine.connectors.sync_service import SyncService

@click.group()
def cli(): pass

@cli.command()
@click.option("--url", required=True); @click.option("--type", "source_type", default="url", type=click.Choice(["url", "telegram"]))
@click.option("--name", default=None)
def add_source(url: str, source_type: str, name: str | None) -> None:
    async def _run():
        factory = async_session_factory()
        async with factory() as s:
            svc = SyncService(s); src = await svc.add_source(url, source_type, name); await s.commit()
            click.echo(f"Source added: {src.id} ({src.name})")
    asyncio.run(_run())

@cli.command()
@click.option("--source-id", required=True)
def sync(source_id: str) -> None:
    async def _run():
        factory = async_session_factory()
        async with factory() as s:
            svc = SyncService(s); r = await svc.sync_source(UUID(source_id)); await s.commit()
            click.echo(f"Synced: {r.documents_created} docs, {r.documents_skipped} skipped")
            for err in r.errors: click.echo(f"  Error: {err}")
    asyncio.run(_run())

@cli.command()
@click.argument("query")
def query(query: str) -> None: click.echo("Query not yet implemented (Issue 7)")

if __name__ == "__main__": cli()
