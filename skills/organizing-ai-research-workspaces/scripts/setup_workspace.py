#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex
import stat
import sys
import tempfile


START_MARKER = "# >>> research-workspace >>>"
END_MARKER = "# <<< research-workspace <<<"
_MODE_UNSET = object()


class WorkspaceError(Exception):
    """Raised when the requested workspace cannot be set up safely."""


def _resolved_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _workspace_paths(root: Path) -> list[tuple[str, Path]]:
    return [
        ("RESEARCH_ROOT", root),
        ("PROJECTS_ROOT", root / "projects"),
        ("SHARED_ROOT", root / "shared"),
        ("DATASETS_ROOT", root / "shared" / "datasets"),
        ("PRETRAINED_ROOT", root / "shared" / "pretrained"),
        ("RUNS_ROOT", root / "runs"),
        ("SCRATCH_ROOT", root / "scratch"),
    ]


def _env_contents(workspace_paths: list[tuple[str, Path]]) -> str:
    return "".join(
        f"export {name}={shlex.quote(str(path))}\n"
        for name, path in workspace_paths
    )


def _shell_block(env_file: Path) -> str:
    quoted_path = shlex.quote(str(env_file))
    return "\n".join(
        (
            START_MARKER,
            f"[ -f {quoted_path} ] && . {quoted_path}",
            END_MARKER,
        )
    )


def _updated_shell_contents(existing: str, block: str) -> str:
    start_matches = list(
        re.finditer(rf"(?m)^{re.escape(START_MARKER)}\r?$", existing)
    )
    end_matches = list(
        re.finditer(rf"(?m)^{re.escape(END_MARKER)}\r?$", existing)
    )
    if not start_matches and not end_matches:
        separator = "" if not existing or existing.endswith("\n") else "\n"
        return f"{existing}{separator}{block}\n"
    if len(start_matches) != 1 or len(end_matches) != 1:
        raise WorkspaceError("shell rc has incomplete research-workspace markers")

    start = start_matches[0]
    end = end_matches[0]
    if start.start() >= end.start():
        raise WorkspaceError("shell rc has incomplete research-workspace markers")
    return f"{existing[:start.start()]}{block}{existing[end.end():]}"


def _preflight_output(
    path: Path, canonical_required_directories: list[Path]
) -> None:
    if any(
        path == directory or path in directory.parents
        for directory in canonical_required_directories
    ):
        raise WorkspaceError(f"output path conflicts with required directory: {path}")
    path_exists = path.exists() or path.is_symlink()
    if path_exists and path.is_dir():
        raise WorkspaceError(f"output path is a directory: {path}")
    if path_exists and not path.is_file():
        raise WorkspaceError(f"output path is not a regular file: {path}")

    for parent in path.parents:
        if (parent.exists() or parent.is_symlink()) and not parent.is_dir():
            raise WorkspaceError(f"output parent is not a directory: {parent}")


def _read_existing(path: Path) -> str:
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _existing_mode(path: Path) -> int | None:
    if not path.exists():
        return None
    return stat.S_IMODE(path.stat().st_mode)


def _atomic_write_text(
    path: Path,
    contents: str,
    existing_mode: int | None | object = _MODE_UNSET,
) -> None:
    if existing_mode is _MODE_UNSET:
        existing_mode = _existing_mode(path)

    descriptor = None
    temporary_path = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        handle = os.fdopen(
            descriptor, "w", encoding="utf-8", newline=""
        )
        descriptor = None
        with handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        if isinstance(existing_mode, int):
            os.chmod(temporary_path, existing_mode)
        os.replace(temporary_path, path)
    except BaseException:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
        raise


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the minimal AI research workspace layout."
    )
    parser.add_argument("--root", required=True)
    parser.add_argument(
        "--env-file", default="~/.config/research-workspace/env.sh"
    )
    parser.add_argument("--shell-rc")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _run(args: argparse.Namespace) -> None:
    root = _resolved_path(args.root)
    env_file = _resolved_path(args.env_file)
    shell_rc = _resolved_path(args.shell_rc) if args.shell_rc else None
    workspace_paths = _workspace_paths(root)
    required_directories = [path for _, path in workspace_paths]

    for directory in required_directories:
        if (
            directory.exists() or directory.is_symlink()
        ) and not directory.is_dir():
            raise WorkspaceError(
                f"required directory is a file: {directory}"
            )

    canonical_required_directories = [
        directory.resolve() for directory in required_directories
    ]
    _preflight_output(env_file, canonical_required_directories)
    if shell_rc is not None:
        _preflight_output(shell_rc, canonical_required_directories)
        if (
            env_file == shell_rc
            or env_file in shell_rc.parents
            or shell_rc in env_file.parents
            or (
                env_file.exists()
                and shell_rc.exists()
                and env_file.samefile(shell_rc)
            )
        ):
            raise WorkspaceError("env file and shell rc paths conflict")

    desired_env = _env_contents(workspace_paths)
    existing_env = _read_existing(env_file)
    existing_env_mode = _existing_mode(env_file)
    desired_shell = None
    existing_shell = None
    existing_shell_mode = None
    if shell_rc is not None:
        existing_shell = _read_existing(shell_rc)
        existing_shell_mode = _existing_mode(shell_rc)
        desired_shell = _updated_shell_contents(
            existing_shell, _shell_block(env_file)
        )

    for directory in required_directories:
        action = "UNCHANGED" if directory.is_dir() else "CREATE"
        print(f"{action} {directory}")
    print(
        f"{'UNCHANGED' if existing_env == desired_env else 'WRITE'} {env_file}"
    )
    if shell_rc is not None:
        action = "UNCHANGED" if existing_shell == desired_shell else "UPDATE"
        print(f"{action} {shell_rc}")

    if args.dry_run:
        return

    for directory in required_directories:
        directory.mkdir(parents=True, exist_ok=True)
    if existing_env != desired_env:
        env_file.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(env_file, desired_env, existing_env_mode)
    if shell_rc is not None and existing_shell != desired_shell:
        shell_rc.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(shell_rc, desired_shell, existing_shell_mode)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        _run(args)
    except (WorkspaceError, OSError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
