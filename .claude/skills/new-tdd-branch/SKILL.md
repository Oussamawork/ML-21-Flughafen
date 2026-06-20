---
name: new-tdd-branch
description: Start work on a TDD by creating its dedicated git branch following the repo's one-branch/one-PR-per-TDD convention. Invoke as /new-tdd-branch <NN> (e.g. /new-tdd-branch 02).
disable-model-invocation: true
---

# new-tdd-branch

Encodes this repo's convention (see `CLAUDE.md` and `docs/tdd/README.md`): each TDD
component gets **one branch and one PR**. Given a TDD number, create and switch to
its branch.

## Steps

1. Read the argument as a zero-padded TDD number `NN` (e.g. `02`). If the user
   gave a bare number, zero-pad to two digits.
2. Find the matching TDD file: `ls docs/tdd/TDD-<NN>-*.md`. If none matches, list
   the available TDDs from `docs/tdd/README.md` and stop.
3. Derive the branch slug from the filename: lowercase, drop the `.md`, e.g.
   `TDD-02-LLM-Agent.md` → `tdd-02-llm-agent`. Branch name: `claude/tdd-02-llm-agent`.
4. Make sure the working tree is clean and `main` is up to date:
   - `git switch main && git pull --ff-only`
   - If there are uncommitted changes, stop and tell the user.
5. Create the branch: `git switch -c claude/<slug>`.
6. Report: branch created, the TDD file it maps to, and remind the user the PR for
   this branch should link `docs/tdd/TDD-<NN>-*.md` and update its status in
   `docs/tdd/README.md` + `docs/PROGRESS.md`.

Do **not** start implementing the TDD — this skill only sets up the branch.
