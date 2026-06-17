# SESSION.md — Knowledge Engine

## 2026-06-17 — Создание issues для Knowledge Engine

**Action:** Создаю 9 GitHub issues с Acceptance Criteria по утверждённому фича-листу

**Rationale:** Фиксируем план работ в GitHub Issues для трекинга прогресса

**Labels:** `feature` — для всех, `mvp` — для первых 7 (приоритет MVP)

**Trade-offs:** Разбивка на 9 вертикальных slices, каждый issue — законченный модуль, который можно имплементировать и протестировать независимо



## 2026-06-17 — Все 9 issues созданы

**Action:** Создал issues #1-#9 в репозитории honeywagonoperator/knowledge_agent

**Results:**
- #1 Project Scaffold
- #2 Data Models
- #3 Database Layer
- #4 URL Connector
- #5 Knowledge Extraction
- #6 Entity & Relation Extraction
- #7 Hybrid Retrieval + Answer
- #8 Telegram Connector
- #9 CLI — adv режим

**Blockers:** MCP-сервер GitHub не принимает новый токен. Работаю через GitHub REST API напрямую.



## 2026-06-17 — Issue 1: Project Scaffold completed

**Action:** Создал feature branch feat/project-scaffold, залил 10 файлов скелета, открыл Draft PR #10

**Files:**
- pyproject.toml (deps: SQLAlchemy, asyncpg, LlamaIndex, httpx, bs4, python-telegram-bot, click, alembic)
- src/knowledge_engine/{cli,models,db,connectors,extractors,retrieval}/__init__.py
- Makefile (install, dev, lint, typecheck, test, clean)
- .gitignore

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/10



## 2026-06-17 — Issue 2: Data Models completed

**Action:** Создал ветку feat/data-models, SQLAlchemy модели для всех 5 таблиц + PR #11

**Files:**
- models/base.py — Base, TimestampMixin, UUIDMixin
- models/source.py — Source (SourceType enum: telegram/url)
- models/document.py — Document (unique content_hash)
- models/knowledge_unit.py — KnowledgeUnit (pgvector embedding)
- models/entity.py — Entity (string PK for Neo4j compat)
- models/relation.py — Relation (enum relation_type, source_quote)

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/11



## 2026-06-17 — Issue 3: Database Layer completed

**Action:** feat/db-layer branch + PR #12

**Files:**
- db/config.py — DatabaseConfig dataclass (env vars)
- db/engine.py — AsyncEngine singleton
- db/session.py — async session factory context manager
- db/repository.py — Generic CRUD Repository[T]
- alembic.ini + async migrations (env.py, script.py.mako)

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/12



## 2026-06-17 — Issue 4: URL Connector completed

**Action:** feat/url-connector branch + PR #13

**Files:**
- connectors/base.py — BaseConnector + SyncResult
- connectors/url.py — URLConnector (httpx + bs4 + dedup)
- connectors/sync_service.py — SyncService orchestrator
- cli/main.py — CLI: add-source, sync, query (stub)

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/13



## 2026-06-17 — Issue 6: Entity & Relation Extraction completed

**Action:** feat/entity-relation-extraction branch + PR #15

**Files:**
- extractors/graph.py — GraphExtractor (entity regex extraction, relation signals, dedup)
- Updated sync_service.py to call GraphExtractor after knowledge extraction

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/15



## 2026-06-17 — Issue 7: Hybrid Retrieval + Answer completed (MVP done!)

**Action:** feat/hybrid-retrieval branch + PR #16 — последний MVP issue

**Files:**
- retrieval/vector.py — VectorRetriever (pgvector cosine similarity + text fallback)
- retrieval/graph_expander.py — GraphExpander (entity extraction + BFS graph traversal)
- retrieval/context_builder.py — ContextBuilder (prompt assembly + source formatting)
- retrieval/service.py — RetrievalService (orchestrator)

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/16



## 2026-06-17 — Issue 8: Telegram Connector completed

**Action:** feat/telegram-connector branch + PR #17 — Telethon-based connector

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/17



## 2026-06-17 — Issue 9: CLI completed — All 9 issues done!

**Action:** feat/cli-adv branch + PR #18 — полный CLI с rich output

**Commands:**
- `ke add-source` — добавить источник
- `ke sync` — синхронизировать
- `ke query` — запрос
- `ke advise` — интерактивный диалог
- `ke graph explore --entity <name>` — исследование графа
- `ke list-sources` — список источников
- `ke status` — статистика

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/18



## 2026-06-17 — Начало Фазы A: Environment + Testing

**Action:** Создаю chore/dev-environment branch с docker-compose.yml, .env.example и тестами



## 2026-06-17 — Phase A-1+2: docker-compose + .env.example

**Action:** chore/dev-environment branch + PR #19

**PR:** https://github.com/honeywagonoperator/knowledge_agent/pull/19

---

## 2026-06-17 — Phase A-3+4: All 21 tests pass!

**Action:** Исправил баги и добился 21/21 зелёных тестов

**Fixes:**
1. `entity.py:18` — добавлен `timezone` в импорт (`from datetime import datetime, timezone`)
2. `session.py` — `expire_on_commit=False` оставлен (нужен для asyncpg), но `Repository.get()` использует `populate_existing=True` для корректного чтения после cascade delete
3. `pyproject.toml` — исправлен TOML синтаксис (новые строки внутри строк, build-backend)
4. `docker-compose.yml` — pgvector/pg:16 вместо pg:17 (образ в 4× меньше)
5. `connectors/base.py` — восстановлен BaseConnector, потерянный при merge `-X ours`
6. `connectors/url.py`, `retrieval/context_builder.py` — исправлены `\n` escape-последовательности
7. `retrieval/vector.py` — исправлено `text` переопределение (конфликт с SQLAlchemy `text()`)

**Test results (all 21 pass):**
- `tests/test_models.py` — 13 passed (create all models, enum values, constraints)
- `tests/test_repository.py` — 8 passed (CRUD + cascade + duplicate PK + pagination + count)

**Files changed:**
- `src/knowledge_engine/models/entity.py` — import timezone
- `src/knowledge_engine/db/repository.py` — `populate_existing=True` in get()
- `pyproject.toml` — TOML syntax, build-backend, pytest-asyncio mode
- `docker-compose.yml` — pg16, removed Ollama

---

## Все 9 issues реализованы!

| # | Issue | PR | Статус |
|---|-------|----|--------|
| 1 | Scaffold | [#10](https://github.com/honeywagonoperator/knowledge_agent/pull/10) | ✅ |
| 2 | Data Models | [#11](https://github.com/honeywagonoperator/knowledge_agent/pull/11) | ✅ |
| 3 | DB Layer | [#12](https://github.com/honeywagonoperator/knowledge_agent/pull/12) | ✅ |
| 4 | URL Connector | [#13](https://github.com/honeywagonoperator/knowledge_agent/pull/13) | ✅ |
| 5 | Knowledge Extraction | [#14](https://github.com/honeywagonoperator/knowledge_agent/pull/14) | ✅ |
| 6 | Entity & Relation | [#15](https://github.com/honeywagonoperator/knowledge_agent/pull/15) | ✅ |
| 7 | Hybrid Retrieval | [#16](https://github.com/honeywagonoperator/knowledge_agent/pull/16) | ✅ |
| 8 | Telegram Connector | [#17](https://github.com/honeywagonoperator/knowledge_agent/pull/17) | ✅ |
| 9 | CLI | [#18](https://github.com/honeywagonoperator/knowledge_agent/pull/18) | ✅ |

## 2026-06-17 — Phase A: Тестирование + Merge

**Action:** Начинаю выполнение плана тестирования. Clone repo → Docker → тесты модуль за модулем → sequential merge.

**Plan:**
1. Clone + env
2. Ph A-3: tests/models → merge #10 → #11
3. Ph A-4: tests/db → merge #12
4. Ph A-5: tests/connectors → merge #13
5. Ph A-6: tests/extractors → merge #14 → #15
6. Ph A-7: tests/retrieval → merge #16
7. Tests Telegram + CLI → merge #17 → #18 → #19
8. Ph B: Sequential merge всех PRs
9. Ph C: GitHub Actions CI

---

## MVP Complete — 7/9 issues реализованы

### Draft PRs:
| # | Issue | PR |
|---|-------|----|
| 1 | Scaffold | [#10](https://github.com/honeywagonoperator/knowledge_agent/pull/10) |
| 2 | Data Models | [#11](https://github.com/honeywagonoperator/knowledge_agent/pull/11) |
| 3 | DB Layer | [#12](https://github.com/honeywagonoperator/knowledge_agent/pull/12) |
| 4 | URL Connector | [#13](https://github.com/honeywagonoperator/knowledge_agent/pull/13) |
| 5 | Knowledge Extraction | [#14](https://github.com/honeywagonoperator/knowledge_agent/pull/14) |
| 6 | Entity & Relation | [#15](https://github.com/honeywagonoperator/knowledge_agent/pull/15) |
| 7 | Hybrid Retrieval | [#16](https://github.com/honeywagonoperator/knowledge_agent/pull/16) |

---

## 2026-06-17 — Архитектурный рефакторинг: LlamaIndex PropertyGraphIndex

**Action:** Полная замена кастомных экстракторов/ретриверов на LlamaIndex PropertyGraphIndex.

**Rationale:** LlamaIndex даёт из коробки chunking (SentenceSplitter), entity/relation extraction (SchemaLLMPathExtractor через LLM), vector search (SimpleVectorStore) и graph traversal — убирает 8 модулей кастомного кода.

**Trade-offs:** Граф на диске (SimplePropertyGraphStore), не в PostgreSQL. PostgreSQL остаётся только для Sources + Documents (CLI). Вектора больше не в pgvector.

### Удалено (8 файлов)
- `models/knowledge_unit.py`, `models/entity.py`, `models/relation.py`
- `extractors/knowledge.py`, `extractors/graph.py`, `extractors/__init__.py`
- `retrieval/vector.py`, `retrieval/graph_expander.py`, `retrieval/context_builder.py`, `retrieval/service.py`

### Создано
- `src/knowledge_engine/index.py` — `KnowledgeIndex` (обёртка PropertyGraphIndex): init, insert_document, query, persist, stats

### Изменено
- `connectors/sync_service.py` — реализован `sync_source(connector)`: вызывает connector.sync(), затем index.insert_document() для каждого документа
- `cli/main.py` — `ke query` → `index.query()` через OpenRouter; `ke sync` → настоящая синхронизация; `ke advise` → через index; `ke status` → без удалённых моделей; `ke graph_explore` → через property_graph_store
- `tests/test_models.py` — сокращён до Source + Document (5 тестов)
- `tests/test_repository.py` — Entity → Source (8 тестов)
- `tests/conftest.py` — DROP TABLE для старых orphan-таблиц
- `docker-compose.yml` — `pgvector/pg:16` → `postgres:16-alpine`
- `models/__init__.py` — только Source, Document
- `knowledge_engine_architecture.md` — полное обновление

### Новая архитектура

```
ke sync → Connector → Document(PG) → index.insert(Document)
                                        ├── SentenceSplitter
                                        ├── OpenAIEmbedding (text-embedding-3-small)
                                        ├── SchemaLLMPathExtractor
                                        └── persist ./data/index/

ke query → index.query("...")
            ├── PropertyGraphIndex.as_retriever()
            │     ├── VectorContextRetriever
            │     └── LLMSynonymRetriever
            └── OpenRouter GPT-4o-mini → ответ
```

### Тесты
- `tests/test_models.py` — 5 passed
- `tests/test_repository.py` — 8 passed
- **Total: 13/13 passed**

---

## 2026-06-17 — Phase A-5/6/7 complete: All 51 tests green

**Action:** Написаны тесты для connectors (14), KnowledgeIndex (11), CLI (13)

**Results:** 51/51 passed (13 models + repo + 14 connectors + 11 index + 13 CLI)

**Files added:**
- `tests/test_connectors.py` — 14 тестов (Base, URL, Telegram, SyncService)
- `tests/test_index.py` — 11 тестов (init/load, insert, query, persist, stats)
- `tests/test_cli.py` — 13 тестов (add-source, sync, query, list-sources, status, graph-explore, advise)

**Phase A Summary:**
| Phase | Scope | Tests | Status |
|-------|-------|-------|--------|
| A-3 | Models | 5 | ✅ |
| A-4 | Repository | 8 | ✅ |
| A-5 | Connectors | 14 | ✅ |
| A-6 | KnowledgeIndex | 11 | ✅ |
| A-7 | CLI | 13 | ✅ |
| **Total** | | **51** | **✅** |

---
