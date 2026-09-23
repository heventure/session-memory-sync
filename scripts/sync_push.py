#!/usr/bin/env python3
"""Extract sessions belonging to the current workDir and commit them into the memory repo.

Usage: sync_push.py <repo-path> [--workdir DIR] [--message MSG]

Repo layout: <repo>/<project-key>/sessions/<sessionId>/... plus index.jsonl.
"""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import git, has_upstream, kimi_home, load_index, project_key, repo_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", help="local clone of the memory git repo")
    ap.add_argument("--workdir", default=str(Path.cwd()))
    ap.add_argument("--message", default=None)
    a = ap.parse_args()

    repo = repo_path(a.repo)
    home = kimi_home()
    rows = [r for r in load_index(home) if r.get("workDir") == a.workdir and r["sessionId"].startswith("conv-")]
    if not rows:
        sys.exit(f"no sessions found for workDir {a.workdir}")

    proj = project_key(a.workdir)
    dest_root = repo / proj / "sessions"
    dest_root.mkdir(parents=True, exist_ok=True)

    copied = []
    for r in rows:
        src = Path(r["sessionDir"])
        if not src.is_dir():
            continue
        dest = dest_root / r["sessionId"]
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        copied.append(r["sessionId"])

    meta = {"workDir": a.workdir, "project": proj,
            "syncedAt": datetime.now(timezone.utc).isoformat(), "sessions": copied}
    (repo / proj / "index.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")

    if has_upstream(repo):
        git(repo, "pull", "--rebase", "--autostash")
    git(repo, "add", proj)
    if not git(repo, "status", "--porcelain", "--", proj):
        print("nothing new to commit")
        return
    msg = a.message or f"sync {proj}: {len(copied)} session(s)"
    git(repo, "commit", "-m", msg)
    if has_upstream(repo):
        git(repo, "push")
    print(f"committed {len(copied)} session(s) for {a.workdir} -> {proj}/")


if __name__ == "__main__":
    main()
