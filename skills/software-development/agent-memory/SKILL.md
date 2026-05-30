---
name: agent-memory
description: "Per-project persistent memory — save, load, and query facts about a project across sessions."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands agent_memory)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [memory, persistence, project-knowledge, remember, cross-session]
    related_skills: [hermes-agent-skill-authoring, studying-codebases]
---

# Agent Memory

Give Hermes persistent memory per project — facts, conventions, decisions, and project knowledge that survive across sessions.

## The Iron Law

```
NEVER LOOSE PROJECT KNOWLEDGE ACROSS SESSIONS
```

If the user tells you "remember this" → save it to memory immediately. If you learn a project convention → save it. If you discover the project structure → save it.

## How Memory Works

### Storage Location

Project-specific memory lives in the project's `.hermes/` directory:

```
<project>/
└── .hermes/
    ├── memory.md          # Project knowledge, conventions, decisions
    └── microagents/       # Per-repo skills (optional)
        └── repo.md        # Repository-specific instructions
```

### What to Save

| Category | Examples |
|---|---|
| **Project conventions** | Coding style, testing framework, commit format |
| **Architecture decisions** | Why X was chosen over Y |
| **Gotchas** | Weird bugs, non-obvious setup, env quirks |
| **Dependencies** | Required env vars, API keys, services |
| **Workflow** | How to build, test, deploy |
| **Contacts** | Who owns what, where to ask |

### What NOT to Save

- API keys or secrets (use env vars)
- Temporary task state
- Anything that changes frequently
- Raw code dumps

## Commands

### Save Memory

When user says "remember this" or "save this":

```bash
# Create .hermes/ if it doesn't exist
mkdir -p /path/to/project/.hermes

# Append to memory.md
cat >> /path/to/project/.hermes/memory.md << 'EOF'
## [Category]
[Fact or convention — one clear statement]
EOF
```

### Load Memory

Before working on any project, check for existing memory:

```bash
cat /path/to/project/.hermes/memory.md 2>/dev/null || echo "No memory yet"
```

### Query Memory

Search across memory files:

```bash
rg "<query>" /path/to/project/.hermes/memory.md
```

## Memory File Format

```markdown
# Project Memory: <project-name>

## Conventions
- Tests use pytest with `-n 4` (xdist)
- Commit messages follow conventional commits
- All PRs must pass pre-commit before review

## Architecture
- Backend: FastAPI in `src/api/`
- Database: PostgreSQL via SQLAlchemy
- Auth: JWT tokens in HTTP-only cookies

## Gotchas
- The test DB needs `TEST_DB_URL` env var
- Docker build requires `--target=dev` for hot reload
- Migration scripts must run before tests: `alembic upgrade head`

## Dependencies
- Requires Redis running on port 6379
- Needs `STRIPE_API_KEY` for payment tests
- Uses `@stripe/stripe-js` v2.x (v3 breaks)

## Deployment
- Staging: `deploy-staging.sh` from `main` branch
- Production: GitHub Actions on `release/*` tags
- Rollback: `rollback.sh <version>`
```

## Create Repository Instructions (repo.md)

For complex projects, create a dedicated repo instructions file:

```bash
mkdir -p /path/to/project/.hermes/microagents
```

```markdown
---
name: repo
type: repo
---

# Repository: <name>

## Purpose
[One paragraph: what this project does and why it exists]

## Setup
\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your values

# Run tests
pytest tests/ -n 4
\`\`\`

## Structure
- `src/` — application source code
- `tests/` — pytest tests
- `scripts/` — utility scripts

## Testing
- Run all: `pytest tests/ -n 4`
- Run specific: `pytest tests/unit/test_xxx.py`
- Coverage: `pytest --cov=src tests/`

## CI Checks
- Linter: `ruff check .`
- Type check: `mypy src/`
- Tests: `pytest tests/ -n 4`
```

## Workflow Integration

### On First Visit to a Project
1. Check for `.hermes/memory.md` — load it if exists
2. Check for `.hermes/microagents/repo.md` — load it if exists
3. If neither exists, offer to create memory as you learn the project

### During Work
1. When you learn a convention → save to memory
2. When user corrects you → save to memory
3. When you discover a gotcha → save to memory
4. When architecture decision is made → save to memory

### On Session End
1. Review what you learned this session
2. Save any unsaved facts to `.hermes/memory.md`

## Tips

- **Be specific**: "Use `pytest -n 4`" not "run tests somehow"
- **Be current**: Update memory when things change
- **Be concise**: One fact per bullet, no essays
- **Use categories**: Group related facts under `##` headers
- **Version note**: If something changed, note when: "Since v2.0, auth uses OAuth2"
