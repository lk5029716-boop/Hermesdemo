---
name: onboarding
description: "First-time project onboarding — progressive interview to understand a project, then create a PR-ready plan."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands onboarding)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [onboarding, interview, planning, first-time, project-setup]
    related_skills: [writing-plans, plan, agent-memory, studying-codebases]
---

# Project Onboarding

When starting work on a new project, do NOT just start coding. Run a progressive interview to understand the project first, then produce a PR-ready plan.

## The Iron Law

```
UNDERSTAND BEFORE YOU BUILD
```

Never touch code until you understand: what it does, how it's structured, how to test it, and what the user actually wants.

## The Onboarding Interview

Ask questions progressively — start broad, get specific. Don't ask everything at once.

### Round 1: Project Overview (2-3 questions)
1. "What does this project do? What problem does it solve?"
2. "Who uses it — internal team, external customers, or yourself?"
3. "Is this a rewrite/new feature/bug fix/from scratch?"

### Round 2: Technical Context (3-4 questions)
1. "What's the tech stack? (languages, frameworks, databases)"
2. "How do I build and run this project?"
3. "How do I test it?"
4. "Is there documentation I should read first?"

### Round 3: Task Clarification (3-4 questions)
1. "What specifically do you want me to build/change/fix?"
2. "What does 'done' look like for this task?"
3. "Are there any constraints? (performance, compatibility, style)"
4. "Should this be one PR or multiple?"

### Round 4: Preferences (2-3 questions)
1. "Do you want me to ask before making each change, or just do it?"
2. "Any conventions I should follow? (commit messages, PR format)"
3. "Want tests for this? What framework?"

## After the Interview

### Write a Plan

Use the answers to write a concise plan:

```markdown
# Plan: <Task Name>

## Context
[What the project does, tech stack, what the user wants]

## Approach
1. [Step 1 — what to change and why]
2. [Step 2]
3. [Step 3]

## Scope
- In scope: [what you'll do]
- Out of scope: [what you won't do]

## Testing
- [How to verify it works]

## Risks
- [Potential issues and mitigations]
```

### Save Onboarding Results

Save what you learned to agent memory:

```bash
cat > .hermes/memory.md << 'EOF'
# Project Memory: <name>

## Purpose
[From Round 1]

## Tech Stack
[From Round 2]

## Setup
\`\`\`bash
[Build/test commands from Round 2]
\`\`\`

## Conventions
[From Round 4]
EOF
```

## Progressive Disclosure

Don't dump all questions at once. Use this flow:

```
Round 1 → wait for answers → Round 2 → wait for answers → etc.
```

If the user gives detailed answers, skip follow-up questions. If they say "just look at the repo," do your own reconnaissance:

```bash
# Auto-interview: read the project yourself
ls -la
cat README.md
cat package.json  # or pyproject.toml, Cargo.toml, etc.
cat .github/workflows/*.yml  # CI tells you build/test commands
find . -name "*.test.*" -o -name "test_*" | head -5  # test files
```

Then tell the user what you found and confirm:
> "I read your repo. It's a Python FastAPI app with pytest. I can see the CLI entry point. You want me to add X — correct?"

## Edge Cases

- **User says "just build it"** → Still read the plan, confirm scope, then build
- **User says "I already told you everything"** → Trust them, proceed to plan
- **User doesn't know the tech stack** → Investigate the repo yourself, report findings
- **Brand new project** → Focus on Round 1 questions, help them think through architecture
