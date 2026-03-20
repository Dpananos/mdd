import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="mdd - Markdown document reviewer with AI-powered editing"
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the markdown file to review",
    )
    parser.add_argument(
        "--session",
        "-s",
        help="Claude Code session ID or name to resume",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    from mdd.app import MddApp

    app = MddApp(file_path=args.file.resolve(), session=args.session)
    app.run()


if __name__ == "__main__":
    main()
