# Contributing Guide

This project uses a simple, team-friendly Git workflow:

**branch -> commits -> push -> PR -> merge -> sync main -> delete branch**

The goal is to keep `main` as the **latest known-good shared baseline** and keep feature branches small and short-lived.

---

## The 3 Git things you are always dealing with

- **Commits**: saved snapshots of the repo at a point in time.
- **Branches**: named pointers to commits (for example, `main`, `feature/mcp-tooling`).
- **Remotes (GitHub)**: `origin` is the GitHub repo. GitHub stores copies like `origin/main` and `origin/feature/mcp-tooling`.

Local branches and GitHub branches line up when you **pull** (download) and **push** (upload).

---

## Daily workflow (standard loop)

### A) Start from a clean, up-to-date `main`

From the project root:

```powershell
git checkout main
git pull origin main
```

### B) Create a branch for your task

Use a short, descriptive name:

```powershell
git checkout -b feature/<short-description>
```

Examples:

- `feature/mcp-server-cleanup`
- `feature/pdf-parser-skeleton`
- `fix/docker-port-mapping`
- `chore/readme-update`

### C) Make only the relevant changes

Keep branches focused: one feature, one fix, or one cleanup per PR.

### D) Run project checks locally before committing

From the project root:

```powershell
python start_all.py
```

In a second terminal, after the backend is up:

```powershell
python tests\mcp_smoke_client.py
```

Make sure the following are true before you commit:

- your virtual environment is activated
- Docker Desktop is running
- the backend starts without errors
- the MCP smoke test succeeds
- you did not accidentally modify unrelated files

If you changed dependencies, also verify:

```powershell
python -m pip install -r requirements.txt
```

### E) Commit and push

```powershell
git status
git add -A
git commit -m "Short, specific message"
git push -u origin feature/<short-description>
```

After the first push, GitHub will usually show a banner to open a PR.

### F) Open a PR and merge into `main`

- Title your PR clearly.
- Describe what changed and why.
- Mention anything teammates need to test locally.
- Request review if your team is doing reviews.
- Merge when approved or when your team agrees it is ready.

### After merge (cleanup)

```powershell
git checkout main
git pull origin main
git branch -d feature/<short-description>
```

Optional, if GitHub does not auto-delete the remote branch:

```powershell
git push origin --delete feature/<short-description>
```

---

## Rules that prevent branching spaghetti

- Keep branches small.
- Keep PRs focused.
- Merge often.
- Sync your branch with `main` if `main` changes while you work.
- Delete branches after merging.
- Prefer PRs over direct pushes to `main`.

---

## Syncing your branch when `main` changes

Simple and team-friendly approach: merge `origin/main` into your branch.

```powershell
git checkout feature/<short-description>
git fetch origin
git merge origin/main
```

If conflicts happen:

1. Resolve the conflicts in the affected files.
2. Then run:

```powershell
git add -A
git commit
git push
```

---

## Project-specific contribution rules

### Respect the project layout

Place new code according to its role:

- developer helper or startup scripts -> `scripts/`
- MCP exposure logic -> `src/grad_applicant_system/mcp/`
- parsing or persistence implementations -> `src/grad_applicant_system/infrastructure/`
- use-cases and orchestration logic -> `src/grad_applicant_system/application/`
- UI code -> `src/grad_applicant_system/presentation/`
- database init or schema SQL -> `db/`
- tests and smoke checks -> `tests/`

Do not place new files in random locations when an existing folder already matches the responsibility.

### Be careful with environment and Docker changes

If you change any of the following:

- `docker-compose.yml`
- `.env.example`
- `db/init/`
- startup scripts in `scripts/`
- dependency declarations in `requirements.txt`

make sure your PR description explains:

- what changed
- why it changed
- whether teammates need to rebuild containers, recreate `.env`, or reinstall dependencies

### Keep `.env.example` safe

- `.env.example` should contain placeholders only.
- Never commit real usernames, passwords, tokens, or private connection strings.
- If a new environment variable becomes required, add it to `.env.example` and document it in `README.md`.

### Do not commit local secrets or machine-specific files

Never commit:

- `.env`
- `.venv/`
- `__pycache__/`
- local IDE settings that are machine-specific
- local database dumps
- Docker volumes
- temporary parsing output files unless they are intentionally tracked fixtures
- OS-generated junk files such as `.DS_Store`

---

## Essential commands

### Repo state

```powershell
git status
```

This shows:

- your current branch
- changed files
- staged versus unstaged changes
- whether you are ahead of or behind `origin/<branch>`

### See branches

```powershell
git branch
```

### See recent history

```powershell
git log --oneline --graph --decorate -n 20
```

### See unstaged changes

```powershell
git diff
```

### See staged changes

```powershell
git diff --staged
```

---

## Undo and recovery

### Unstage something but keep the file changes

```powershell
git restore --staged <file>
```

### Discard local changes to a file

Danger: this loses your uncommitted edits.

```powershell
git restore <file>
```

### Fix the last commit message

Only do this if the commit has not been pushed yet.

```powershell
git commit --amend
```

### Stash work temporarily

```powershell
git stash
git checkout main
```

Later:

```powershell
git stash pop
```

---

## What a PR is

A PR (Pull Request) is a GitHub workflow object that says:

> I have changes on this branch. Please merge them into that branch, usually `main`.

PRs:

- show the exact file changes
- allow comments and review
- provide a safe path into `main`
- create a shared record of why a change was made

---

## PR checklist

Before opening a PR, confirm that:

- you branched from an updated `main`
- your branch is focused on one task
- the project still starts successfully
- the MCP smoke test still works if your changes affect backend behavior
- you updated `README.md` or `.env.example` if setup changed
- you did not commit secrets or local-only files
- your PR title and description clearly explain the change

---

## Commit message examples

Good examples:

- `Add initial applicant repository interface`
- `Fix MySQL port mapping for local Docker setup`
- `Add smoke-test instructions to README`
- `Refactor MCP startup script into helper module`

Try to avoid vague messages such as:

- `update stuff`
- `changes`
- `fix`
- `work in progress`

---

## Final team guideline

When in doubt:

1. pull `main`
2. make a small branch
3. make one focused change
4. test locally
5. open a PR
6. merge and clean up

That workflow will keep the repo understandable and stable as the project grows.