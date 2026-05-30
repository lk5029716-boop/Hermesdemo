---
name: repositories
description: "Multi-repo project management — git submodules, subtrees, monorepo patterns, workspace configuration."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands repositories)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [multi-repo, submodules, subtrees, monorepo, workspace, git]
    related_skills: [github-repo-management, agent-memory, writing-plans]
---

# Multi-Repository Management

Most real-world projects span multiple repositories. This skill covers patterns for managing them effectively.

## The Pattern Decision Tree

```
Do components share a release cycle?
├── YES → Monorepo (single repo, multiple packages)
└── NO  → Multi-repo
         ├── Tight coupling? → Git Submodules
         ├── Loose coupling? → Git Subtrees
         └── Independent?    → Separate repos + workspace tooling
```

## Pattern 1: Separate Repos + Workspace

Best when: Repos are loosely coupled, different teams, different release cycles.

```bash
# Create a workspace directory
mkdir my-workspace && cd my-workspace

# Clone all repos
git clone git@github.com:org/backend.git
git clone git@github.com:org/frontend.git
git clone git@github.com:org/shared-lib.git
git clone git@github.com:org/docs.git

# Structure:
my-workspace/
├── backend/
├── frontend/
├── shared-lib/
└── docs/
```

### Workspace README
Create a `README.md` in the workspace root:

```markdown
# My Project Workspace

## Repos
- `backend/` — Python API server
- `frontend/` — React UI
- `shared-lib/` — Shared utilities (used by both)
- `docs/` — Documentation

## Setup
\`\`\`bash
cd shared-lib && pip install -e .
cd ../backend && pip install -r requirements.txt
cd ../frontend && npm install
\`\`\`

## Testing
\`\`\`bash
cd backend && pytest
cd frontend && npm test
\`\`\`
```

### Helper scripts
```bash
# scripts/test-all.sh
for dir in backend frontend shared-lib; do
    echo "=== Testing $dir ==="
    (cd $dir && npm test 2>/dev/null || pytest 2>/dev/null)
done
```

## Pattern 2: Git Submodules

Best when: You need exact version pinning of dependencies, or a repo embedded in another.

```bash
# Add a submodule
git submodule add git@github.com:org/shared-lib.git libs/shared-lib

# Clone with submodules
git clone --recurse-submodules git@github.com:org/main-project.git

# Update submodules
git submodule update --remote --merge

# Update a specific submodule
cd libs/shared-lib
git pull origin main
cd ..
git add libs/shared-lib
git commit -m "Update shared-lib to latest"
```

### Submodule management commands
```bash
# List submodules
git submodule status

# Init submodules (first time)
git submodule init
git submodule update

# Run command in all submodules
git submodule foreach 'git pull origin main'
git submodule foreach 'pytest'

# Remove a submodule
git submodule deinit libs/shared-lib
git rm libs/shared-lib
rm -rf .git/modules/libs/shared-lib
```

### .gitmodules file
```ini
[submodule "libs/shared-lib"]
    path = libs/shared-lib
    url = git@github.com:org/shared-lib.git
    branch = main
```

### Gotchas
- Submodules point to a **specific commit**, not a branch head
- Team members must remember to `git submodule update` after pull
- CI must use `git submodule update --init --recursive`
- Nested submodules are painful — avoid

## Pattern 3: Git Subtrees

Best when: You want to merge external repo content into your repo without the complexity of submodules.

```bash
# Add a subtree
git remote add shared-lib git@github.com:org/shared-lib.git
git subtree add --prefix=libs/shared-lib shared-lib main --squash

# Pull updates
git subtree pull --prefix=libs/shared-lib shared-lib main --squash

# Push changes back (if you have write access)
git subtree push --prefix=libs/shared-lib shared-lib main
```

### Subtree vs Submodule
| | Submodule | Subtree |
|---|---|---|
| Complexity | High | Low |
| History | Separate | Merged into main repo |
| Clone | Needs `--recurse-submodules` | Works normally |
| Size | Small (just a reference) | Large (full content) |
| Push back | Easy | Possible but awkward |
| CI complexity | Must init submodules | None |

## Pattern 4: Monorepo

Best when: All components share a release cycle and are tightly coupled.

```
monorepo/
├── packages/
│   ├── api/          # Backend
│   ├── web/          # Frontend
│   ├── shared/       # Shared code
│   └── cli/          # CLI tool
├── scripts/
│   ├── build.sh
│   └── test.sh
├── package.json      # Root workspace config (Node)
├── pyproject.toml    # Root config (Python)
└── Makefile
```

### Python monorepo with workspace
```toml
# pyproject.toml (root)
[tool.uv.workspace]
members = ["packages/*"]
```

### Node monorepo with workspaces
```json
// package.json (root)
{
  "workspaces": ["packages/*"],
  "scripts": {
    "test": "npm workspaces run test",
    "build": "npm workspaces run build"
  }
}
```

### Make-based monorepo (language-agnostic)
```makefile
# Makefile
.PHONY: test build clean

test:
	@for dir in packages/*; do \
		echo "Testing $$dir..."; \
		$(MAKE) -C $$dir test; \
	done

build:
	@for dir in packages/*; do \
		$(MAKE) -C $$dir build; \
	done

clean:
	@for dir in packages/*; do \
		$(MAKE) -C $$dir clean; \
	done
```

## Pattern 5: Meta-Repo with Repo Tool

Google's `repo` tool for managing many Git repos (originally for Android):

```bash
# Install repo
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo

# Initialize workspace
repo init -u git@github.com:org/manifests.git
repo sync

# manifest.xml defines which repos go where
```

## Recommendations

| Situation | Recommended Pattern |
|---|---|
| 2-3 repos, same team | Separate repos + workspace directory |
| Dependency with version pinning | Git Subtrees (simpler than submodules) |
| Many repos, different teams | Meta-repo with repo tool OR subtrees |
| Tightly coupled, shared release | Monorepo |
| Fork with upstream tracking | Git Subtrees |

## Tips

- **Avoid submodules** if possible — they cause more pain than they solve
- **Prefer subtrees** for embedding dependencies
- **Monorepos are great** until they're not — size and tooling matter
- **Document the workspace** — a workspace README is essential
- **Automate with scripts** — don't make humans run 10 commands to set up
