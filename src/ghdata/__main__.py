import argparse

from pathlib import Path

from ghdata.config import load_settings
from ghdata.github_client import GitHubClient, GitHubError
from ghdata.storage import Storage
from ghdata.transforms import repo_json_to_row, issue_json_to_row


def main() -> int:
    parser = argparse.ArgumentParser(prog="ghdata")
    parser.add_argument("--ping", action="store_true", help="Sanity check the CLI")
    parser.add_argument("--me", action="store_true", help="Show the authenticated GitHub user")
    parser.add_argument("--rate-limit", action="store_true", help="Show rate limit status")
    parser.add_argument(
        "--sync-repos", action="store_true", help="Fetch all repos and store in SQLite"
    )
    parser.add_argument("--list-repos", action="store_true", help="List top repos from SQLite")
    parser.add_argument("--db", default="ghdata.sqlite", help="SQLite DB path")

    parser.add_argument(
        "--sync-issues", action="store_true", help="Fetch issues for each repo and store in SQLite"
    )
    parser.add_argument("--metrics", action="store_true", help="Show basic metrics from SQLite")
    parser.add_argument(
        "--issue-limit-repos",
        type=int,
        default=10,
        help="How many repos to sync issues for (safety)",
    )

    args = parser.parse_args()

    if args.ping:
        print("pong")
        return 0

    settings = load_settings()
    client = GitHubClient(token=settings.github_token)

    try:
        db_path = Path(args.db)
        store = Storage(db_path)

        if args.sync_issues:
            # Safety default: syncing issues for every repo can be slow if you have many.
            # We'll default to top N repos by stars already storeed in DB

            repos = store.list_repos(limit=args.issue_limit_repos)

            # store.list_repos returns tuples; we need repo full_name.
            # We'll re-query repo_id + full_name directly for accuracy.
            with store._connect() as conn:  # ok for now, later we can make a method
                repo_rows = conn.execute(
                    """
                    SELECT repo_id, full_name
                    FROM repos
                    ORDER BY stargazers_count DESC, forks_count DESC
                    LIMIT ?;
                    """,
                    (args.issue_limit_repos,),
                ).fetchall()

            total_synced = 0

            for repo_id, full_name in repo_rows:
                # full_name looks like "owner repo"
                owner, repo = full_name.split("/", 1)

                items = client.iter_repo_issues(owner=owner, repo=repo, per_page=100)
                rows = [issue_json_to_row(repo_id=repo_id, item=1) for i in items]

                total_synced += store.upsert_issues(rows)
                print(f"Synced {len(rows)} issues for {full_name}")

            print(f"Total synced issues: {total_synced}")
            return 0

        if args.me:
            data = client.get_viewer()
            print(data.get("login", "<no login field>"))
            return 0

        if args.rate_limit:
            data = client.get_rate_limit()
            core = data.get("rate", {})
            remaining = core.get("remaining")
            limit = core.get("limit")
            print(f"core remaining: {remaining}/{limit}")
            return 0

        if args.sync_repos:
            items = client.iter_user_repos(per_page=100)
            rows = [repo_json_to_row(i) for i in items]
            n = store.upsert_repos(rows)
            print(f"synced repos: {n}")
            return 0

        if args.list_repos:
            rows = store.list_repos(limit=10)
            for full_name, stars, forks, pushed_at in rows:
                print(f"{full_name} | ⭐ {stars} | forks {forks} | {pushed_at}")
            return 0

        if args.metrics:
            m = store.metrics()
            print(f"Total issues: {m['total']}")
            print(f"open: {m['open']} | closed: {m['closed']}")
            print("top repos by open issues:")
            for full_name, open_issues in m["top_open"]:
                print(f"{full_name}: {open_issues}")
            return 0

        parser.print_help()
        return 0

    except GitHubError as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
