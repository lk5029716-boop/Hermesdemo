---
name: update-pr-description
description: "Auto-update a GitHub PR description by reading the branch diff and updating via the GitHub API."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands update_pr_description)
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [github, pr, pull-request, api, automation, documentation]
    related_skills: [github-pr-workflow, github-code-review, github-repo-management]
---

# Update PR Description

Read a branch's diff against main, understand the changes, then auto-update the GitHub PR description to accurately reflect what was changed.

## When to Use

- After making significant changes to a PR branch
- When the PR description no longer matches the actual diff
- When asked to "update this PR description"

## Prerequisites

- `gh` CLI installed and authenticated
- A GitHub token with PR write access (via `gh auth` or `GITHUB_TOKEN` env var)
- Valid PR URL and branch name

## Workflow

### Step 1: Understand the Branch

```bash
# Checkout the branch
git checkout <BRANCH_NAME>

# See the diff against main
git diff main...<BRANCH_NAME>

# See commit history for context
git log main..<BRANCH_NAME> --oneline
```

### Step 2: Read the Existing PR Description

```bash
# Get current PR info
gh pr view <PR_URL> --json title,body,number,state
```

### Step 3: Analyze Changes

Summarize the diff:
- What files changed?
- What was added/removed/modified?
- What's the overall purpose of the changes?
- Any breaking changes?
- Any new dependencies or config changes?

### Step 4: Update the PR Description

```bash
# Update the PR body
gh pr edit <PR_NUMBER> --body "$(cat <<'EOF'
## Summary
[One paragraph describing what this PR does and why]

## Changes
- [Change 1: what and where]
- [Change 2]
- [Change 3]

## Testing
- [How to test these changes]

## Checklist
- [ ] Tests pass
- [ ] Linter passes
- [ ] Documentation updated (if needed)
EOF
)"
```

### Step 5: Confirm with User

After updating, tell the user:
- What the old description said
- What the new description says
- Link to the PR

## Template

Use this template for well-structured PR descriptions:

```markdown
## Summary
[1-2 sentences: what this PR accomplishes]

## Motivation
[Why these changes were needed]

## Changes
### Added
- [New feature/file — what it does]

### Changed
- [Modified behavior — what and how]

### Fixed
- [Bug fix — what was wrong, what it does now]

### Removed
- [Deleted code/feature — why]

## Testing
\`\`\`bash
[Command to run tests]
\`\`\`

## Screenshots (if UI changes)
[Before/after images]

## Checklist
- [ ] Tests pass (`pytest tests/`)
- [ ] Linter passes (`ruff check .`)
- [ ] Type checker passes (`mypy src/`)
- [ ] No new security issues
- [ ] Backward compatible (or documented breaking change)
```

## Tips

- **Be specific**: "Added retry logic to payment webhook handler" not "Fixed stuff"
- **Reference issues**: "Closes #123" or "Related to #456"
- **Highlight breaking changes**: Put them at the top in a `## ⚠️ Breaking Changes` section
- **Keep it scannable**: Use bullet lists, not walls of text
- **Mention side effects**: "Also refactored X to support Y"
