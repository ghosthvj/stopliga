#!/usr/bin/env python3

from __future__ import annotations

import os
import pathlib
import sys


DEFAULT_UID = 10001
DEFAULT_GID = 10001


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{name} must be >= 0")
    return parsed


def _candidate_paths() -> list[pathlib.Path]:
    configured = [
        pathlib.Path(os.environ.get("STOPLIGA_STATE_FILE", "/data/state.json")),
        pathlib.Path(os.environ.get("STOPLIGA_LOCK_FILE", "/data/stopliga.lock")),
        pathlib.Path(os.environ.get("STOPLIGA_BOOTSTRAP_GUARD_FILE", "/data/bootstrap_guard.json")),
    ]
    parents = [path.parent for path in configured]
    return parents + configured


def _ensure_writable_paths(uid: int, gid: int) -> None:
    seen: set[pathlib.Path] = set()
    for path in _candidate_paths():
        if path in seen:
            continue
        seen.add(path)
        if path.exists() and path.is_symlink():
            raise RuntimeError(f"Refusing to operate on symlinked path: {path}")
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                continue
        else:
            path.mkdir(parents=True, exist_ok=True)
        if path.parent.exists() and path.parent.is_symlink():
            raise RuntimeError(f"Refusing to operate on symlinked parent path: {path.parent}")
        try:
            os.chown(path, uid, gid)
        except PermissionError:
            if os.access(path, os.W_OK):
                continue
            raise


def _drop_privileges(uid: int, gid: int) -> None:
    try:
        os.setgroups([])
    except PermissionError:
        pass

    if os.getegid() != gid:
        try:
            os.setgid(gid)
        except PermissionError as exc:
            raise PermissionError(
                f"Unable to switch group to {gid}; run the container as that user/group or allow SETGID"
            ) from exc

    if os.geteuid() != uid:
        try:
            os.setuid(uid)
        except PermissionError as exc:
            raise PermissionError(
                f"Unable to switch user to {uid}; run the container as that user/group or allow SETUID"
            ) from exc


def main() -> int:
    uid = _env_int("STOPLIGA_UID", DEFAULT_UID)
    gid = _env_int("STOPLIGA_GID", DEFAULT_GID)

    if os.geteuid() == 0:
        _ensure_writable_paths(uid, gid)
        _drop_privileges(uid, gid)

    os.execvp("stopliga", ["stopliga", *sys.argv[1:]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
