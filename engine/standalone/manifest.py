from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from .manifest_schema import MANIFEST_SCHEMA_V1


class ManifestError(Exception):
    def __init__(self, message: str, app_id: str = "unknown") -> None:
        super().__init__(message)
        self.app_id = app_id


@dataclass(frozen=True)
class Manifest:
    data: dict[str, Any]

    @property
    def app_id(self) -> str:
        return str(self.data.get("appId", ""))

    @staticmethod
    def load(path: Path) -> "Manifest":
        app_id_for_log = "unknown"
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise ManifestError(f"manifest 缺失: {path}", app_id=app_id_for_log) from e
        except OSError as e:
            raise ManifestError(f"读取 manifest 失败: {path}: {e}", app_id=app_id_for_log) from e

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ManifestError(f"manifest JSON 解析失败: {path}: {e}", app_id=app_id_for_log) from e

        if isinstance(data, dict) and isinstance(data.get("appId"), str) and data.get("appId"):
            app_id_for_log = data["appId"]

        try:
            jsonschema.validate(instance=data, schema=MANIFEST_SCHEMA_V1)
        except jsonschema.ValidationError as e:
            raise ManifestError(
                f"manifest schema 校验失败: {path}: {e.message}",
                app_id=app_id_for_log,
            ) from e

        return Manifest(data=data)

    def dump(self, path: Path) -> None:
        path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
