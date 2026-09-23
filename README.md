# session-memory-sync

An agent skill that syncs coding-agent session memory to and from a git repository, organized per project and per agent — one repo manages memory for all your projects and all your agents.

Works with **Kimi Work / Kimi Code**, **Codex**, and **Claude Code** out of the box; other agents (opencode, deepseek-harness, pi, …) can be added via a one-function adapter in `scripts/agents.py`.

## Install

```bash
npx skills add heventure/session-memory-sync
```

Compatible with any agent runtime that supports SKILL.md-style skills.

## How it works

- **Push**: extracts the current workspace's session files into `<repo>/<project>/<agent>/`, then commits and pushes.
- **Pull**: lists projects in the repo and restores sessions back into each agent's local session store — never overwriting a newer local copy.
- **Repo layout**: `<repo>/<project>/<agent>/` + `<project>/<agent>.index.json`. One private repo covers many projects; agents can pull another project's history to learn from it.

## Usage

```bash
# save current project's sessions (auto-detects installed agents)
python3 scripts/sync_push.py <repo-path> --workdir "$PWD"
python3 scripts/sync_push.py <repo-path> --agent codex   # or kimi / claude / all

# restore
python3 scripts/sync_pull.py <repo-path> --list
python3 scripts/sync_pull.py <repo-path> [--project <key>] [--agent <name>]
python3 scripts/sync_pull.py <repo-path> --all
```

Point the scripts at a local clone of your memory repo (argument or `SESSION_MEMORY_REPO` env var). See [SKILL.md](SKILL.md) for the full workflow, including first-run onboarding.

**Note:** session files contain full conversation content — use a **private** memory repo.
