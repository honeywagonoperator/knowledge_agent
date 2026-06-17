import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from knowledge_engine.index import KnowledgeIndex


def make_index(mock_index: MagicMock | None = None) -> tuple[KnowledgeIndex, MagicMock]:
    mock_idx = mock_index or MagicMock()
    mock_llm = MagicMock()
    mock_embed = MagicMock()

    with (
        patch("knowledge_engine.index.OpenAI", return_value=mock_llm),
        patch("knowledge_engine.index.OpenAIEmbedding", return_value=mock_embed),
        patch.object(KnowledgeIndex, "_load_or_create", return_value=mock_idx),
    ):
        ki = KnowledgeIndex()

    return ki, mock_idx


# ── Init / Load ────────────────────────────────────────────────────────────────


def test_index_creates_new_when_no_storage():
    mock_new = MagicMock()

    with (
        patch("knowledge_engine.index.OpenAI"),
        patch("knowledge_engine.index.OpenAIEmbedding"),
        patch("knowledge_engine.index.SchemaLLMPathExtractor"),
        patch("knowledge_engine.index.PropertyGraphIndex", return_value=mock_new),
        patch("knowledge_engine.index.STORAGE_DIR", Path(tempfile.mkdtemp()) / "_nonexistent"),
    ):
        ki = KnowledgeIndex()

    assert ki._index == mock_new


def test_index_loads_existing_storage():
    mock_loaded = MagicMock()

    with (
        patch("knowledge_engine.index.OpenAI"),
        patch("knowledge_engine.index.OpenAIEmbedding"),
        patch("knowledge_engine.index.SchemaLLMPathExtractor"),
        patch("knowledge_engine.index.StorageContext"),
        patch("knowledge_engine.index.load_index_from_storage", return_value=mock_loaded),
        patch("knowledge_engine.index.STORAGE_DIR", Path(tempfile.gettempdir())),
    ):
        ki = KnowledgeIndex()

    assert ki._index == mock_loaded


def test_index_fallback_on_load_error():
    mock_new = MagicMock()

    with (
        patch("knowledge_engine.index.OpenAI"),
        patch("knowledge_engine.index.OpenAIEmbedding"),
        patch("knowledge_engine.index.SchemaLLMPathExtractor"),
        patch("knowledge_engine.index.StorageContext.from_defaults", side_effect=FileNotFoundError),
        patch("knowledge_engine.index.PropertyGraphIndex", return_value=mock_new),
        patch("knowledge_engine.index.STORAGE_DIR", Path(tempfile.gettempdir())),
    ):
        ki = KnowledgeIndex()

    assert ki._index == mock_new


# ── insert_document ────────────────────────────────────────────────────────────


def test_insert_document_calls_index_insert():
    mock_index = MagicMock()
    ki, _ = make_index(mock_index)

    ki.insert_document("doc_1", "content", {"url": "https://x.com"})

    mock_index.insert.assert_called_once()
    call_doc = mock_index.insert.call_args[0][0]
    assert call_doc.text == "content"
    assert call_doc.id_ == "doc_1"
    assert call_doc.metadata == {"url": "https://x.com"}


def test_insert_document_without_metadata():
    mock_index = MagicMock()
    ki, _ = make_index(mock_index)

    ki.insert_document("doc_2", "text")

    call_doc = mock_index.insert.call_args[0][0]
    assert call_doc.text == "text"
    assert call_doc.metadata == {}


# ── query ──────────────────────────────────────────────────────────────────────


def test_query_returns_answer():
    mock_node = MagicMock()
    mock_node.text = "Relevant info"
    mock_node.metadata = {"url": "https://example.com"}

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [mock_node]

    mock_llm = MagicMock()
    mock_llm.complete.return_value.text = "The answer is 42."

    mock_index = MagicMock()
    mock_index.as_retriever.return_value = mock_retriever

    ki, _ = make_index(mock_index)
    ki._llm = mock_llm

    answer = ki.query("what is the answer?")

    assert "The answer is 42" in answer
    mock_retriever.retrieve.assert_called_once_with("what is the answer?")


def test_query_no_results():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []

    mock_index = MagicMock()
    mock_index.as_retriever.return_value = mock_retriever

    ki, _ = make_index(mock_index)

    answer = ki.query("nothing")

    assert "No relevant information found" in answer


# ── persist ────────────────────────────────────────────────────────────────────


def test_persist_creates_dir_and_saves():
    mock_index = MagicMock()
    ki, _ = make_index(mock_index)

    with (
        patch("knowledge_engine.index.STORAGE_DIR", Path("/tmp/test_persist")),
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        ki.persist()

    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_index.storage_context.persist.assert_called_once_with(
        persist_dir=str(Path("/tmp/test_persist"))
    )


# ── stats ──────────────────────────────────────────────────────────────────────


def test_stats_empty():
    mock_graph = MagicMock()
    mock_graph.nodes = []
    mock_graph.edges = []

    mock_graph_store = MagicMock()
    mock_graph_store.graph = mock_graph

    mock_index = MagicMock()
    mock_index.property_graph_store = mock_graph_store

    ki, _ = make_index(mock_index)
    stats = ki.stats

    assert stats["nodes"] == 0
    assert stats["relations"] == 0


def test_stats_with_data():
    mock_graph = MagicMock()
    mock_graph.nodes = {"a": 1, "b": 2}
    mock_graph.edges = MagicMock()

    mock_graph_store = MagicMock()
    mock_graph_store.graph = mock_graph

    mock_index = MagicMock()
    mock_index.property_graph_store = mock_graph_store

    ki, _ = make_index(mock_index)
    stats = ki.stats

    assert stats["nodes"] == 2


def test_stats_no_graph():
    mock_graph_store = MagicMock()
    mock_graph_store.graph = None

    mock_index = MagicMock()
    mock_index.property_graph_store = mock_graph_store

    ki, _ = make_index(mock_index)
    stats = ki.stats

    assert stats["nodes"] == 0
    assert stats["relations"] == 0
