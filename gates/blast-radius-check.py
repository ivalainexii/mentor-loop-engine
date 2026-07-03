from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def normalize_path(path: str) -> str:
    cleaned = path.strip().strip("`").strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def _bullet_value(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("-"):
        return None
    value = stripped[1:].strip()
    return normalize_path(value) if value else None


def _looks_like_path(value: str) -> bool:
    return "/" in value or "\\" in value or "." in Path(value).name


def extract_blast_radius(brief_text: str) -> tuple[list[str], list[str]]:
    allowed: list[str] = []
    do_not_touch: list[str] = []
    mode: str | None = None
    in_blast_radius = False

    for raw_line in brief_text.splitlines():
        stripped = raw_line.strip()
        lowered = stripped.lower()
        if stripped.startswith("## "):
            in_blast_radius = lowered == "## blast radius"
            mode = None
            continue
        if not in_blast_radius:
            continue
        if lowered.startswith("likely touched files"):
            mode = "allowed"
            continue
        if lowered.startswith("do not touch"):
            mode = "do_not_touch"
            continue
        if lowered.endswith(":") and not stripped.startswith("-"):
            mode = None
            continue
        value = _bullet_value(raw_line)
        if not value or not _looks_like_path(value):
            continue
        if mode == "allowed":
            allowed.append(value)
        elif mode == "do_not_touch":
            do_not_touch.append(value)

    return allowed, do_not_touch


def check_blast_radius(brief_text: str, changed_files: list[str]) -> dict[str, object]:
    allowed, do_not_touch = extract_blast_radius(brief_text)
    changed = [normalize_path(path) for path in changed_files]
    outside = [path for path in changed if path not in set(allowed)]
    violations = [path for path in changed if path in set(do_not_touch)]
    return {
        "ok": bool(allowed) and not outside and not violations,
        "allowed_files": allowed,
        "do_not_touch": do_not_touch,
        "outside_blast_radius": outside,
        "do_not_touch_violations": violations,
    }


def _path_from_status_line(line: str) -> str | None:
    if not line:
        return None
    path = line[3:] if len(line) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return normalize_path(path) if path else None


def git_changed_files() -> list[str]:
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip().splitlines()[0] if error.stderr.strip() else "not inside a git worktree"
        raise RuntimeError(f"could not read git diff: {message}") from error

    commands = [["git", "status", "--porcelain"]]
    files: list[str] = []
    seen: set[str] = set()
    for command in commands:
        try:
            completed = subprocess.run(command, check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as error:
            message = error.stderr.strip() or error.stdout.strip() or str(error)
            raise RuntimeError(f"could not read git diff: {message}") from error
        for line in completed.stdout.splitlines():
            path = _path_from_status_line(line)
            if path and path not in seen:
                seen.add(path)
                files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Check changed files against a Mentor Brief Blast Radius.")
    parser.add_argument("--brief", required=True)
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        help="Changed file path. Repeat for multiple files. If omitted, reads git status --porcelain.",
    )
    args = parser.parse_args()

    brief_text = Path(args.brief).read_text(encoding="utf-8-sig")
    try:
        changed_files = args.changed or git_changed_files()
    except RuntimeError as error:
        print(f"changed_files: (unavailable)")
        print(f"result: BLOCKED")
        print(str(error))
        return 1
    result = check_blast_radius(brief_text, changed_files)

    print(f"changed_files: {', '.join(changed_files) or '(none)'}")
    print(f"allowed_files: {', '.join(result['allowed_files']) or '(none)'}")
    if result["outside_blast_radius"]:
        print("outside_blast_radius:")
        for path in result["outside_blast_radius"]:
            print(f"- {path}")
    if result["do_not_touch_violations"]:
        print("do_not_touch_violations:")
        for path in result["do_not_touch_violations"]:
            print(f"- {path}")
    print("result: OK" if result["ok"] else "result: BLOCKED")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
