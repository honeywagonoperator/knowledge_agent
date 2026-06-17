---
name: vibe-coding
description: Vibe-coding workflow — when and how to use context7, sequential-thinking, and serena tools for optimal flow
---

## Overview

Vibe-coding is a workflow that keeps you in flow by picking the right tool at the right time. Three core tools form the stack:

- **context7** — documentation intelligence
- **sequential-thinking** — structured reasoning
- **serena** — codebase navigation and editing

---

## context7 — Documentation Intelligence

**When to use:**
- User asks how to use a specific library/framework API
- You need version-specific docs (e.g., "Next.js 15", "React 19")
- Writing code that depends on a third-party library and you're unsure of the exact API
- Before suggesting an approach that relies on an external library — validate the API first

**When NOT to use:**
- Standard language built-ins (Python `os`, `json`, etc.)
- The question is about the project's own code — use serena instead
- Simple, well-known patterns you're confident about

**Workflow:**
1. `context7_resolve-library-id({ query, libraryName })` — find the library
2. `context7_query-docs({ libraryId, query })` — get specific docs

**Examples:**
```
User: "How do I use Prisma with PostgreSQL?"
Agent:
1. context7_resolve-library-id({ query: "Prisma PostgreSQL connection", libraryName: "Prisma" })
2. context7_query-docs({ libraryId: "/prisma/prisma", query: "connect to PostgreSQL datasource" })

User: "Add authentication with NextAuth.js"
Agent:
1. context7_resolve-library-id({ query: "NextAuth.js v5 authentication setup", libraryName: "NextAuth.js" })
2. context7_query-docs({ libraryId: "/nextauthjs/next-auth", query: "v5 app router setup credentials provider" })
```

---

## sequential-thinking — Structured Reasoning

**When to use:**
- Complex architectural decisions with multiple tradeoffs
- Debugging a non-obvious bug where root cause is unclear
- Planning multi-step feature implementation with dependencies
- Ambiguous requirements that need refinement
- Before making irreversible design choices
- Breaking down a large task into ordered steps

**When NOT to use:**
- Simple lookups or straightforward tasks
- When the answer is obvious from context
- Pure code-gen tasks (implement a known pattern)

**Examples:**
```
Situation: "Add offline-first support to the notes app"
→ Use sequential-thinking to map out: sync strategy, conflict resolution, local DB schema, network detection, UI states

Situation: "The build is failing with a cryptic Webpack error"
→ Use sequential-thinking to: list possible causes, check each hypothesis, narrow down systematically

Situation: "We need to migrate from REST to GraphQL"
→ Use sequential-thinking to: inventory endpoints, design schema, plan migration phases, identify risks
```

---

## serena — Codebase Navigation & Editing

**When to use:**
- Understanding code structure (`get_symbols_overview`, `find_symbol`)
- Finding where something is defined or used (`find_referencing_symbols`, `find_implementations`)
- Searching for patterns in code (`search_for_pattern`)
- Making precise edits (`replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`)
- Renaming symbols across the codebase (`rename_symbol`)
- Reading diagnostics (`get_diagnostics_for_file`)
- Storing/retrieving project knowledge (`write_memory`, `read_memory`)

**When NOT to use:**
- You already have the full file content from a prior read
- The edit is simpler with direct file tools (single-line change in a large file)

**Best practices:**
- Start with `get_symbols_overview` + `depth=1` to understand a new file
- Use `find_symbol` with `include_body=true` only when you need the implementation
- Use `find_referencing_symbols` before renaming/deleting to avoid breakage
- Write memories for recurring patterns, architectural decisions, and conventions

**Examples:**
```
Task: "Add validation to the createUser function"
1. find_symbol({ name_path_pattern: "createUser", include_body: true })
2. replace_symbol_body({ name_path: "createUser", body: "def createUser(data):\n    validate(data)\n    ..." })

Task: "Rename getItems to fetchItems"
1. find_referencing_symbols({ name_path: "getItems" }) — check all usages
2. rename_symbol({ name_path: "getItems", new_name: "fetchItems" })
```

---

## Combined Workflow Example

Scenario: "Add a rate limiter using express-rate-limit"

1. **sequential-thinking** — plan approach (middleware placement, config, testing)
2. **context7** — `resolve-library-id("express-rate-limit")` → `query-docs("/express-rate-limit", "middleware setup")`
3. **serena** — `find_symbol("src/middleware/")` to find where to add it
4. **serena** — `insert_after_symbol` or edit to add the rate limiter
5. **serena** — `write_memory` to document the rate limiting approach for future reference
