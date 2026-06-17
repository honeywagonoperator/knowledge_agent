# Knowledge Engine — AGENTS.md

## Project Overview

**Knowledge Engine** — личный AI-агент, который собирает знания из Telegram-каналов и URL, превращает их в структурированные knowledge units, строит knowledge graph (entities + relations) и отвечает с обязательными ссылками на источники.

**Стэк:** Python, PostgreSQL (Sources/Documents), LlamaIndex PropertyGraphIndex (вектора + граф на диске)

Архитектура и стек технологий: `knowledge_engine_architecture.md`

---

## Session Logging

Все действия и решения агента записываются в `SESSION.md` в корне проекта.

**Запись добавляется перед каждым значимым действием:**
```
## <timestamp> — <что делаем>

**Action:** <что именно делаем>
**Rationale:** <почему делаем именно так>
**Trade-offs:** <какие альтернативы рассматривали, почему выбрали эту>
```

Прочитать последние записи: `read("SESSION.md")`

Перед каждым шагом воркфлоу — **сначала запиши действие в SESSION.md**, потом выполняй.

---

## Skills

| Skill | Назначение |
|---|---|
| `load skill vibe-coding` | Воркфлоу кодинга — когда использовать context7, sequential-thinking, serena |
| `load skill github` | GitHub workflow — ветки, PR, issues, code review |

## Known Issues & Workarounds

### GitHub MCP Server не работает
MCP сервер `@modelcontextprotocol/server-github` выдаёт auth error. Все GitHub операции выполняются через **REST API напрямую** (`github_create_branch`, `github_push_files`, `github_create_pull_request`, etc.) — они доступны как встроенные инструменты, `load skill github` не требуется.

### Windows socks4 proxy ломает pip
Системный прокси `socks4://127.0.0.1:10808` (читается через `urllib.request.getproxies()` из реестра Windows) блокирует установку пакетов. Workaround:
```
source .venv/Scripts/activate
pip install -e ".[dev]" --no-build-isolation
```
с установленной переменной `NO_PROXY=*` в окружении.

### pytest-asyncio
Версия **0.24.0** форсирована (не 0.25+ из pyproject.toml) — 0.25+ вызывает event loop mismatch с asyncpg. Команда для запуска тестов:
```
python -m pytest tests/ -v
```

---

## Workflow

### 1. Анализ запроса

→ записать в `SESSION.md`

**Новый запрос / идея / фича:**
- `github_create_issue` — создать issue с Acceptance Criteria, labels, assignee

**Запрос на выполнение существующей фичи:**
- `github_search_issues` / `github_get_issue` — прочитать issue
- Если issue не найдено — уточнить у пользователя, создать новое

### 2. Создание feature branch + Draft PR

`load skill github`:

```
github_create_branch({ branch: "feat/<name>", from_branch: "main" })
github_create_pull_request({ head: "feat/<name>", base: "main", draft: true })
```

**Жизненно важно:** каждая фича — отдельная ветка. Никаких коммитов в main.

> **Note:** GitHub MCP server не работает — используй встроенные tools `github_create_branch`, `github_push_files`, `github_create_pull_request` напрямую, `load skill github` не требуется.

### 3. Планирование

→ записать в `SESSION.md`
`load skill vibe-coding` → **sequential-thinking**:

- Разобрать задачу на шаги
- Оценить сложность, риски, зависимости
- Если не хватает контекста — **задать уточняющие вопросы пользователю**

> **Пользователь — менеджер проекта, не разработчик.** Агент обязан:
> - Предлагать лучшие engineering-решения, даже если они противоречат первоначальной идее
> - Объяснять trade-offs простым языком
> - Направлять, а не просто исполнять
> - Не соглашаться на технический компромисс без явного осознанного решения

### 4. Реализация (код)

→ записать в `SESSION.md`
`load skill vibe-coding`:

- **context7** — для документации библиотек (если нужен новый пакет или API)
- **serena** — для навигации по коду и редактирования
- Писать код в соответствии с архитектурой проекта (см. knowledge_engine_architecture.md)
- Коммиты через `load skill github` → `github_push_files` (формат сообщений — в github skill)

### 5. Тестирование

→ записать в `SESSION.md`

- Юнит-тесты для новой логики
- Интеграционное/функциональное тестирование (если нужно)
- Прогнать тесты, убедиться что всё зелёное
- Фреймворк: pytest + pytest-asyncio 0.24.0
- Команда: `python -m pytest tests/ -v` (см. Known Issues про pytest-asyncio)

### 6. Подтверждение

→ записать в `SESSION.md`

Показать пользователю **diff изменений** (summary ключевых файлов):

- Какие файлы добавлены/изменены
- Ключевые моменты реализации
- Trade-offs, если были

Получить approval перед merge. Если пользователь просит изменить — вернуться к шагу 4.

### 7. Merge

→ записать в `SESSION.md`
`load skill github`:

```
github_merge_pull_request({ merge_method: "squash" })
```

### 8. Rollback (если что-то пошло не так)

→ записать в `SESSION.md`
Если после мержа обнаружена проблема:

1. `github_create_branch({ branch: "fix/rollback-<description>", from_branch: "main" })`
2. Откатить изменения (revert коммит через `github_push_files`)
3. `github_create_pull_request({ ... })` → `github_merge_pull_request`
4. Создать новый issue на исправление проблемы

---

## Guiding Principles

1. **Quality over speed** — цель не «сделать быстро», а «сделать правильно»
2. **Challenge the user** — менеджер может ошибаться в технических решениях; аргументированно предлагай лучшее
3. **Skills first** — coding → `load skill vibe-coding`, git → `load skill github`
4. **Ask, don't assume** — если не хватает контекста или требования противоречивы — уточни
5. **Each feature = one branch** — никаких исключений
6. **Architecture-aware** — все изменения должны соответствовать data model и pipeline из knowledge_engine_architecture.md
