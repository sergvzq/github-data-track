from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RepoRow:
    repo_id: int
    name: str
    full_name: str
    private: int  # 0/1
    html_url: str
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    pushed_at: str | None


class Storage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS repos (
                    repo_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    private INTEGER NOT NULL,
                    html_url TEXT NOT NULL,
                    stargazers_count INTEGER NOT NULL,
                    forks_count INTEGER NOT NULL,
                    open_issues_count INTEGER NOT NULL,
                    pushed_at TEXT
                );
                """
            )
            # Issues table:
            # - issue_id is globally unique across GitHub, so it can be the primary key.
            # - repo_id links the issue back to the repo table.
            # - pull_request is 0/1 because the Issues API also returns PRs.
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS issues (
                    issue_id INTEGER PRIMARY KEY,
                    repo_id INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    state TEXT NOT NULL,             -- "open" or "closed"
                    is_pull_request INTEGER NOT NULL, -- 0/1
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    html_url TEXT NOT NULL,
                    user_login TEXT,
                    FOREIGN KEY (repo_id) REFERENCES repos(repo_id)
                );
                """
            )

            # Helpful index for querying by repo and state
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_issues_repo_state ON issues(repo_id, state);"
            )

    def upsert_repos(self, rows: Iterable[RepoRow]) -> int:
        rows_list = list(rows)
        if not rows_list:
            return 0

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO repos (
                    repo_id, name, full_name, private, html_url,
                    stargazers_count, forks_count, open_issues_count, pushed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repo_id) DO UPDATE SET
                    name=excluded.name,
                    full_name=excluded.full_name,
                    private=excluded.private,
                    html_url=excluded.html_url,
                    stargazers_count=excluded.stargazers_count,
                    forks_count=excluded.forks_count,
                    open_issues_count=excluded.open_issues_count,
                    pushed_at=excluded.pushed_at
                ;
                """,
                [
                    (
                        r.repo_id,
                        r.name,
                        r.full_name,
                        r.private,
                        r.html_url,
                        r.stargazers_count,
                        r.forks_count,
                        r.open_issues_count,
                        r.pushed_at,
                    )
                    for r in rows_list
                ],
            )
        return len(rows_list)

    def upsert_issues(self, rows: Iterable[IssueRow]) -> int:
        """
        Insert issues; if an issue already exists (same issue_id), update it.
        This makes the sync safe to re-run.
        """
        rows_list = list(rows)
        if not rows_list:
            return 0

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO issues(
                    issue_id, repo_id, number, title, state, is_pull_request,
                    created_at, closed_at, html_url, user_login
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(issue_id) DO UPDATE SET
                    repo_id=excluded.repo_id,
                    number=excluded.number,
                    title=excluded.title,
                    state=excluded.state,
                    is_pull_request=excluded.is_pull_request,
                    created_at=excluded.created_at,
                    closed_at=excluded.closed_at,
                    html_url=excluded.html_url,
                    user_login=excluded.user_login
                ;
                """,
                [
                    (
                        r.issue_id,
                        r.repo_id,
                        r.number,
                        r.title,
                        r.state,
                        r.is_pull_request,
                        r.created_at,
                        r.closed_at,
                        r.html_url,
                        r.user_login,
                    )
                    for r in rows_list
                ],
            )
        return len(rows_list)

    def metrics(self) -> dict[str, int]:
        """
        Return some basic metrics about the stored data, e.g. number of repos and issues.
        """
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
            open_count = conn.execute(
                "SELECT COUNT (*) FROM issues WHERE state='open';"
            ).fetchone()[0]
            closed_count = conn.execute(
                "SELECT COUNT (*) FROM issues WHERE state='closed';"
            ).fetchone()[0]

            top_open = conn.execute(
                """
                SELECT r.full_name, COUNT(*) AS open_issues
                FROM issues i
                JOIN repos r ON r.repo_id = i.repo_id
                WHERE i.state = 'open'
                GROUP BY r.full_name
                ORDER BY open_issues DESC
                LIMIT 5;
                """
            ).fetchall()

        return {
            "total": total,
            "open": open_count,
            "closed": closed_count,
            "top_open": top_open,
        }

    def list_repos(self, limit: int = 10) -> list[tuple[str, int, int, str | None]]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT full_name, stargazers_count, forks_count, pushed_at
                FROM repos
                ORDER BY stargazers_count DESC, forks_count DESC
                LIMIT ?
                """,
                (limit,),
            )
            return list(cur.fetchall())


@dataclass(frozen=True)
class IssueRow:
    issue_id: int
    repo_id: int
    number: int
    title: str
    state: str  # "open" or "closed"
    is_pull_request: int  # 0/1
    created_at: str
    closed_at: str | None
    html_url: str
    user_login: str | None
