from __future__ import annotations

from ghdata.storage import IssueRow, RepoRow


def repo_json_to_row(item: dict) -> RepoRow:
    return RepoRow(
        repo_id=int(item["id"]),
        name=str(item["name"]),
        full_name=str(item["full_name"]),
        private=1 if item.get("private") else 0,
        html_url=str(item["html_url"]),
        stargazers_count=int(item.get("stargazers_count", 0)),
        forks_count=int(item.get("forks_count", 0)),
        open_issues_count=int(item.get("open_issues_count", 0)),
        pushed_at=item.get("pushed_at"),
    )


def issue_json_to_row(repo_id: int, item: dict) -> IssueRow:
    """
    Convert a raw GitHub issue JSON into our normalized IssueRow format.

    reopo_id is passed so we can link issues back to the repo table.
    """

    is_pr = 1 if "pull_request" in item else 0

    user = item.get("user") or {}
    user_login = user.get("login")

    return IssueRow(
        issue_id=int(item["id"]),
        repo_id=int(repo_id),
        number=int(item["number"]),
        title=str(item.get("title") or ""),
        state=str(item.get("state") or "unknown"),
        is_pull_request=is_pr,
        created_at=str(item["created_at"]),
        updated_at=str(item["updated_at"]),
        closed_at=item.get("closed_at"),
        html_url=str(item["html_url"]),
        user_login=str(user_login) if user_login else None,
    )
