from __future__ import annotations

import argparse
import ast
import re
import subprocess
from pathlib import Path


MIN_API_VERSION: dict[str, tuple[int, int]] = {
    "removeprefix": (3, 9),
    "removesuffix": (3, 9),
}


def normalize_path(path: str) -> str:
    cleaned = path.strip().strip("`").strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def parse_version(value: str) -> tuple[int, int] | None:
    match = re.search(r"3\.(\d+)", value)
    if not match:
        return None
    return (3, int(match.group(1)))


def parse_python_requires(text: str) -> tuple[int, int] | None:
    patterns = [
        r"python_requires\s*=\s*['\"]([^'\"]+)['\"]",
        r"requires-python\s*=\s*['\"]([^'\"]+)['\"]",
        r"python_requires\s*=\s*([^\n#]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            version = parse_version(match.group(1))
            if version:
                return version
    return None


def find_python_requires(root: Path) -> tuple[tuple[int, int] | None, Path | None]:
    for name in ("pyproject.toml", "setup.py", "setup.cfg"):
        path = root / name
        if not path.exists():
            continue
        version = parse_python_requires(path.read_text(encoding="utf-8-sig", errors="ignore"))
        if version:
            return version, path
    return None, None


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
        raise RuntimeError(f"could not read git status: {message}") from error

    try:
        completed = subprocess.run(["git", "status", "--porcelain"], check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip() or str(error)
        raise RuntimeError(f"could not read git status: {message}") from error

    files: list[str] = []
    seen: set[str] = set()
    for line in completed.stdout.splitlines():
        path = _path_from_status_line(line)
        if path and path not in seen:
            seen.add(path)
            files.append(path)
    return files


def find_api_uses(path: Path) -> list[dict[str, object]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except SyntaxError as error:
        return [
            {
                "path": normalize_path(str(path)),
                "api": "syntax_error",
                "required_version": None,
                "line": error.lineno or 0,
            }
        ]

    uses: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in MIN_API_VERSION:
            uses.append(
                {
                    "path": normalize_path(str(path)),
                    "api": node.attr,
                    "required_version": MIN_API_VERSION[node.attr],
                    "line": getattr(node, "lineno", 0),
                }
            )
    return uses


def check_runtime_floor(root: Path, python_requires: tuple[int, int] | None, changed_files: list[str]) -> dict[str, object]:
    python_files = [normalize_path(path) for path in changed_files if normalize_path(path).endswith(".py")]
    findings: list[dict[str, object]] = []
    for relative in python_files:
        path = root / relative
        if path.exists():
            findings.extend(find_api_uses(path))

    blocked: list[dict[str, object]] = []
    for finding in findings:
        required = finding["required_version"]
        if required is None:
            blocked.append(finding)
        elif python_requires is None or required > python_requires:
            blocked.append(finding)

    return {
        "ok": not blocked,
        "python_requires": python_requires,
        "python_files": python_files,
        "findings": findings,
        "blocked": blocked,
    }


def format_version(version: tuple[int, int] | None) -> str:
    if version is None:
        return "(unknown)"
    return f"{version[0]}.{version[1]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check changed Python files against the declared Python runtime floor.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--python-requires", help="Override detected runtime floor, e.g. '>=3.6'.")
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        help="Changed file path. Repeat for multiple files. If omitted, reads git status --porcelain.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if args.python_requires:
        python_requires = parse_version(args.python_requires)
        source = "command line"
    else:
        python_requires, source_path = find_python_requires(root)
        source = str(source_path) if source_path else "(not found)"

    try:
        changed_files = args.changed or git_changed_files()
    except RuntimeError as error:
        print("changed_files: (unavailable)")
        print("result: BLOCKED")
        print(str(error))
        return 1

    result = check_runtime_floor(root, python_requires, changed_files)

    print(f"python_requires: {format_version(python_requires)}")
    print(f"python_requires_source: {source}")
    print(f"changed_python_files: {', '.join(result['python_files']) or '(none)'}")
    if result["blocked"]:
        print("runtime_floor_violations:")
        for finding in result["blocked"]:
            required = finding["required_version"]
            if finding["api"] == "syntax_error":
                print(f"- {finding['path']}:{finding['line']} cannot be parsed")
            else:
                print(
                    f"- {finding['path']}:{finding['line']} uses {finding['api']} "
                    f"(requires Python {format_version(required)})"
                )
    print("result: OK" if result["ok"] else "result: BLOCKED")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
