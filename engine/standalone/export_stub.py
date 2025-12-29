from __future__ import annotations

import argparse
from pathlib import Path

from .contracts import ExportRequest
from .packager_directory import DirectoryPackager


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Standalone export (stage1 stub)")
    parser.add_argument("--output", required=True, help="导出目录（export/）")
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--entrypoint", default="scripts/main.py")
    args = parser.parse_args(argv)

    req = ExportRequest(
        app_id=args.app_id,
        entrypoint_path=args.entrypoint,
        output_dir=Path(args.output).resolve(),
        included_components=["astronverse-system"],
        excluded_components=["astronverse-vision", "astronverse-browser"],
        python_version="3.13.x",
    )
    DirectoryPackager().package(req, deps={})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

