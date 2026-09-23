"""Per-agent session store adapters.

Each adapter knows where one agent family keeps session files and yields
entries: dict(id=<stable id>, src=<Path to file or dir>, rel=<repo-relative name>).
Restore copies entries back to their original home.
"""
import json
import os
from pathlib import Path

from common import kimi_home, load_index


def kimi_sessions(workdir: str) -> list[dict]:
    home = kimi_home()
    out = []
    for r in load_index(home):
        if r.get("workDir") == workdir and r["sessionId"].startswith("conv-"):
            src = Path(r["sessionDir"])
            if src.is_dir():
                out.append({"id": r["sessionId"], "src": src, "rel": src.name})
    return out


def codex_sessions(workdir: str) -> list[dict]:
    root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    out = []
    if not root.is_dir():
        return out
    for f in sorted(root.rglob("rollout-*.jsonl")):
        try:
            with f.open() as fh:
                first = json.loads(fh.readline())
            meta = first.get("payload", {})
            if first.get("type") == "session_meta" and meta.get("cwd") == workdir:
                out.append({"id": meta.get("session_id", f.stem), "src": f,
                            "rel": str(f.relative_to(root))})
        except (json.JSONDecodeError, OSError):
            continue
    return out


def claude_sessions(workdir: str) -> list[dict]:
    slug = workdir.replace("/", "-")
    root = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")) / "projects" / slug
    out = []
    if not root.is_dir():
        return out
    for f in sorted(root.glob("*.jsonl")):
        out.append({"id": f.stem, "src": f, "rel": f.name})
    return out


# Simple file/dir-copy restore for non-kimi agents
def copy_restore_root(agent: str) -> Path | None:
    if agent == "codex":
        return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    if agent == "claude":
        slug_root = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")) / "projects"
        return slug_root
    return None


ADAPTERS = {
    "kimi": kimi_sessions,
    "codex": codex_sessions,
    "claude": claude_sessions,
}


def detect_agents() -> list[str]:
    """Agents whose session homes exist on this machine."""
    found = []
    if kimi_home().exists():
        found.append("kimi")
    if (Path.home() / ".codex" / "sessions").is_dir():
        found.append("codex")
    if (Path.home() / ".claude" / "projects").is_dir():
        found.append("claude")
    return found
