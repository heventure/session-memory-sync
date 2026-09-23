# session-memory-sync

A [Kimi](https://www.kimi.com/) skill that syncs agent session memory to and from a git repository, organized per project — one repo manages memory for all your projects.

## Install

```bash
npx skills add heventure/session-memory-sync
```

## Usage

Point the skill at a local clone of your memory repo (argument or `SESSION_MEMORY_REPO` env var), then ask the agent to save or restore session memory. See [SKILL.md](SKILL.md) for the full workflow.

```bash
# save current project's sessions
python3 scripts/sync_push.py <repo-path> --workdir "$PWD"

# restore
python3 scripts/sync_pull.py <repo-path> --list
python3 scripts/sync_pull.py <repo-path> [--project <key> | --all]
```

Repo layout: `<repo>/<project>/index.json` + `sessions/<sessionId>/`.

**Note:** session files contain full conversation content — use a **private** memory repo.
