import argparse
import os
import sys

from dotenv import load_dotenv

from cliper import Cliper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update Notion Web Clip entries with tags and classification via Cliper"
    )
    parser.add_argument(
        "database_url",
        nargs="?",
        default=None,
        help=(
            "Notion database query API endpoint; if omitted, reads NOTION_DATABASE_URL "
            "from environment"
        ),
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to the environment variable file loaded before execution (default: .env)",
    )
    parser.add_argument(
        "--page-id",
        default=None,
        help="Notion page ID to update; if omitted, reads NOTION_PAGE_ID",
    )
    parser.add_argument(
        "--start-cursor",
        default=None,
        help="Optional Notion pagination cursor if you want to resume from a previous run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.env_file:
        load_dotenv(args.env_file)
    else:
        load_dotenv()

    cliper = Cliper(env_file=args.env_file)

    page_id = args.page_id or os.environ.get("NOTION_PAGE_ID")
    if page_id:
        try:
            cliper.update_single_clip(page_id)
        except Exception as exc:
            print(f"处理失败: {exc}")
            return 1
        return 0

    database_url = args.database_url or os.environ.get("NOTION_DATABASE_URL")
    if not database_url:
        print("未提供 page_id 或 database_url，且相关环境变量未设置", file=sys.stderr)
        return 2

    try:
        cliper.update_web_clips(database_url, args.start_cursor)
    except Exception as exc:
        print(f"处理失败: {exc}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
