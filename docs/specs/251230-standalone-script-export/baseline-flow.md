# 阶段一基准示例流程（无 vision/browser）

本示例用于阶段一/后续阶段的持续回归，要求 **不依赖**：

- `astronverse-vision*`（OpenCV）
- `astronverse-browser*`（浏览器自动化）

目标是覆盖至少一条“能跑通的基础能力链路”，并且具有可重复的冒烟步骤。

## A. 示例脚本（Python）

建议后续把导出得到的 `scripts/main.py` 逐步替换为真实流程编译产物。阶段一先给出最小可执行逻辑：

- 写入一个文本文件（system 能力替代）
- 读取并打印内容

示例 `scripts/main.py`（仅说明用途，阶段一的导出 stub 不会自动生成该文件）：

```python
from pathlib import Path

def main():
    p = Path("resources") / "hello.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("hello standalone\\n", encoding="utf-8")
    print(p.read_text(encoding="utf-8").strip())

if __name__ == "__main__":
    main()
```

## B. 冒烟步骤

1. 使用 `engine/standalone` 的导出 stub 生成形态 A 目录：

```powershell
python -m engine.standalone.export_stub --output .\\_out\\baseline_export --app-id baseline-app
```

2. 在产物 `scripts/` 中放入 `main.py`（用上面的示例脚本）。

3. 使用启动器 stub 校验 manifest（阶段一只做校验，不执行脚本）：

```powershell
python -m engine.standalone.launcher_stub .\\_out\\baseline_export
echo $LASTEXITCODE
```

期望：`$LASTEXITCODE` 为 `0`。

> 注：后续阶段（形态 A MVP）会把启动器替换为真正的 `launcher.exe` 并执行 `scripts/main.py`，此文档可复用为回归入口。

