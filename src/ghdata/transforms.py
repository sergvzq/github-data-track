from __future__ import annotations
 
from ghdata.storage import RepoRow


def repo_json_to_row(item: dict) -> RepoRow:
    return RepoRow(
        repo_id=int(item["id"]),
        name = str(item["name"]),
        full_name=str(item["full_name"]),
        private=1 if item.get("private") else 0,
        html_url=str(item["html_url"]),
        stargazers_count=int(item.get("stargazers_count", 0)),
        forks_count=int(item.get("forks_count", 0)),
        open_issues_count=int(item.get("open_issues_count", 0)),
        pushed_at=item.get("pushed_at"),
    )