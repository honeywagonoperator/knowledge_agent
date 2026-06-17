import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from knowledge_engine.cli.main import cli
from knowledge_engine.connectors.base import SyncResult
from knowledge_engine.models.source import Source, SourceType

runner = CliRunner()


def source_factory() -> Source:
    return Source(id=uuid.uuid4(), type=SourceType.URL, name="Test", url="https://test.com", enabled=True)


# ── add-source ─────────────────────────────────────────────────────────────────


def test_add_source_ok():
    mock_src = source_factory()
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_repo_instance = MagicMock()
    mock_repo_instance.add = AsyncMock(return_value=mock_src)

    with (
        patch("knowledge_engine.cli.main.async_session_factory") as mock_factory,
        patch("knowledge_engine.cli.main.Repository") as mock_repo_cls,
    ):
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_repo_cls.return_value = mock_repo_instance

        result = runner.invoke(cli, ["add-source", "--url", "https://test.com"])

    assert result.exit_code == 0
    assert "Source added" in result.output
    mock_repo_instance.add.assert_awaited_once()


def test_add_source_with_name():
    mock_src = source_factory()
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_repo_instance = MagicMock()
    mock_repo_instance.add = AsyncMock(return_value=mock_src)

    with (
        patch("knowledge_engine.cli.main.async_session_factory") as mock_factory,
        patch("knowledge_engine.cli.main.Repository") as mock_repo_cls,
    ):
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_repo_cls.return_value = mock_repo_instance

        result = runner.invoke(cli, ["add-source", "--url", "https://tg", "--type", "telegram", "--name", "MyChannel"])

    assert result.exit_code == 0
    assert "Source added" in result.output


# ── sync ───────────────────────────────────────────────────────────────────────


def test_sync_source_not_found():
    mock_session = AsyncMock()
    mock_repo_instance = MagicMock()
    mock_repo_instance.get = AsyncMock(return_value=None)

    with (
        patch("knowledge_engine.cli.main.async_session_factory") as mock_factory,
        patch("knowledge_engine.cli.main.Repository") as mock_repo_cls,
    ):
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_repo_cls.return_value = mock_repo_instance

        result = runner.invoke(cli, ["sync", "--source-id", str(uuid.uuid4())])

    assert result.exit_code == 0
    assert "not found" in result.output.lower()


def test_sync_ok():
    mock_src = source_factory()
    mock_session = AsyncMock()
    mock_repo_instance = MagicMock()
    mock_repo_instance.get = AsyncMock(return_value=mock_src)
    mock_session.commit = AsyncMock()

    mock_connector = MagicMock()
    mock_connector_cls = MagicMock(return_value=mock_connector)

    mock_service = MagicMock()
    mock_service.sync_source = AsyncMock(return_value=SyncResult(source_id=mock_src.id, documents_created=3))
    mock_service_cls = MagicMock(return_value=mock_service)

    mock_index = MagicMock()

    with (
        patch("knowledge_engine.cli.main.async_session_factory") as mock_factory,
        patch("knowledge_engine.cli.main.Repository") as mock_repo_cls,
        patch("knowledge_engine.connectors.url.URLConnector", mock_connector_cls),
        patch("knowledge_engine.connectors.sync_service.SyncService", mock_service_cls),
        patch("knowledge_engine.cli.main.KnowledgeIndex") as mock_index_cls,
    ):
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_repo_cls.return_value = mock_repo_instance

        result = runner.invoke(cli, ["sync", "--source-id", str(mock_src.id)])

    assert result.exit_code == 0
    assert "3 created" in result.output
    mock_service.sync_source.assert_awaited_once()


# ── query ──────────────────────────────────────────────────────────────────────


def test_query_ok():
    with (
        patch("knowledge_engine.cli.main.KnowledgeIndex") as mock_index_cls,
    ):
        mock_index = MagicMock()
        mock_index.query.return_value = "Python is a programming language."
        mock_index_cls.return_value = mock_index

        result = runner.invoke(cli, ["query", "What is Python?"])

    assert result.exit_code == 0
    assert "Python is a programming language" in result.output


def test_query_no_results():
    with patch("knowledge_engine.cli.main.KnowledgeIndex") as mock_index_cls:
        mock_index = MagicMock()
        mock_index.query.return_value = "No relevant information found."
        mock_index_cls.return_value = mock_index

        result = runner.invoke(cli, ["query", "unknown"])

    assert result.exit_code == 0
    assert "No relevant information found" in result.output


# ── list-sources ────────────────────────────────────────────────────────────────


def test_list_sources_empty():
    mock_session = AsyncMock()
    mock_repo_instance = MagicMock()
    mock_repo_instance.list = AsyncMock(return_value=[])

    with (
        patch("knowledge_engine.cli.main.async_session_factory") as mock_factory,
        patch("knowledge_engine.cli.main.Repository") as mock_repo_cls,
    ):
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_repo_cls.return_value = mock_repo_instance

        result = runner.invoke(cli, ["list-sources"])

    assert result.exit_code == 0
    assert "No sources" in result.output


def test_list_sources_with_data():
    src = source_factory()
    mock_session = AsyncMock()
    mock_repo_instance = MagicMock()
    mock_repo_instance.list = AsyncMock(return_value=[src])

    with (
        patch("knowledge_engine.cli.main.async_session_factory") as mock_factory,
        patch("knowledge_engine.cli.main.Repository") as mock_repo_cls,
    ):
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_repo_cls.return_value = mock_repo_instance

        result = runner.invoke(cli, ["list-sources"])

    assert result.exit_code == 0
    assert "Test" in result.output


# ── status ─────────────────────────────────────────────────────────────────────


def test_status_ok():
    mock_session = AsyncMock()
    mock_repo_instance = MagicMock()
    mock_repo_instance.count = AsyncMock(side_effect=[2, 5])

    mock_index = MagicMock()
    mock_index.stats = {"nodes": 10, "relations": 3}

    with (
        patch("knowledge_engine.cli.main.async_session_factory") as mock_factory,
        patch("knowledge_engine.cli.main.Repository") as mock_repo_cls,
        patch("knowledge_engine.cli.main.KnowledgeIndex") as mock_index_cls,
    ):
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_repo_cls.return_value = mock_repo_instance
        mock_index_cls.return_value = mock_index

        result = runner.invoke(cli, ["status"])

    assert result.exit_code == 0
    assert "Sources" in result.output
    assert "Documents" in result.output
    assert "Graph Nodes" in result.output or "Graph Relations" in result.output


# ── graph-explore ──────────────────────────────────────────────────────────────


def test_graph_explore_no_data():
    mock_graph_store = MagicMock()
    mock_graph_store.graph = None

    mock_index = MagicMock()
    mock_index._index = MagicMock()
    mock_index._index.property_graph_store = mock_graph_store

    with patch("knowledge_engine.cli.main.KnowledgeIndex") as mock_index_cls:
        mock_index_cls.return_value = mock_index

        result = runner.invoke(cli, ["graph-explore", "--entity", "Python"])

    assert result.exit_code == 0
    assert "No graph data" in result.output


def test_graph_explore_no_match():
    mock_graph = MagicMock()
    mock_graph.nodes = ["Java", "C++"]
    mock_graph.edges = MagicMock(return_value=[])

    mock_graph_store = MagicMock()
    mock_graph_store.graph = mock_graph

    mock_index = MagicMock()
    mock_index._index = MagicMock()
    mock_index._index.property_graph_store = mock_graph_store

    with patch("knowledge_engine.cli.main.KnowledgeIndex") as mock_index_cls:
        mock_index_cls.return_value = mock_index

        result = runner.invoke(cli, ["graph-explore", "--entity", "Python"])

    assert result.exit_code == 0
    assert "No entities found" in result.output


# ── advise ─────────────────────────────────────────────────────────────────────


def test_advise_exit_immediately():
    mock_index = MagicMock()
    with patch("knowledge_engine.cli.main.KnowledgeIndex") as mock_index_cls:
        mock_index_cls.return_value = mock_index

        result = runner.invoke(cli, ["advise"], input="exit\n")

    assert result.exit_code == 0


def test_advise_single_question():
    mock_index = MagicMock()
    mock_index.query.return_value = "Answer from knowledge base."

    with patch("knowledge_engine.cli.main.KnowledgeIndex") as mock_index_cls:
        mock_index_cls.return_value = mock_index

        result = runner.invoke(cli, ["advise"], input="What is AI?\nexit\n")

    assert result.exit_code == 0
    assert "Answer from knowledge base" in result.output
