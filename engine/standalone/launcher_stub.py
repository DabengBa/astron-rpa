from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Sequence

from .exit_codes import ExitCode
from .logging_utils import default_log_path, ensure_parent_dir
from .manifest import Manifest, ManifestError


class LauncherStub:
    """阶段一启动器最小实现（Python 版）。

    注意：PRD 里启动器是 `launcher.exe`，这里先提供 Python stub 用于契约验证与回归。
    """

    def launch(self, base_dir: Path, args: Sequence[str] | None = None) -> int:
        args = list(args or [])
        manifest_path = base_dir / "manifest.json"
        log_path = default_log_path(app_id="unknown", base_dir=base_dir)
        try:
            manifest = Manifest.load(manifest_path)
            log_path = default_log_path(app_id=manifest.app_id, base_dir=base_dir)

            # 阶段一：只验证能读取 manifest，并不真正执行脚本
            return int(ExitCode.OK)
        except ManifestError as e:
            log_path = default_log_path(app_id=getattr(e, "app_id", "unknown"), base_dir=base_dir)
            ensure_parent_dir(log_path)
            log_path.write_text(str(e) + "\n", encoding="utf-8")
            return int(ExitCode.MANIFEST_INVALID)
        except FileNotFoundError:
            ensure_parent_dir(log_path)
            log_path.write_text(f"manifest 缺失: {manifest_path}\n", encoding="utf-8")
            return int(ExitCode.MANIFEST_MISSING)
        except Exception as e:
            ensure_parent_dir(log_path)
            log_path.write_text(f"internal error: {e}\n{traceback.format_exc()}\n", encoding="utf-8")
            return int(ExitCode.INTERNAL_ERROR)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    base_dir = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    return LauncherStub().launch(base_dir=base_dir, args=argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
