#!/usr/bin/env python3
"""Pull the memory repo and restore session memory into the local session home.

Usage:
  sync_pull.py <repo-path> --list                 # list projects and sessions in the repo
  sync_pull.py <repo-path> [--project KEY]        # restore one project (default: current workDir's)
  sync_pull.py <repo-path> --all                  # restore every project

Restore copies session dirs back into the session home (never overwriting a newer
local session) and merges entries into session_index.jsonl so the agent can see them.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from common import git, has_upstream, kimi_home, load_index, project_key, repo_path, save_index


def list_projects(repo: Path) -> None:
    for proj in sorted(p for p in repo.iterdir() if p.is_dir() and not p.name.startswith(".")):
        meta_file = proj / "index.json"
        if meta_file.exists():
            m = json.loads(meta_file.read_text())
            print(f"{proj.name}\tworkDir={m.get('workDir')}\tsessions={len(m.get('sessions', []))}\tsyncedAt={m.get('syncedAt')}")


def restore_project(repo: Path, home: Path, proj_dir: Path) -> int:
    meta_file = proj_dir / "index.json"
    if not meta_file.exists():
        return 0
    meta = json.loads(meta_file.read_text())
    work_dir = meta["workDir"]
    rows = load_index(home)
    by_id = {r["sessionId"]: r for r in rows}
    restored = 0
    for sess in sorted((proj_dir / "sessions").iterdir()):
        if not sess.is_dir():
            continue
        sid = sess.name
        # reuse the existing wd_* dir for this workDir if one exists, else create one
        base = Path(work_dir).name
        existing = by_id.get(sid, {}).get("sessionDir")
        if existing:
            target = Path(existing)
        else:
            wd_dirs = sorted((home / "sessions").glob(f"wd_{base}*"))
            target = (wd_dirs[0] if wd_dirs else home / "sessions" / f"wd_{base}") / sid
        if target.exists():
            # keep whichever copy is newer
            local_new = max((f.stat().st_mtime for f in target.rglob("*") if f.is_file()), default=0)
            repo_new = max((f.stat().st_mtime for f in sess.rglob("*") if f.is_file()), default=0)
            if local_new >= repo_new:
                continue
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(sess, target)
        by_id[sid] = {"sessionId": sid, "sessionDir": str(target), "workDir": work_dir}
        restored += 1
    if restored:
        save_index(home, list(by_id.values()))
    return restored


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?")
    ap.add_argument("--project", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--workdir", default=str(Path.cwd()))
    a = ap.parse_args()

    repo = repo_path(a.repo)
    if has_upstream(repo):
        git(repo, "pull", "--rebase", "--autostash")

    if a.list:
        list_projects(repo)
        return

    home = kimi_home()
    keys = ([a.project] if a.project
            else None if a.all
            else [project_key(a.workdir)])
    proj_dirs = ([p for p in repo.iterdir() if (p / "index.json").exists()] if keys is None
                 else [repo / k for k in keys])
    total = 0
    for pd in proj_dirs:
        if pd.is_dir():
            n = restore_project(repo, home, pd)
            total += n
            print(f"{pd.name}: restored {n} session(s)")
    print(f"done, {total} session(s) restored into {home / 'sessions'}")


if __name__ == "__main__":
    main()
