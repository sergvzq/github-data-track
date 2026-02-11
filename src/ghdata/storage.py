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
