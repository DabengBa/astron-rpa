from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path


def default_log_path(app_id: str, base_dir: Path | None = None) -> Path:
    """默认日志落盘路径（参考 PRD 3.1 标准 5）。"""

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        root = Path(local_appdata) / "AstronRPA" / "Logs" / "standalone" / app_id
    elif base_dir is not None:
        root = base_dir / "logs" / app_id
    else:
        root = Path.cwd() / "logs" / app_id

    date_str = _dt.date.today().isoformat()
    return root / f"{date_str}.log"


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

