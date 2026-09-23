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


def project_key(work_dir: str) -> str:
    """Stable, filesystem-safe top-level directory name for a project."""
    name = Path(work_dir).name or work_dir
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
