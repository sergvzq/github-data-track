from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ghdata.storage import Storage


def write_markdown_report(store: Storage, out_path: Path) -> None:
    """
    Generate a simple Markdown report from DB metrics.
    This is intentionally basics for now-cleam output matters more than fancy formatting.

    :param store: Description
    :type store: Storage
    :param out_path: Description
    :type out_path: Path
    """

    metrics = store.metrics()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    lines: list[str] = []
    lines.append(f"# GitHub Activity Report")
    lines.append("")
    lines.append(f"Generated: **{now}**")
    lines.append("")
    lines.append(f"## Overview")
    lines.append("")
    lines.append(f"- Total items in issues table: **{metrics['total']}**")
    lines.append(
        f"- Issues: **open {metrics['issues_open']}**, **closed {metrics['issues_closed']}**"
    )
    lines.append(f"- PRs: **open {metrics['prs_open']}**, **closed {metrics['prs_closed']}**")
    lines.append("")
    lines.append(f"## Top Repos by Open Issues")
    lines.append("")
    lines.append(f"| Repo Full Name | Open Issues |")
    lines.append(f"| --- | ---: |")
    for full_name, open_issues in metrics["top_open_issues"]:
        lines.append(f"| {full_name} | {open_issues} |")

    out_path.write_text("\n".join(lines), encoding="utf-8")
