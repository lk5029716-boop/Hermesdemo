---
name: address-pr-comments
description: "Read GitHub PR review comments and systematically address each one in the code."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands address_pr_comments)
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [github, pr, code-review, review-comments, fix, automation]
    related_skills: [github-code-review, github-pr-workflow, requesting-code-review]
---

# Address PR Comments

Read all review comments on a GitHub PR, then systematically address each one. Every comment gets a response — either fixed with code changes or explained why not.

## The Iron Law

```
EVERY REVIEW COMMENT GETS A RESPONSE. NO COMMENT IS IGNORED.
```

## Prerequisites

- `gh` CLI installed and authenticated
- A GitHub token with PR read/write access
- Valid PR URL and branch name

## Workflow

### Step 1: Understand the Branch

```bash
# Checkout the branch
git checkout <BRANCH_NAME>

# See the diff to understand context
git diff main...<BRANCH_NAME>
```

### Step 2: Read All PR Review Comments

```bash
# Get ALL review comments (inline + general)
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments --paginate

# Get the review threads (grouped conversations)
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/reviews --paginate

# Or use gh pr view for the overview
gh pr view <PR_URL> --json reviews,comments,reviewThreads
```

### Step 3: Parse and List Comments

For each comment, note:
1. **Who** left it (reviewer login)
2. **Where** (file path + line number)
3. **What** (the comment text)
4. **Severity** (blocking suggestion vs nit vs question)

### Step 4: Address Each Comment Systematically

Work through comments in order. For each one:

**If it's a fix/change request:**
```bash
# Read the file at that location
# Make the change
# Stage the change
git add <file>
```

**If it's a question or discussion:**
- Reply to the comment on GitHub explaining your reasoning

**If you disagree:**
- Reply explaining why, with technical reasoning — don't just ignore it

### Step 5: Reply to Each Comment on GitHub

After addressing a comment, reply:

```bash
# Reply to an inline comment (review thread)
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments/<COMMENT_ID>/replies \
  -X POST -f body="Fixed in [commit-hash]. [Brief explanation]"

# Or resolve the review thread via the review API
```

### Step 6: Commit Changes

```bash
git add .
git commit -m "Address PR review comments: [brief summary of changes]"
git push origin <BRANCH_NAME>
```

### Step 7: Notify Reviewer

Tell the PR reviewer:
- Which comments were addressed
- What changes were made
- Which comments need discussion (if any)

## Handling Different Comment Types

### "This should be X instead of Y"
→ Make the fix. Reply: "Fixed. Changed to X as suggested."

### "What about edge case Z?"
→ Handle the edge case if valid. Reply: "Good catch. Added handling for Z."

### "This is wrong because..."
→ If they're right, fix it. If you disagree, explain with code evidence.

### "Nit: rename variable"
→ Just fix it. Reply: "Done." (no debate on style nits)

### "Why did you choose X?"
→ Reply with your reasoning. Don't change code unless convinced.

### "Consider using Y pattern"
→ Evaluate. If Y is better, switch. If X is intentionally chosen, explain why.

## Tips

- **Don't batch all fixes into one small commit** — group related fixes logically
- **Reference specific comments in commit messages**: "Fix: handle null input (addresses review comment on line 42)"
- **[Don't mark as resolved without fixing](http://don't)** — only resolve when code actually changes
- **[Don't argue in commits](http://don't)** — use GitHub replies for discussion
- **Be respectful** — reviewers are helping improve the code
- **Ask if unclear** — better to ask than to guess and get it wrong
