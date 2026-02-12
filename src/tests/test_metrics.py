# from pathlib import Path

# from ghdata.storage import IssueRow, RepoRow, Storage


# def test_metrics_counts(tmp_path):
#     db = tmp_path / "m.sqlite"
#     store = Storage(Path(db))

#     # Insert one repo
#     store.upsert_repos(
#         [
#             RepoRow(
#                 repo_id=1,
#                 name="a",
#                 full_name="u/a",
#                 private=0,
#                 html_url="x",
#                 stargazers_count=0,
#                 forks_count=0,
#                 open_issues_count=0,
#                 pushed_at=None,
#             )
#         ]
#     )

#     # Insert issues: 2 open, 1 closed
#     store.upsert_issues(
#         [
#             IssueRow(101, 1, 1, "t1", "open", 0, "2020-01-01T00:00:00Z", None, "url1", "bob"),
#             IssueRow(102, 1, 2, "t2", "open", 1, "2020-01-01T00:00:00Z", None, "url2", "bob"),
#             IssueRow(
#                 103,
#                 1,
#                 3,
#                 "t3",
#                 "closed",
#                 0,
#                 "2020-01-01T00:00:00Z",
#                 "2020-01-02T00:00:00Z",
#                 "url3",
#                 "ann",
#             ),
#         ]
#     )

#     m = store.metrics()
#     assert m["total"] == 3
#     assert m["open"] == 2
#     assert m["closed"] == 1
#     assert m["top_open"][0][0] == "u/a"

from pathlib import Path

from ghdata.storage import IssueRow, RepoRow, Storage


def test_metrics_counts(tmp_path):
    db = tmp_path / "m.sqlite"
    store = Storage(Path(db))

    # Insert one repo
    store.upsert_repos(
        [
            RepoRow(
                repo_id=1,
                name="a",
                full_name="u/a",
                private=0,
                html_url="x",
                stargazers_count=0,
                forks_count=0,
                open_issues_count=0,
                pushed_at=None,
            )
        ]
    )

    # Insert issues: 2 open, 1 closed
    store.upsert_issues(
        [
            IssueRow(101, 1, 1, "t1", "open", 0, "2020-01-01T00:00:00Z", None,
                     "url1", "bob"),
            IssueRow(102, 1, 2, "t2", "open", 1, "2020-01-01T00:00:00Z", None,
                     "url2", "bob"),
            IssueRow(103, 1, 3, "t3", "closed", 0, "2020-01-01T00:00:00Z",
                        "2020-01-02T00:00:00Z", "url3", "ann")
        ]
    )

    m = store.metrics()
    assert m["total"] == 3
    assert m["open"] == 2
    assert m["closed"] == 1
    assert m["top_open"][0][0] == "u/a"
    