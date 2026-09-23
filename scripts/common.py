"""Shared helpers for session-memory-sync scripts."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_HOME = Path.home() / "Library/Application Support/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home"


def kimi_home() -> Path:
    return Path(os.environ.get("KIMI_HOME", DEFAULT_HOME)).expanduser()


def index_path(home: Path) -> Path:
    return home / "session_index.jsonl"


def load_index(home: Path) -> list[dict]:
    p = index_path(home)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def save_index(home: Path, rows: list[dict]) -> None:
    p = index_path(home)
    seen = set()
    out = []
    for r in rows:
        sid = r["sessionId"]
        if sid in seen:
            continue
        seen.add(sid)
        out.append(json.dumps(r, ensure_ascii=False))
    p.write_text("\n".join(out) + "\n")


_AUTO_NAME = re.compile(r"^[0-9a-f]{8}$|^\d{2}-\d{2}-\d{2}-[0-9a-f]{6,}$|^[0-9a-f-]{12,}$")


def _git_repo_name(work_dir: str) -> str | None:
    r = subprocess.run(["git", "-C", work_dir, "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return Path(r.stdout.strip()).name or None
    return None


def project_key(work_dir: str) -> str:
    """Readable, stable, filesystem-safe top-level directory name for a project.

    Priority: git repo name > derived name for auto-generated workspace dirs
    (e.g. Kimi task dirs like ``11-37-48-dad645d7`` -> ``kimi-task-<parent>-<hash>``)
    > sanitized basename.
    """
    repo = _git_repo_name(work_dir)
    if repo:
        name = repo
    else:
        name = Path(work_dir).name or work_dir
        if _AUTO_NAME.match(name):
            parent = Path(work_dir).parent.name
            short = re.search(r"[0-9a-f]{6,}", name)
            suffix = short.group(0)[:8] if short else "x"
            name = f"kimi-task-{parent}-{suffix}" if parent else f"kimi-task-{suffix}"
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")


def repo_path(arg: str | None) -> Path:
    """Resolve the memory repo: CLI arg > env var; error otherwise."""
    src = arg or os.environ.get("SESSION_MEMORY_REPO")
    if not src:
        sys.exit("error: pass the repo path as an argument or set SESSION_MEMORY_REPO")
    p = Path(src).expanduser()
    if not (p / ".git").exists():
        sys.exit(f"error: {p} is not a git repository (clone the memory repo there first)")
    return p


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def has_upstream(repo: Path) -> bool:
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
                       capture_output=True, text=True)
    return r.returncode == 0
