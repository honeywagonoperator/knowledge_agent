# Knowledge Engine (Personal AI + Knowledge Graph)

## Vision

Личный AI-агент, который:

- собирает знания из Telegram-каналов и URL
- превращает их в knowledge graph (entities + relations)
- использует hybrid retrieval (vector + graph) через LlamaIndex
- отвечает с обязательными ссылками на источники

---

# 🧠 Core Idea

```
Documents → LlamaIndex PropertyGraphIndex → KG (вектора + граф на диске)
                                                    ↓
        LLM (OpenRouter) ← синтез ответа ← retriever (vector + graph)
```

---

# 🏗️ High-Level Architecture

```
                    ┌────────────────────┐
                    │   OpenCode Agent   │
                    └─────────┬──────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │ Knowledge Service    │
                   │ (index.py + CLI)     │
                   └─────────┬────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                     ▼
  Connectors           PropertyGraphIndex     PostgreSQL
  (Telethon, httpx)    (LlamaIndex)           (Sources + Docs)
                              │
                              ▼
                    ./data/index/ (persist на диск)
                    ├ graph.json
                    └ vector_store.json
```

---

# 🧱 Data Model

## PostgreSQL (только Sources + Documents для CLI и трекинга)

| Таблица | Назначение |
|---------|-----------|
| `sources` | `ke add-source`, `ke list-sources`, `ke status` |
| `documents` | content_hash dedup, хранение сырого контента |

## PropertyGraphIndex (LlamaIndex, на диске)

| Компонент | Хранилище |
|-----------|-----------|
| Chunks (Node) | `SimpleVectorStore` → `./data/index/vector_store.json` |
| Embeddings | `SimpleVectorStore` |
| Entity nodes | `SimplePropertyGraphStore` → `./data/index/property_graph_store.json` |
| Relations | `SimplePropertyGraphStore` |

---

# 🔁 Processing Pipeline

```
ke sync
  │
  ├── Connector (URL/Telegram) → Document → PostgreSQL
  │
  └── index.insert(Document)
        │
        ├── SentenceSplitter → chunks
        ├── OpenAIEmbedding → vectors
        ├── SchemaLLMPathExtractor → entities + relations
        └── persist ./data/index/
```

---

# 🔍 Retrieval Pipeline

```
ke query "вопрос"
  │
  ├── PropertyGraphIndex.as_retriever()
  │     ├── VectorContextRetriever (cosine similarity по чанкам)
  │     └── LLMSynonymRetriever (entity extraction → graph traversal)
  │
  ├── Context: top-5 chunks + их графовые связи
  │
  └── OpenRouter (GPT-4o-mini) → ответ с source URLs
```

---

# 💬 Answer System

Each answer MUST include:

## Answer
Полный и развёрнутый, grounded в knowledge base.

## Sources (обязательно)
- url / channel
- relevant insights

---

# 🛠️ Tech Stack

## LLM

| Назначение | Провайдер | Модель |
|---|---|---|
| Ответы, extraction, синтез | OpenRouter | GPT-4o-mini / Claude Sonnet |
| Embeddings | OpenRouter | text-embedding-3-small |

## Framework

**LlamaIndex PropertyGraphIndex:**
- `SentenceSplitter` — chunking
- `SchemaLLMPathExtractor` — entity/relation extraction (через LLM)
- `SimpleVectorStore` — хранение векторов
- `SimplePropertyGraphStore` — хранение графа

Обёртка: `knowledge_engine/index.py` — `KnowledgeIndex` (init, insert, query, persist/load)

## База данных

**PostgreSQL** — только для:
- `sources` — управление источниками (CLI)
- `documents` — контент + dedup

pgvector extension не требуется (вектора в SimpleVectorStore на диске).

## Коннекторы

| Источник | Библиотека |
|---|---|
| Telegram | Telethon |
| URL | httpx + beautifulsoup4 |

## Архитектура приложения

**Python-библиотека + CLI** (`ke` commands). Вызов напрямую из OpenCode.

## Dev-инструменты

- pytest + pytest-asyncio 0.24.0
- ruff (линтер)
- mypy (тайп-чекинг)

## Docker-окружение

**docker-compose.yml** — только PostgreSQL (чистый, без pgvector):
- `postgres:16-alpine`
- Никаких LLM-сервисов (всё через OpenRouter API)

---

# 🧠 Design Decisions

| Решение | Причина |
|---------|---------|
| PropertyGraphIndex вместо кастомных таблиц | LlamaIndex даёт extraction + retrieval из коробки |
| Граф на диске, не в PostgreSQL | SimplePropertyGraphStore не поддерживает PG; PostgreSQL только для CLI-данных |
| OpenRouter вместо локального Ollama | Не нужно GPU, единый API, дешевле чем держать сервер |
| Telethon вместо python-telegram-bot | Лучшая поддержка асинхронности, проще авторизация |

---

# 🎯 MVP Goal

- ingest Telegram + URLs
- build knowledge graph
- answer with sources
