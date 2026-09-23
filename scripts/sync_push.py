#!/usr/bin/env python3
"""Extract sessions belonging to the current workDir and commit them into the memory repo.

Usage: sync_push.py <repo-path> [--workdir DIR] [--agent auto|kimi|codex|claude|all] [--message MSG]

Repo layout: <repo>/<project-key>/<agent>/<rel-path> plus <project-key>/<agent>.index.json.
"""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from agents import ADAPTERS, detect_agents
from common import git, has_upstream, project_key, repo_path


def copy_entry(entry: dict, dest_root: Path) -> None:
    src = entry["src"]
    dest = dest_root / entry["rel"]
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", help="local clone of the memory git repo")
    ap.add_argument("--workdir", default=str(Path.cwd()))
    ap.add_argument("--agent", default="auto", choices=["auto", "all", *ADAPTERS])
    ap.add_argument("--message", default=None)
    a = ap.parse_args()

    repo = repo_path(a.repo)
    agents = list(ADAPTERS) if a.agent == "all" else ([a.agent] if a.agent != "auto" else detect_agents())
    if not agents:
        sys.exit("no agent session homes detected on this machine")

    proj = project_key(a.workdir)
    pushed = {}
    for agent in agents:
        entries = ADAPTERS[agent](a.workdir)
        if not entries:
            continue
        dest_root = repo / proj / agent
        dest_root.mkdir(parents=True, exist_ok=True)
        for e in entries:
            copy_entry(e, dest_root)
        meta = {"agent": agent, "workDir": a.workdir, "project": proj,
                "syncedAt": datetime.now(timezone.utc).isoformat(),
                "sessions": [e["id"] for e in entries]}
        (repo / proj / f"{agent}.index.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
        pushed[agent] = len(entries)

    if not pushed:
        sys.exit(f"no sessions found for workDir {a.workdir}")

    if has_upstream(repo):
        git(repo, "pull", "--rebase", "--autostash")
    git(repo, "add", proj)
    if not git(repo, "status", "--porcelain", "--", proj):
        print("nothing new to commit")
        return
    msg = a.message or f"sync {proj}: " + ", ".join(f"{k}={v}" for k, v in pushed.items())
    git(repo, "commit", "-m", msg)
    if has_upstream(repo):
        git(repo, "push")
    print(f"committed sessions for {a.workdir} -> {proj}/: {pushed}")


if __name__ == "__main__":
    main()
