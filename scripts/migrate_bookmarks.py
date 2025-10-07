from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.bookmarks_migrator import BookmarksMigrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate legacy bookmark data into the consolidated bookmarks.json schema.",
    )
    default_app_dir = PROJECT_ROOT / "app"
    parser.add_argument(
        "--app-dir",
        type=Path,
        default=default_app_dir,
        help="Path to the application directory containing defaults/ and configs/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without writing any files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    migrator = BookmarksMigrator(app_root=args.app_dir, dry_run=args.dry_run)
    report = migrator.migrate()

    changes = False
    for directory_report in report.directories:
        status = (
            "created"
            if directory_report.created
            else "updated" if directory_report.updated else "skipped"
        )
        reason = f" ({directory_report.reason})" if directory_report.reason else ""
        logging.info(
            "%s: %s -> %s%s",
            directory_report.scope,
            directory_report.old_bookmarks,
            directory_report.new_bookmarks,
            reason,
        )
        if directory_report.created or directory_report.updated:
            changes = True

    if args.dry_run:
        logging.info("Dry run complete. No files were modified.")
        return 0

    if not changes:
        logging.info("Bookmarks already at desired schema. No updates applied.")
    else:
        logging.info("Bookmarks migration completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
