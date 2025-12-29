from __future__ import annotations

import datetime as _dt
import hashlib
from pathlib import Path
from typing import Any

from .contracts import ExportPaths, ExportRequest, ExportResult, IPackager
from .manifest import Manifest


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DirectoryPackager(IPackager):
    """形态 A（自包含目录）的最小实现：生成空目录结构 + manifest.json。"""

    def package(self, request: ExportRequest, deps: dict[str, Any]) -> ExportResult:
        export_paths = ExportPaths(export_root=request.output_dir)
        export_paths.export_root.mkdir(parents=True, exist_ok=True)
        export_paths.runtime_dir.mkdir(parents=True, exist_ok=True)
        export_paths.packages_dir.mkdir(parents=True, exist_ok=True)
        export_paths.scripts_dir.mkdir(parents=True, exist_ok=True)
        export_paths.resources_dir.mkdir(parents=True, exist_ok=True)

        created_at = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        build_id = _sha256_text(
            "|".join(
                [
                    "schema:1.0",
                    f"appId:{request.app_id}",
                    f"entry:{request.entrypoint_path}",
                    f"py:{request.python_version}",
                    "components:" + ",".join(sorted(request.included_components)),
                ]
            )
        )[:16]

        manifest_data: dict[str, Any] = {
            "schemaVersion": "1.0",
            "appId": request.app_id,
            "buildId": build_id,
            "createdAt": created_at,
            "python": {"version": request.python_version, "distribution": "embedded", "arch": "x64"},
            "entrypoint": {"module": "main", "path": request.entrypoint_path},
            "paths": {
                "runtimeDir": "runtime",
                "packagesDir": "packages",
                "scriptsDir": "scripts",
                "resourcesDir": "resources",
            },
            "astronverse": {
                "baselineVersion": "unknown",
                "includedComponents": list(request.included_components),
                "excludedComponents": list(request.excluded_components),
            },
            "pythonPackages": {
                "locked": bool(deps.get("locked", True)),
                "requirements": list(deps.get("requirements", ["placeholder-package>=0"])),
                "wheelFiles": list(deps.get("wheelFiles", [])),
            },
            "blockedImports": list(deps.get("blockedImports", [])),
            "nativeArtifacts": deps.get("nativeArtifacts", {}),
            "runtimeOptions": deps.get("runtimeOptions", {"logLevel": "INFO"}),
        }

        Manifest(data=manifest_data).dump(export_paths.manifest_path)
        return ExportResult(export_root=export_paths.export_root, manifest_path=export_paths.manifest_path)

