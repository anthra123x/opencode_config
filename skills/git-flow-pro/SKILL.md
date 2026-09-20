---
name: git-flow-pro
description: Professional Git and GitHub workflow standards, conventional commits, branch management, PR lifecycles, and conflict resolution.
---

# Git Flow Pro: Enterprise Git & GitHub Engineering

Mastery standard for Git and GitHub workflows in collaborative multi-agent environments.

## 1. Conventional Commits Standard

Every commit message MUST follow the Conventional Commits specification:

```
<type>(<scope>): <short description in imperative mood>

[optional body explaining 'why', context, and trade-offs]

[optional footer(s): Closes #123, BREAKING CHANGE: ...]
```

### Commit Types:
- `feat`: A new feature or enhancement for the end user
- `fix`: A bug fix
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Code change that improves execution performance
- `test`: Adding missing tests or correcting existing tests
- `docs`: Documentation changes only
- `chore`: Maintenance, dependencies, tool configurations
- `ci`: Changes to CI/CD workflows and automation scripts

### Rules:
1. **Imperative, present tense**: "add user route", NOT "added user route" or "adds user route".
2. **First letter lowercase** (unless proper noun).
3. **No trailing period** in the subject line.
4. **Atomic commits**: One logical change per commit. Never mix refactoring with feature development.

---

## 2. Branch Naming Conventions

Always use structured, hierarchical branch names:

```
feature/<ticket-or-slug>     # e.g., feature/auth-jwt-refresh
fix/<ticket-or-slug>         # e.g., fix/null-pointer-session
refactor/<ticket-or-slug>    # e.g., refactor/db-connection-pool
chore/<ticket-or-slug>       # e.g., chore/upgrade-dependencies
release/vX.Y.Z               # e.g., release/v2.1.0
hotfix/vX.Y.Z                # e.g., hotfix/v2.1.1
```

---

## 3. Pre-Commit Verification Gate

Before staging or committing any code, verify:
1. `git status` — Ensure no stray, temporary, or sensitive `.env` files are staged.
2. `git diff` — Review every single changed line for debugging prints (`console.log`, `print`), commented-out code, or formatting glitches.
3. **Build & Lint Check**: Verify that `npm run lint` / `cargo check` / `ruff check` passes.
4. **Test Suite**: Relevant unit and integration tests must be green.

---

## 4. Pull Request (PR) Crafting Protocol

When opening a Pull Request or preparing a PR summary:

```markdown
## Summary
Brief 2-3 sentence overview of what this PR accomplishes and why it is needed.

## Key Changes
- **Component / Module**: Specific implementation highlights
- **Database / Schema**: Any migrations or index adjustments
- **API / Contract**: Changes in endpoints or request/response shapes

## Verification & Testing
- [x] Unit tests passed (`npm test` / `pytest`)
- [x] Linting and type checking clean
- [x] Manual verification performed

## Breaking Changes / Migrations
- None (or list any required manual steps / env vars)
```

---

## 5. Merge Conflict Resolution Protocol

1. Pull latest upstream/main branch into local tracking:
   ```bash
   git fetch origin
   git merge origin/main   # Or: git rebase origin/main
   ```
2. Identify conflicts with `git status`.
3. Open conflicting files:
   - Identify base, current, and incoming changes.
   - Preserve intended functional logic of BOTH branches.
   - Never blindly accept current or incoming without inspecting imports and dependents.
4. Run tests immediately after resolving conflicts.
5. Finalize merge:
   ```bash
   git add <resolved-files>
   git commit -m "chore(git): resolve merge conflicts with main"
   ```

---

## 6. Multi-Agent Team Collaboration Sync

When operating as `@git-flow` in a Team Swarm:
- Call `team_read_feed()` to identify tasks marked as `ready_for_review`.
- Verify diffs against the shared contracts from `team_get_artifact()`.
- Create clean, semantic commits and branch structures.
- Broadcast PR readiness and commit hashes via `team_broadcast(sender="git-flow", message=...)`.
