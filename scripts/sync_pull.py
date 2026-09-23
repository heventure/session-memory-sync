#!/usr/bin/env python3
"""Pull the memory repo and restore session memory into local agent session homes.

Usage:
  sync_pull.py <repo-path> --list                  # list projects/agents/sessions in the repo
  sync_pull.py <repo-path> [--project KEY] [--agent NAME]   # restore (default: current workDir, all agents)
  sync_pull.py <repo-path> --all                   # restore every project

Never overwrites a newer local copy. Kimi sessions are additionally merged into
session_index.jsonl so the agent can discover them.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from agents import copy_restore_root
from common import (git, has_upstream, kimi_home, load_index, project_key,
                    repo_path, save_index)


def iter_projects(repo: Path):
    return sorted(p for p in repo.iterdir() if p.is_dir() and any(p.glob("*.index.json")))


def list_projects(repo: Path) -> None:
    for proj in iter_projects(repo):
        for meta_file in sorted(proj.glob("*.index.json")):
            m = json.loads(meta_file.read_text())
            print(f"{proj.name}\tagent={m['agent']}\tworkDir={m.get('workDir')}\t"
                  f"sessions={len(m.get('sessions', []))}\tsyncedAt={m.get('syncedAt')}")


def newest_mtime(p: Path) -> float:
    if p.is_file():
        return p.stat().st_mtime
    return max((f.stat().st_mtime for f in p.rglob("*") if f.is_file()), default=0)


def restore_kimi(sess: Path, workdir: str, home: Path, by_id: dict) -> bool:
    sid = sess.name
    existing = by_id.get(sid, {}).get("sessionDir")
    if existing:
        target = Path(existing)
    else:
        base = Path(workdir).name
        wd_dirs = sorted((home / "sessions").glob(f"wd_{base}*"))
        target = (wd_dirs[0] if wd_dirs else home / "sessions" / f"wd_{base}") / sid
    if target.exists() and newest_mtime(target) >= newest_mtime(sess):
        return False
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sess, target)
    by_id[sid] = {"sessionId": sid, "sessionDir": str(target), "workDir": workdir}
    return True


def restore_files(proj_dir: Path, agent: str, workdir: str) -> int:
    root = copy_restore_root(agent)
    if root is None:
        return 0
    if agent == "claude":
        root = root / workdir.replace("/", "-")
    n = 0
    for src in sorted((proj_dir / agent).rglob("*")):
        if not src.is_file():
            continue
        dest = root / src.relative_to(proj_dir / agent)
        if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        n += 1
    return n


def restore_project(repo: Path, proj_dir: Path, only_agent: str | None) -> int:
    total = 0
    for meta_file in sorted(proj_dir.glob("*.index.json")):
        meta = json.loads(meta_file.read_text())
        agent = meta["agent"]
        if only_agent and agent != only_agent:
            continue
        workdir = meta["workDir"]
        if agent == "kimi":
            home = kimi_home()
            rows = load_index(home)
            by_id = {r["sessionId"]: r for r in rows}
            n = 0
            for sess in sorted((proj_dir / "kimi").iterdir()):
                if sess.is_dir() and restore_kimi(sess, workdir, home, by_id):
                    n += 1
            if n:
                save_index(home, list(by_id.values()))
        else:
            n = restore_files(proj_dir, agent, workdir)
        print(f"{proj_dir.name}/{agent}: restored {n}")
        total += n
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?")
    ap.add_argument("--project", default=None)
    ap.add_argument("--agent", default=None)
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

    proj_dirs = (iter_projects(repo) if a.all
                 else [repo / (a.project or project_key(a.workdir))])
    total = 0
    for pd in proj_dirs:
        if pd.is_dir():
            total += restore_project(repo, pd, a.agent)
    print(f"done, {total} item(s) restored")


if __name__ == "__main__":
    main()
