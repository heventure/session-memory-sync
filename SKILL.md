---
name: session-memory-sync
description: Sync Kimi Work agent session memory to and from a user-provided git repository. Use when the user asks to save/commit/back up the current session's memory, extract session files into a git repo, restore or pull session memory from the repo, resume past conversations on another machine, or reference other projects' session history. The repo's top-level directories are per-project, so one repo manages memory for many projects.
---

# Session Memory Sync

Sync agent session files between the local session home and a git repository, organized per project.

## Concepts

- **Session home**: `$KIMI_HOME` or `~/Library/Application Support/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home`. Sessions live under `<home>/sessions/<wd_*>/<sessionId>/` (state.json + agents/*/wire.jsonl); `<home>/session_index.jsonl` maps sessionId → sessionDir → workDir.
- **Memory repo**: one git repo per user. Top-level dir = sanitized project dir name (`project_key` in scripts/common.py), containing `index.json` (workDir, sync time, session list) and `sessions/<sessionId>/`.
- Repo location: pass as first CLI arg, or set env `SESSION_MEMORY_REPO`. The repo must be cloned locally first; if the user only has a remote URL, clone it before running scripts.

## Push (save current session memory)

```bash
python3 scripts/sync_push.py <repo-path> --workdir "$PWD"
```

Copies all `conv-*` sessions whose workDir is the current workspace into `<repo>/<project>/sessions/`, pulls with rebase, commits and pushes. Run at the end of a meaningful work session, or when the user asks to save/commit memory.

## Pull (restore session memory)

```bash
python3 scripts/sync_pull.py <repo-path> --list              # show projects in the repo
python3 scripts/sync_pull.py <repo-path>                     # restore current project
python3 scripts/sync_pull.py <repo-path> --project <key>     # restore another project
python3 scripts/sync_pull.py <repo-path> --all               # restore everything
```

Never overwrites a newer local session copy; merges restored sessions into `session_index.jsonl` so the agent can discover and resume them.

## Cross-project memory

To let the agent learn from another project's experience: `--list`, then `--project <key>` to restore it, then read the restored `wire.jsonl` / `state.json` files directly, or resume those sessions per the agent-session-resume workflow.

## Notes

- Session files can contain full conversation content — commit only to a repo the user controls; suggest a **private** repo.
- Both scripts require `git` and network access for pull/push; failures exit non-zero with the git error.
