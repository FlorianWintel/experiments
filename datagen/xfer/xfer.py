#!/usr/bin/env python3
"""Continuously transfer data from Idun to the local machine."""

from dataclasses import dataclass
import re
import sys
import json
import subprocess
import time
from pathlib import Path
import typing as t


@dataclass
class Args:
    idun_path_str: str
    local_path_str: str


def parse_args():
    args = sys.argv[1:]

    run = args[0]

    idun_path_str = f"work/thesis/datagen/output/{run}/data/"
    local_path_str = f"/data/work/aasewold/datagen/transfuser/{run}/data/"

    to_path = Path(local_path_str)
    if not to_path.exists():
        print(f"Creating {to_path}")
        to_path.mkdir(parents=True)

    return Args(idun_path_str, local_path_str)


def rsync_data(args: Args):
    """Rsync all data from the remote machine."""
    subprocess.run(
        [
            "rsync",
            "-az",
            '--info=progress2',
            f"idun:{args.idun_path_str}",
            f"{args.local_path_str}",
        ]
    )


def find_checkpoints(args: Args):
    """Find all checkpoint.json files in the local directory."""
    for path in Path(args.local_path_str).rglob("checkpoint.json"):
        text = path.read_text()
        if not text:
            continue
        data = json.loads(text)
        checkpoint = data.get("_checkpoint", {})
        progress = checkpoint.get("progress", [])
        if not progress:
            continue
        curr, tot = progress
        yield path.parent, (curr, tot)


def find_deletable(path: Path, p_curr: int, p_tot: int):
    """Find all routes before the current route."""
    for sub in path.iterdir():
        if not sub.is_dir():
            continue
        route_num = re.match(r"[a-zA-Z0-9_]+_route(\d+)_[a-zA-Z0-9_]+", sub.name)
        if route_num:
            route_num = int(route_num.group(1))
            if route_num < p_curr:
                yield sub


def translate_deletable_paths(args: Args, paths: t.List[Path]):
    remote_paths: t.List[str] = []
    for local_path in paths:
        local_path_str = str(local_path)
        if not local_path_str.startswith(args.local_path_str):
            raise ValueError(f"Unexpected local path {local_path_str}")
        local_path_rel = local_path_str[len(args.local_path_str) :]
        remote_path = args.idun_path_str + local_path_rel
        remote_paths.append(remote_path)
    return remote_paths


def delete_paths(paths: t.List[str]):
    cmd = [
        "ssh",
        "idun",
        "rm",
        "-rf",
        *paths,
    ]
    subprocess.run(cmd)


def main():
    args = parse_args()

    already_deleted = set()

    while True:
        print('date:', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        rsync_data(args)

        for path, (p_curr, p_tot) in find_checkpoints(args):
            deletables = sorted(find_deletable(path, p_curr, p_tot))
            remote_paths = translate_deletable_paths(args, deletables)
            remote_paths = [p for p in remote_paths if p not in already_deleted]
            if remote_paths:
                print(f"Deleting {len(remote_paths)} routes from {path.name} with progress {p_curr}/{p_tot}")
                for d in remote_paths:
                    print(f" - {d}")
                delete_paths(remote_paths)
                already_deleted.update(remote_paths)

        time.sleep(10 * 60)


if __name__ == "__main__":
    main()
