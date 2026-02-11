from pathlib import Path

from ghdata.storage import RepoRow, Storage


def test_upsert_repos_idempotent(tmp_path):
    db = tmp_path / "test.sqlite"
    store = Storage(Path(db))

    r1 = RepoRow(
        repo_id=1,
        name="a",
        full_name="u/a",
        private=0,
        html_url="x",
        stargazers_count=1,
        forks_count=0,
        open_issues_count=0,
        pushed_at=None,
    )

    assert store.upsert_repos([r1]) == 1
    assert store.upsert_repos([r1]) == 1  # upsert again

    rows = store.list_repos(limit=10)
    assert len(rows) == 1
    assert rows[0][0] == "u/a"
