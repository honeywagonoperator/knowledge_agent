# Knowledge Engine (Personal AI + Knowledge Graph)

## Vision

Личный AI-агент, который:

- собирает знания из Telegram-каналов и URL
- превращает их в структурированные knowledge units
- строит поверх них knowledge graph (entities + relations)
- использует hybrid retrieval (vector + graph)
- отвечает с обязательными ссылками на источники

---

# 🧠 Core Idea

Не строим “RAG по текстам”.

Строим:

Knowledge Units (истина)
        ↓
Vector Layer (поиск)
        ↓
Graph Layer (связи)
        ↓
LLM Agent (синтез)
        ↓
Ответ + источники

---

# 🏗️ High-Level Architecture

                     ┌────────────────────┐
                     │   OpenCode Agent   │
                     └─────────┬──────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Knowledge Service    │
                    │ (core logic)         │
                    └─────────┬────────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼

 Connectors            Knowledge Layer         Graph Layer
 (Telegram, URL)       (units + vector)       (entities + relations)

                              │
                              ▼
                  PostgreSQL + pgvector

---

# 🧱 Data Model (Graph-ready + RAG)

## Sources
- id
- type
- name
- url
- enabled
- last_sync

## Documents
- id
- source_id
- title
- content
- url
- content_hash
- created_at

## Knowledge Units
- id
- document_id
- type
- content
- domain
- confidence
- embedding
- created_at

## Entities
- id (STRING)
- name
- type
- canonical
- created_at

## Relations
- id
- from_entity_id
- to_entity_id
- relation_type
- confidence
- weight
- source_knowledge_unit_id
- source_quote

---

# 🔁 Processing Pipeline

Telegram / URL
        ↓
Document creation
        ↓
Knowledge extraction
        ↓
Knowledge units
        ↓
Entity extraction
        ↓
Relation extraction
        ↓
Graph storage
        ↓
Embeddings

---

# 🔍 Retrieval Pipeline

1. Vector search
2. Entity extraction
3. Graph expansion
4. Context building
5. LLM response

---

# 💬 Answer System

Each answer MUST include:

## Answer
Полный и развёрнутый, раскрывающий суть вопроса. Должен быть grounded в knowledge base.

## Sources (обязательно)
- channel / url
- relevant insights

## Trace (optional)
Why this answer was produced

---

# ⚙️ Features

- add_source
- sync
- search
- advise
- graph expansion
- source-aware responses

---

# 🧠 Design Decisions

- Postgres = source of truth
- Graph = derived layer
- Knowledge Units > Documents
- Hybrid retrieval = vector + graph
- Stable entity IDs for future Neo4j migration

---

# 🛠️ Tech Stack

## LLM (гибридная стратегия)

| Назначение | Провайдер | Модель |
|---|---|---|
| Ответы пользователю, сложные задачи | OpenRouter (OpenAI-compatible API) | GPT-4o-mini / Claude Sonnet |
| Knowledge extraction, entities, relations | Ollama (локально) | LLaMA 3 / Qwen 2.5 |
| Embeddings | OpenRouter / Ollama | text-embedding-3-small / nomic-embed-text |

Абстракция через LlamaIndex `Settings` — `llm` и `embed_model` подменяются в рантайме.

## Framework

**LlamaIndex** — PropertyGraphIndex, SchemaLLMPathExtractor:
- Chunking документов
- Извлечение entities + relations (кастомные типы через схему)
- Хранение графа в PostgreSQL (SimplePropertyGraphStore)
- Hybrid retrieval (vector search + graph traversal)

## База данных

**PostgreSQL + pgvector** — единая база:
- SQLAlchemy 2.0 async + asyncpg
- SimplePropertyGraphStore для графа (встроен в LlamaIndex)
- Кастомные модели: Sources, Documents, Knowledge Units

## Коннекторы

| Источник | Библиотека |
|---|---|
| Telegram | python-telegram-bot (async) |
| URL | httpx + beautifulsoup4 / selectolax |

## Архитектура приложения

**Python-библиотека** (без REST API). Вызов напрямую из OpenCode.

## Dev-инструменты

- pytest + pytest-asyncio
- ruff (линтер)
- mypy (тайп-чекинг)

---

# 🎯 MVP Goal

- ingest Telegram + URLs
- extract knowledge
- build graph
- answer with sources
