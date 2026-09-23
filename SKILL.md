---
name: session-memory-sync
description: Sync agent session memory (Kimi Work, Codex, Claude Code, and other CLI agents) to and from a user-controlled git repository. Use when the user asks to save/commit/back up the current session's memory, extract session files into a git repo, restore or pull session memory, resume past conversations on another machine, or reference other projects' session history. The repo's top-level directories are per-project, with per-agent subdirectories, so one repo manages memory for many projects and many agents.
---

# Session Memory Sync

Sync agent session files between local session stores and a git repository, organized per project and per agent. Works with multiple agent families; adapters live in `scripts/agents.py`:

- **kimi** — Kimi Work / Kimi Code (`$KIMI_HOME` or the default daimon runtime home; uses `session_index.jsonl`)
- **codex** — Codex CLI/Desktop (`~/.codex/sessions/**/rollout-*.jsonl`, matched by `session_meta.cwd`)
- **claude** — Claude Code (`~/.claude/projects/<path-slug>/*.jsonl`)

To add another agent (opencode, deepseek-harness, pi, …), add one extractor function to `scripts/agents.py` and register it in `ADAPTERS`.

## First use: onboard the memory repo

On the first run in a new environment, ALWAYS ask the user which they prefer before doing anything:

1. **User-provided repo** — the user gives a remote URL or local path; clone it if needed.
2. **Agent-created repo** — create a new **private** repo for the user (e.g. `gh repo create session-memory --private`), clone it, and make an initial commit.

Then remember the local path (env `SESSION_MEMORY_REPO`, or pass it as the first CLI arg). Session files contain full conversation content — the repo MUST be private unless the user insists otherwise.

## Push (save current session memory)

```bash
python3 scripts/sync_push.py <repo-path> --workdir "$PWD"                # auto-detect agents
python3 scripts/sync_push.py <repo-path> --agent codex                   # one agent only
python3 scripts/sync_push.py <repo-path> --agent all                     # every supported agent
```

Copies matching sessions into `<repo>/<project>/<agent>/`, writes `<project>/<agent>.index.json`, pulls with rebase, commits and pushes. Project naming priority: git repo name > derived readable name for auto-generated workspace dirs (e.g. `11-37-48-dad645d7` → `kimi-task-2026-09-23-dad645d7`) > sanitized basename. Run at the end of a meaningful work session or when the user asks to save memory.

## Pull (restore session memory)

```bash
python3 scripts/sync_pull.py <repo-path> --list              # projects × agents in the repo
python3 scripts/sync_pull.py <repo-path>                     # restore current project, all agents
python3 scripts/sync_pull.py <repo-path> --project <key> --agent codex
python3 scripts/sync_pull.py <repo-path> --all               # restore everything
```

Never overwrites a newer local copy. Kimi sessions are merged into `session_index.jsonl`; codex/claude files are copied back to their original session stores.

## Cross-project memory

To let the agent learn from another project's experience: `--list`, then restore with `--project <key>`, then read the restored session files directly or resume those sessions with the agent's own resume mechanism.

## Notes

- Both scripts require `git`; pull/push steps are skipped automatically when the repo has no upstream.
- Failures exit non-zero with the underlying git error.
