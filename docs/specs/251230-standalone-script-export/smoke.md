# Standalone Script Export（阶段一）冒烟说明

本文件用于阶段一（`tasks-stage1.csv`）的最小可重复冒烟，重点验证：

- 形态 A 产物目录契约可生成（空流程也可）
- 产物包含 `manifest.json`
- 启动器（Python stub）可读取/强校验 manifest，缺失/损坏时非 0 退出且日志落盘

## 1. 准备

在仓库根目录执行（Windows / PowerShell）：

1. 确保已安装 `uv`
2. 进入 `engine` 目录（本阶段 stub 代码在 `engine/standalone`）

## 2. 生成空流程产物目录

```powershell
cd engine
uv run python -m standalone.export_stub --output ..\\_out\\standalone_stage1_export --app-id demo-app
```

期望产物目录结构（简写）：

```
_out/standalone_stage1_export/
  runtime/
  packages/
  scripts/
  resources/
  manifest.json
```

## 3. 校验启动器读取 manifest

```powershell
cd engine
uv run python -m standalone.launcher_stub ..\\_out\\standalone_stage1_export
echo $LASTEXITCODE
```

期望：
- 退出码为 `0`

## 4. 缺失 manifest 的失败体验

```powershell
Remove-Item -Force ..\\_out\\standalone_stage1_export\\manifest.json
uv run python -m standalone.launcher_stub ..\\_out\\standalone_stage1_export
echo $LASTEXITCODE
```

期望：
- 退出码非 0
- 日志默认落盘到 `%LOCALAPPDATA%\\AstronRPA\\Logs\\standalone\\{appId}\\{date}.log`（appId 不可解析时会使用 `unknown`）

## 5. 损坏 manifest 的失败体验

```powershell
Set-Content -Path ..\\_out\\standalone_stage1_export\\manifest.json -Value \"not a json\"
uv run python -m standalone.launcher_stub ..\\_out\\standalone_stage1_export
echo $LASTEXITCODE
```

期望：
- 退出码非 0
- 日志包含“解析失败/校验失败”的原因描述

