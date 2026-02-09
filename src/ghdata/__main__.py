import argparse

from pathlib import Path

from ghdata.config import load_settings
from ghdata.github_client import GitHubClient, GitHubError
from ghdata.storage import Storage
from ghdata.transforms import repo_json_to_row


def main() -> int:
    parser = argparse.ArgumentParser(prog="ghdata")
    parser.add_argument("--ping", action="store_true", help="Sanity check the CLI")
    parser.add_argument("--me", action="store_true", help="Show the authenticated GitHub user")
    parser.add_argument("--rate-limit", action="store_true", help="Show rate limit status")
    parser.add_argument("--sync-repos", action="store_true", help="Fetch all repos and store in SQLite")
    parser.add_argument("--list-repos", action="store_true", help="List top repos from SQLite")
    parser.add_argument("--db", default="ghdata.sqlite", help="SQLite DB path")
    args = parser.parse_args()

    if args.ping:
        print("pong")
        return 0

    settings = load_settings()
    client = GitHubClient(token=settings.github_token)

    try:
        db_path = Path(args.db)
        store = Storage(db_path)

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
        

        parser.print_help()
        return 0

    except GitHubError as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
