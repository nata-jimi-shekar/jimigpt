# Git Worktrees for Code Review — Setup Guide

> **What is a worktree?** A separate working directory that shares the same
> Git history as your main repo. You can have one worktree on `main` (your
> normal dev environment) and another on a `review` branch — completely
> independent folders, same underlying repo. Changes in one don't affect
> the other.

> **Why use it for Codex review?** You keep coding in your main worktree
> while Codex reviews a frozen snapshot. No risk of your ongoing work
> contaminating the review, and no risk of review experiments touching main.

---

## One-Time Setup (Do This Once)

### Step 1: Choose where review worktrees will live

Your main repo is at:
```
C:\shekar73\Documents\Projects\jimigpt
```

Create a sibling folder for review worktrees:
```powershell
mkdir C:\shekar73\Documents\Projects\jimigpt-reviews
```

This keeps things clean — your main repo and review copies are side by side,
not nested inside each other.

### Step 2: Verify your repo is clean

Before creating a worktree, make sure main has no uncommitted changes:
```powershell
cd C:\shekar73\Documents\Projects\jimigpt
git status
```

If you see uncommitted changes, either commit them or stash them:
```powershell
git stash
```

---

## Per-Feature Review Workflow (Do This After Each Feature)

### Step 1: Make sure you're on main with everything merged

```powershell
cd C:\shekar73\Documents\Projects\jimigpt
git checkout main
git log --oneline -5
```

Confirm you see all the commits for the feature you just finished (e.g.,
all F01 commits should be there).

### Step 2: Create a review branch

This branch is a snapshot of main at this moment. It won't change while
you keep working.

```powershell
git branch review/F01
```

Replace `F01` with whichever feature you're reviewing. For future features:
`review/F02`, `review/F03`, etc.

### Step 3: Create the worktree

This creates a separate folder checked out to the review branch:

```powershell
git worktree add C:\shekar73\Documents\Projects\jimigpt-reviews\F01 review/F01
```

What this does:
- Creates the folder `jimigpt-reviews\F01\`
- Checks out the `review/F01` branch in that folder
- The folder has ALL your source code, tests, configs — a complete copy
- It shares Git history with your main repo (no duplicate `.git` data)

### Step 4: Verify it worked

```powershell
cd C:\shekar73\Documents\Projects\jimigpt-reviews\F01
git branch
dir src\personality
```

You should see:
- `* review/F01` as the current branch
- All your F01 source files present

### Step 5: Go back to your main repo and keep working

```powershell
cd C:\shekar73\Documents\Projects\jimigpt
git checkout main
```

You can now start F02 in your main repo. The review worktree at
`jimigpt-reviews\F01\` is frozen on the F01 snapshot.

---

## Feeding Code to Codex

Now you have a clean snapshot. Here's how to get the code into Codex:

### Option A: Copy-paste files directly (simplest)

Open the files from the review worktree folder and paste into Codex:

```powershell
cd C:\shekar73\Documents\Projects\jimigpt-reviews\F01
```

For F01, paste these files in this order (most important first):
1. The review brief: `docs\review\triage\F01-codex-brief-READY.md`
2. `src\personality\models.py`
3. `src\personality\archetypes.py`
4. `src\personality\prompt_builder.py`
5. `src\personality\pet_profile.py`
6. `src\messaging\models.py`
7. `config\archetypes\jimigpt\chaos_gremlin.yaml` (one archetype as example)
8. `tests\personality\test_integration.py` (the most comprehensive test)

If Codex has room in its context, also add:
9. `tests\personality\test_archetypes.py`
10. `tests\personality\test_prompt_builder.py`

### Option B: Use a script to concatenate files (for bigger features)

Create this script once and reuse it:

```powershell
# Run from the review worktree root
# Adjust the file list per feature

$files = @(
    "src\personality\models.py",
    "src\personality\enums.py",
    "src\personality\pet_profile.py",
    "src\personality\archetypes.py",
    "src\personality\prompt_builder.py",
    "src\messaging\models.py",
    "tests\personality\test_models.py",
    "tests\personality\test_archetypes.py",
    "tests\personality\test_prompt_builder.py",
    "tests\personality\test_integration.py",
    "tests\personality\test_tone_intent.py",
    "config\archetypes\jimigpt\chaos_gremlin.yaml"
)

$output = ""
foreach ($file in $files) {
    $output += "`n`n" + "=" * 60 + "`n"
    $output += "FILE: $file`n"
    $output += "=" * 60 + "`n"
    $output += Get-Content $file -Raw
}

$output | Set-Content "codex-review-package.txt" -Encoding UTF8
Write-Host "Created codex-review-package.txt"
```

Then paste `codex-review-package.txt` contents into Codex along with the
review brief.

---

## After the Review: Cleanup

Once you've triaged the Codex feedback and implemented any "Fix Now" items
in your main repo, clean up the worktree:

### Step 1: Remove the worktree

```powershell
cd C:\shekar73\Documents\Projects\jimigpt
git worktree remove C:\shekar73\Documents\Projects\jimigpt-reviews\F01
```

If Git complains about it being dirty (you accidentally edited something
in the review folder):
```powershell
git worktree remove --force C:\shekar73\Documents\Projects\jimigpt-reviews\F01
```

### Step 2: Delete the review branch

```powershell
git branch -d review/F01
```

If Git says it's not fully merged (it doesn't need to be — it was
just a snapshot):
```powershell
git branch -D review/F01
```

### Step 3: Verify cleanup

```powershell
git worktree list
```

Should show only your main worktree:
```
C:/shekar73/Documents/Projects/jimigpt  abc1234 [main]
```

---

## Quick Reference (Cheat Sheet)

```powershell
# === CREATE (after finishing a feature) ===
cd C:\shekar73\Documents\Projects\jimigpt
git checkout main
git branch review/F##
git worktree add C:\shekar73\Documents\Projects\jimigpt-reviews\F## review/F##

# === USE (feed to Codex) ===
cd C:\shekar73\Documents\Projects\jimigpt-reviews\F##
# Open files and paste into Codex

# === CLEANUP (after triage is done) ===
cd C:\shekar73\Documents\Projects\jimigpt
git worktree remove C:\shekar73\Documents\Projects\jimigpt-reviews\F##
git branch -D review/F##
```

---

## Troubleshooting

**"fatal: 'review/F01' is already checked out"**
You're trying to create a worktree for a branch that's already checked
out somewhere. Make sure your main repo is on `main`, not on `review/F01`.

**"fatal: working tree already exists"**
The worktree folder already exists. Either remove it first or use a
different folder name.

**"error: failed to prune worktrees"**
Run `git worktree prune` to clean up stale worktree references, then retry.

**Worktree folder is missing files**
The worktree doesn't install dependencies. It has the source code but not
`node_modules`, `.venv`, `__pycache__`, etc. This is fine for review — Codex
only needs the source files, not a running environment.

**I accidentally edited files in the review worktree**
No problem. Those edits only exist in the review branch. When you delete
the worktree and branch during cleanup, they disappear. Your main repo
is untouched.
