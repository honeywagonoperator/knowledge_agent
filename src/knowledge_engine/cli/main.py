import asyncio
import click
from knowledge_engine.db.session import async_session_factory
from knowledge_engine.db.engine import dispose_engine
from knowledge_engine.connectors.sync_service import SyncService

@click.group()
def cli() -> None:
    pass

@cli.command()
@click.option("--url", required=True, help="Source URL")
@click.option("--type", "source_type", default="url", type=click.Choice(["url", "telegram"]))
@click.option("--name", default=None, help="Source name")
def add_source(url: str, source_type: str, name: str | None) -> None:
    async def _run() -> None:
        factory = async_session_factory()
        async with factory() as session:
            service = SyncService(session)
            source = await service.add_source(url, source_type, name)
            await session.commit()
            click.echo(f"Source added: {source.id} ({source.name})")
    asyncio.run(_run())

@cli.command()
@click.option("--source-id", required=True, help="Source UUID")
def sync(source_id: str) -> None:
    async def _run() -> None:
        from uuid import UUID
        factory = async_session_factory()
        async with factory() as session:
            service = SyncService(session)
            result = await service.sync_source(UUID(source_id))
            await session.commit()
            click.echo(f"Synced: {result.documents_created} created, {result.documents_skipped} skipped")
            if result.errors:
                for err in result.errors:
                    click.echo(f"  Error: {err}")
    asyncio.run(_run())

@cli.command()
@click.argument("query")
def query(query: str) -> None:
    click.echo("Query not yet implemented (Issue 7)")

if __name__ == "__main__":
    cli()
