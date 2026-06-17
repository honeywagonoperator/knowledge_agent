---
name: github
description: GitHub workflow — branching strategy, PR lifecycle, issue management, and code review
---

## Core Principle

**Каждая фича — отдельная ветка.** Никогда не коммить напрямую в `main`/`master`. Feature branch создаётся от актуального `main`, после завершения — PR и squash-merge.

---

## Branching

**Соглашение об именах веток:**
- `feat/<короткое-описание>` — новая фича
- `fix/<короткое-описание>` — багфикс
- `refactor/<короткое-описание>` — рефакторинг
- `docs/<короткое-описание>` — документация
- `chore/<короткое-описание>` — обслуживание (deps, CI, конфиги)

**Примеры:**
```
git checkout -b feat/rate-limiter
git checkout -b fix/login-redirect
git checkout -b refactor/api-client
```

---

## Pull Request Lifecycle

### 1. Создание ветки
```
github_create_branch({
  owner: "<owner>",
  repo: "<repo>",
  branch: "feat/<name>",
  from_branch: "main"     // всегда от свежего main
})
```

### 2. Пуш изменений
После локальных изменений:
```
github_push_files({
  owner: "<owner>",
  repo: "<repo>",
  branch: "feat/<name>",
  files: [
    { path: "src/file.ts", content: "..." },
    { path: "src/file.test.ts", content: "..." }
  ],
  message: "feat: add rate limiter middleware"
})
```

### 3. Создание PR
```
github_create_pull_request({
  owner: "<owner>",
  repo: "<repo>",
  title: "feat: add rate limiter middleware",
  body: "## What\nAdds express-rate-limit to /api routes.\n\n## Why\nPrevents brute force attacks.\n\n## Testing\n- `npm test` passes\n- Manual test with 100 req/min",
  head: "feat/rate-limiter",
  base: "main",
  draft: false
})
```

### 4. Статус и ревью
```
github_get_pull_request_status({ owner, repo, pull_number })
github_get_pull_request_reviews({ owner, repo, pull_number })
```

### 5. Обновление ветки если main ушёл вперёд
```
github_update_pull_request_branch({ owner, repo, pull_number })
```

### 6. Merge
```
github_merge_pull_request({
  owner, repo, pull_number,
  merge_method: "squash"   // squash — чистая история
})
```

---

## Issue Management

**Создание:**
```
github_create_issue({
  owner: "<owner>",
  repo: "<repo>",
  title: "Add rate limiter to /api routes",
  body: "**Acceptance criteria:**\n- [ ] Limit 100 req/min per IP\n- [ ] Return 429 on exceed\n- [ ] Configurable via env",
  labels: ["enhancement"],
  assignees: ["username"]
})
```

**Поиск:**
```
github_search_issues({ q: "rate limit repo:owner/repo is:issue is:open" })
```

**Закрытие:**
```
github_update_issue({ owner, repo, issue_number, state: "closed" })
```

---

## Code Review

**Запросить изменения:**
```
github_create_pull_request_review({
  owner, repo, pull_number,
  event: "REQUEST_CHANGES",
  body: "Нужно добавить тесты на edge cases.",
  comments: [
    { path: "src/middleware.ts", line: 42, body: "Вынести magic number в константу" }
  ]
})
```

**Аппрув:**
```
github_create_pull_request_review({
  owner, repo, pull_number,
  event: "APPROVE",
  body: "LGTM, все тесты проходят."
})
```

---

## Полный воркфлоу на примере

**Задача:** "Добавить rate limiter на /api routes"

1. `sequential-thinking` — план: middleware → config → env vars → тесты
2. `github_create_branch({ branch: "feat/rate-limiter", from_branch: "main" })`
3. `github_push_files({ files: [middleware.ts, config.ts, middleware.test.ts], message: "feat: add rate limiter" })`
4. `github_create_pull_request({ head: "feat/rate-limiter", base: "main", draft: true })`
5. `github_update_issue({ issue_number: 12, state: "closed" })` — если есть issue

**После аппрува:**
6. `github_merge_pull_request({ merge_method: "squash" })`
7. Ветка `feat/rate-limiter` удаляется на гитхабе (можно вручную или через API)

---

## Important Reminders

- `github_get_pull_request_files` — посмотреть какие файлы изменены в PR перед ревью
- `github_list_commits` — проверить историю коммитов перед мержем
- `github_push_files` НЕ создаёт ветку — всегда сначала создать через `create_branch`
- GHToken должен иметь права на репо (repo, pull_request, issues)
