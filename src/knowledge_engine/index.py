import os
from pathlib import Path

from llama_index.core import Document as LlamaindexDocument
from llama_index.core import PropertyGraphIndex, StorageContext, load_index_from_storage
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

STORAGE_DIR = Path(os.getenv("KE_STORAGE_DIR", "./data/index"))


class KnowledgeIndex:
    def __init__(self) -> None:
        self._llm = OpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            temperature=0.1,
        )
        self._embed_model = OpenAIEmbedding(
            model_name=os.getenv("EMBED_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            api_base=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        )
        self._index = self._load_or_create()

    def _load_or_create(self) -> PropertyGraphIndex:
        if STORAGE_DIR.exists():
            try:
                sc = StorageContext.from_defaults(persist_dir=str(STORAGE_DIR))
                return load_index_from_storage(
                    storage_context=sc,
                    llm=self._llm,
                    embed_model=self._embed_model,
                )
            except (FileNotFoundError, ValueError):
                pass
        return PropertyGraphIndex(
            llm=self._llm,
            embed_model=self._embed_model,
            kg_extractors=[
                SchemaLLMPathExtractor(
                    llm=self._llm,
                    possible_entities=["Concept", "Person", "Tool", "Method", "Library"],
                    possible_relations=["depends_on", "implements", "relates_to", "part_of", "contrary_to"],
                    max_triplets_per_chunk=10,
                ),
            ],
            show_progress=False,
        )

    def insert_document(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        li_doc = LlamaindexDocument(text=content, id_=doc_id, metadata=metadata or {})
        self._index.insert(li_doc)

    def query(self, query_str: str, top_k: int = 5) -> str:
        retriever = self._index.as_retriever(
            include_text=True,
        )
        nodes = retriever.retrieve(query_str)
        if not nodes:
            return "No relevant information found."
        context = "\n\n".join(
            f"Source ({n.metadata.get('url', 'unknown')}):\n{n.text[:500]}"
            for n in nodes[:top_k]
        )
        response = self._llm.complete(
            f"Answer the question based on the context below.\n\n"
            f"Question: {query_str}\n\n"
            f"Context:\n{context}\n\n"
            f"Answer:"
        )
        return response.text

    def persist(self) -> None:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self._index.storage_context.persist(persist_dir=str(STORAGE_DIR))

    @property
    def stats(self) -> dict:
        store = self._index.property_graph_store
        return {
            "nodes": len(store.graph.nodes) if hasattr(store, "graph") and store.graph else 0,
            "relations": len(store.graph.edges) if hasattr(store, "graph") and store.graph else 0,
        }
