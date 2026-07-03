#!/usr/bin/env python3
"""Collect candidate GitHub issues/PRs for Mentor Loop eval tasks."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_REPOS = [
    "kellyjonbrazil/jc",
    "pallets/click",
    "tqdm/tqdm",
    "dateutil/dateutil",
    "jd/tenacity",
    "date-fns/date-fns",
    "colinhacks/zod",
    "yargs/yargs",
    "sindresorhus/execa",
]


def configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def stage_summary(result: str, detail: str) -> str:
    return f"stage: collect-tasks | result: {result} | detail: {detail}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def split_repo(repo: str) -> tuple[str, str]:
    if "/" not in repo:
        raise ValueError(f"repo must be owner/name: {repo}")
    owner, name = repo.split("/", 1)
    return owner, name


def parse_linked_issue(body: str) -> int | None:
    pattern = r"(?i)\b(?:fix(?:e[sd])?|close[sd]?|resolve[sd]?)\s+#(\d+)"
    match = re.search(pattern, body or "")
    return int(match.group(1)) if match else None


def verification_hint(files: list[dict[str, Any]]) -> str:
    test_files = [item["filename"] for item in files if "test" in item.get("filename", "").lower()]
    if test_files:
        return "Prefer focused verification from touched test file(s): " + ", ".join(test_files[:5])
    return "No touched test file found; inspect PR for focused verification before solidifying."


class GitHubClient:
    def __init__(self, fixture: dict[str, Any] | None, sleep_seconds: float) -> None:
        self.fixture = fixture
        self.sleep_seconds = sleep_seconds
        token = os.environ.get("GH_TOKEN", "")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "mentor-loop-eval-collector",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def get_json(self, url: str) -> Any:
        if self.fixture is not None:
            return self.fixture_get(url)
        request = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def fixture_get(self, url: str) -> Any:
        assert self.fixture is not None
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        if path == "/search/issues":
            q = query.get("q", [""])[0]
            repo_match = re.search(r"repo:([^\s+]+)", q)
            repo = repo_match.group(1) if repo_match else ""
            return {"items": self.fixture.get("search", {}).get(repo, [])}
        match = re.match(r"/repos/([^/]+/[^/]+)/pulls/(\d+)(?:/files)?$", path)
        if match:
            repo, number = match.group(1), match.group(2)
            key = f"{repo}#{number}"
            if path.endswith("/files"):
                return self.fixture.get("files", {}).get(key, [])
            return self.fixture.get("pulls", {}).get(key, {})
        match = re.match(r"/repos/([^/]+/[^/]+)/issues/(\d+)$", path)
        if match:
            repo, number = match.group(1), match.group(2)
            return self.fixture.get("issues", {}).get(f"{repo}#{number}", {})
        raise KeyError(f"fixture missing URL: {url}")


def search_url(repo: str, since: str, per_repo: int) -> str:
    query = f"repo:{repo} is:pr is:merged closed:>{since} fix in:title"
    return "https://api.github.com/search/issues?" + urllib.parse.urlencode({"q": query, "per_page": str(per_repo)})


def collect_repo(client: GitHubClient, repo: str, since: str, per_repo: int) -> list[dict[str, Any]]:
    owner, name = split_repo(repo)
    search = client.get_json(search_url(repo, since, per_repo))
    candidates: list[dict[str, Any]] = []
    for item in search.get("items", []):
        number = int(item["number"])
        pr = client.get_json(f"https://api.github.com/repos/{owner}/{name}/pulls/{number}")
        body = pr.get("body") or item.get("body") or ""
        issue_number = parse_linked_issue(body)
        if not issue_number:
            continue
        files = client.get_json(f"https://api.github.com/repos/{owner}/{name}/pulls/{number}/files")
        total_diff_lines = sum(int(file.get("additions", 0)) + int(file.get("deletions", 0)) for file in files)
        if total_diff_lines >= 100:
            continue
        issue = client.get_json(f"https://api.github.com/repos/{owner}/{name}/issues/{issue_number}")
        has_test_file = any("test" in file.get("filename", "").lower() for file in files)
        candidates.append(
            {
                "repo": repo,
                "language_hint": "Python" if repo in DEFAULT_REPOS[:5] else "JavaScript/TypeScript",
                "issue_url": issue.get("html_url", f"https://github.com/{repo}/issues/{issue_number}"),
                "issue_number": issue_number,
                "issue_title": issue.get("title", ""),
                "issue_body": issue.get("body", ""),
                "fix_pr_url": pr.get("html_url", item.get("html_url", "")),
                "fix_pr_number": number,
                "fix_pr_title": pr.get("title", item.get("title", "")),
                "pr_merged_at": pr.get("merged_at"),
                "merge_commit_sha": pr.get("merge_commit_sha"),
                "base_commit": f"{pr.get('merge_commit_sha')}^1" if pr.get("merge_commit_sha") else "",
                "files_changed": [file.get("filename", "") for file in files],
                "total_diff_lines": total_diff_lines,
                "touches_test_file": has_test_file,
                "verification_hint": verification_hint(files),
            }
        )
        if client.fixture is None:
            time.sleep(client.sleep_seconds)
    return candidates


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Collect GitHub candidate tasks for Mentor Loop evals.")
    parser.add_argument("--repo", action="append", dest="repos", help="Repo in owner/name form. Repeatable.")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "candidates.json")
    parser.add_argument("--since", default="2025-09-01")
    parser.add_argument("--per-repo", type=int, default=10)
    parser.add_argument("--sleep-seconds", type=float, default=7.0)
    parser.add_argument("--fixture", type=Path, help="Mock HTTP fixture for dry verification.")
    args = parser.parse_args()

    fixture = read_json(args.fixture) if args.fixture else None
    client = GitHubClient(fixture=fixture, sleep_seconds=args.sleep_seconds)
    repos = args.repos or DEFAULT_REPOS
    candidates: list[dict[str, Any]] = []
    failures: list[str] = []
    for repo in repos:
        try:
            candidates.extend(collect_repo(client, repo, args.since, args.per_repo))
        except Exception as error:
            failures.append(f"{repo}: {error}")
        if fixture is None:
            time.sleep(args.sleep_seconds)

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "since": args.since,
        "repos": repos,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "failures": failures,
        "notes": [
            "Candidates are raw. Human selection happens in a second pass.",
            "Pre-fix checkout should resolve base_commit after clone, e.g. git rev-parse <merge_commit_sha>^1.",
        ],
    }
    write_json(args.output, payload)
    result = "OK" if candidates else "BLOCKED"
    detail = f"candidates={len(candidates)}; failures={len(failures)}; output={args.output}"
    print(stage_summary(result, detail))
    return 0 if candidates else 1


if __name__ == "__main__":
    raise SystemExit(main())
