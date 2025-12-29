from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True)
class ExportPaths:
    """形态 A（自包含目录）产物目录契约。

    注意：PRD 6.5.1 里推荐结构是 `export/runtime|packages|scripts|resources|manifest.json`。
    本项目 stage1 任务描述里也提到 `runtime/packages/scripts/resources/manifest.json`。
    因此这里采用与 PRD 一致的顶层结构：

    - export_root/
      - runtime/
      - packages/
      - scripts/
      - resources/
      - manifest.json
    """

    export_root: Path

    @property
    def runtime_dir(self) -> Path:
        return self.export_root / "runtime"

    @property
    def packages_dir(self) -> Path:
        return self.export_root / "packages"

    @property
    def scripts_dir(self) -> Path:
        return self.export_root / "scripts"

    @property
    def resources_dir(self) -> Path:
        return self.export_root / "resources"

    @property
    def manifest_path(self) -> Path:
        return self.export_root / "manifest.json"


@dataclass(frozen=True)
class ExportRequest:
    app_id: str
    entrypoint_path: str
    output_dir: Path
    included_components: Sequence[str]
    excluded_components: Sequence[str]
    python_version: str


@dataclass(frozen=True)
class ExportResult:
    export_root: Path
    manifest_path: Path


class IDependencyAnalyzer(Protocol):
    def analyze(self, request: ExportRequest) -> dict:
        """返回用于打包与写入 manifest 的依赖信息（最小实现可返回空 dict）。"""


class IPackager(Protocol):
    def package(self, request: ExportRequest, deps: dict) -> ExportResult:
        """根据 request + deps 生成产物并返回路径。"""


class ILauncher(Protocol):
    def launch(self, base_dir: Path, args: Sequence[str] | None = None) -> int:
        """以产物根目录为 BASE_DIR 启动执行，返回退出码。"""

