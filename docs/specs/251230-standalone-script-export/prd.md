# Astron RPA 独立脚本打包功能 - 产品需求文档 (PRD)

> **一句话总结**: 实现将 RPA 流程导出为可在无 Python 环境下独立运行的可执行脚本，采用嵌入式 Python + 自定义启动器方案。

## 1. 目标与价值 (Goal & Value)

### 1.1 要解决的问题 (Problem)

当前 Astron RPA 平台导出的 Python 脚本需要在目标机器上预先安装 Python 3.13 环境及所有依赖包，这带来了以下问题：

- **部署复杂度高**: 用户需要手动配置 Python 环境，安装大量依赖包
- **版本冲突风险**: 不同脚本可能需要不同版本的依赖，导致环境冲突
- **技术门槛高**: 非技术用户难以正确配置运行环境
- **分发困难**: 需要分发源代码，可能泄露业务逻辑
- **离线场景限制**: 无法在没有网络的环境中安装依赖

### 1.2 期望的结果 (Goal)

- **一键运行**: 导出的脚本可在任何 Windows 机器上直接运行，无需预先安装 Python
- **便携式分发**: 单个可执行文件或自包含目录，便于分发和部署
- **离线支持**: 完全离线运行，不依赖网络下载依赖
- **体积优化**: 通过排除不需要的依赖（如 OpenCV、selenium 等），控制打包体积
- **高性能启动**: 优化的启动流程，快速响应用户执行请求

## 2. 功能范围 (Scope)

### 2.1 核心功能

#### 功能点 1: 嵌入式 Python 运行时集成
- 将 Python 3.13 嵌入式运行时打包到导出目录中
- 支持动态加载 Python 解释器和标准库
- 自动配置 Python 环境变量和路径

#### 功能点 2: 依赖包智能打包
- 自动分析脚本依赖的 astronverse 组件
- 只打包实际使用的组件和第三方库
- 排除不需要的组件（astronverse-vision、astronverse-browser 等）
- 处理原生依赖（.dll、.pyd 文件）

#### 功能点 3: 自定义启动器
- 实现轻量级启动器，负责初始化 Python 环境
- 解压运行时和依赖到临时目录
- 设置正确的 Python 路径和模块搜索路径
- 执行用户脚本并清理临时资源

#### 功能点 4: 脚本导出流程
- 在现有的代码生成流程中增加打包选项
- 支持导出为单个可执行文件或自包含目录（见 5.2 分发形态）
- 生成启动脚本（Windows 批处理或可执行文件）
- 包含必要的配置文件和资源

#### 功能点 5: 错误处理和日志
- 捕获并友好显示 Python 执行错误
- 提供详细的日志记录功能
- 支持日志文件输出和调试模式

### 2.2 非功能需求

#### 兼容性要求
- 支持 Windows 10/11 x64 系统
- 不需要管理员权限
- 支持离线运行

#### 可维护性要求
- 遵循 SOLID 原则设计启动器架构
- 模块化设计，便于扩展和测试
- 清晰的代码结构和文档

## 3. 验收标准 (Acceptance Criteria)

### 3.1 功能验收标准

- **标准 1**: 当用户选择"导出独立脚本"选项时，系统应自动分析脚本依赖并打包所有必要的组件和运行时。
  - 验收点：产物中必须包含 `manifest.json`，且字段 `python/version`、`entrypoint/path`、`astronverse/includedComponents`、`pythonPackages/requirements` 不为空。
  - 验收点：导出过程生成“依赖解析报告”，可定位每个依赖的来源与过滤原因。

- **标准 2**: 当在未安装 Python 的 Windows 机器上运行导出的脚本时，应能正常启动并执行，无需任何额外配置。
  - 验收点：目标机不安装 Python（无 `python.exe`），双击 `launcher.exe` 可运行并完成示例流程。
  - 验收点：启动器不得依赖管理员权限写入 Program Files/系统目录。

- **标准 3**: 当脚本使用 astronverse-system、astronverse-excel 等核心组件时，应能正常调用相关功能。
  - 验收点：提供至少 3 个覆盖核心能力的示例流程（system/excel/network 或 database 任一），在 Win10/Win11 均可执行通过。

- **标准 4**: 当脚本尝试使用 astronverse-vision 或 astronverse-browser 等排除的组件时，应给出明确的错误提示。
  - 验收点：错误信息包含：被阻断模块名、阻断原因（体积/依赖限制）、建议替代方案（如“请改用不依赖 vision/browser 的方案”或“在平台端改为非独立脚本运行”）。
  - 验收点：退出码非 0，日志中包含堆栈与 `blockedImports` 命中项。

- **标准 5**: 当脚本执行过程中发生错误时，应显示友好的错误信息和堆栈跟踪。
  - 验收点：终端/弹窗提示中包含“简要原因 + 指向日志路径”；日志文件包含完整 traceback。
  - 验收点：日志默认落盘到 `%LOCALAPPDATA%\\AstronRPA\\Logs\\standalone\\{appId}\\{date}.log`（或等价可配置路径）。

- **标准 6（性能）**: 启动性能满足基本体验要求。
  - 验收点（形态 A 冷启动）：从双击到执行入口 `main.py` 开始不超过 2s（在基准机器上）。
  - 验收点（形态 B 热启动）：缓存命中时启动耗时不超过 1s；首次运行允许更长但必须有进度提示。

- **标准 7（体积）**: 在排除 vision/browser 的前提下，产物体积可控。
  - 验收点：形态 A 默认产物大小目标 ≤ 250MB（可在后续迭代按真实依赖校准）。
  - 验收点：产物中不得包含 `opencv*`、`selenium*` 等默认阻断依赖（除非显式允许并在 Manifest 标记）。

### 3.2 兼容性验收标准

- **标准 9**: 导出的脚本应能在 Windows 10 x64 和 Windows 11 x64 系统上运行。

- **标准 10**: 导出的脚本应在非管理员权限账户下正常运行。

- **标准 11**: 导出的脚本应在完全离线的环境中正常运行。
  - 验收点：运行阶段无任何网络依赖（不调用 uv/pip 下载），可通过断网/抓包验证。

## 4. 关键约束与依赖 (Constraints & Dependencies)

### 4.1 技术约束

- **Python 版本**: 必须使用 Python 3.13 嵌入式运行时
- **打包工具**: 使用自定义启动器方案，不依赖 PyInstaller 等第三方打包工具
- **依赖管理**: 使用 UV 进行依赖解析和下载（仅用于导出阶段；运行阶段严禁联网下载）
- **组件排除**: 必须排除 astronverse-vision、astronverse-browser、astronverse-vision-picker、astronverse-verifycode 等包含 OpenCV 或浏览器自动化的组件

### 4.2 外部依赖

- **Python 嵌入式运行时**: 需要从 Python 官网下载 Python 3.13 Embedded ZIP 包
- **UV 包管理器**: 用于解析和下载 Python 依赖包
- **astronverse 组件**: 基于现有的 astronverse 组件库

### 4.3 数据要求

- 需要准备 Python 3.13 嵌入式运行时的下载链接或本地副本
- 需要维护一份核心组件清单，列出打包时包含的组件

## 5. 设计原则约束 (Design Principles Constraints)

### 5.1 可维护性 (Maintainability) - 最高优先级

**核心保障**: SOLID 原则、高内聚

- **单一职责原则 (SRP)**:
  - 启动器只负责环境初始化和脚本执行
  - 依赖分析器只负责分析脚本依赖
  - 打包器只负责文件打包和压缩

- **开闭原则 (OCP)**:
  - 通过接口抽象支持不同的打包格式（单文件、目录）
  - 支持扩展新的依赖分析规则而不修改现有代码

- **里氏替换原则 (LSP)**:
  - 所有依赖分析器实现可互换
  - 所有打包器实现可互换

- **接口隔离原则 (ISP)**:
  - 启动器接口只定义必要的方法
  - 避免依赖者依赖不需要的接口

- **依赖倒置原则 (DIP)**:
  - 高层模块（打包流程）依赖抽象接口，不依赖具体实现
  - 具体实现（依赖分析器、打包器）依赖抽象接口

- **高内聚**:
  - 相关功能聚合在同一模块中
  - 降低模块间耦合度

**实践要求**:
- 代码变更时，影响范围应最小化
- 新功能应通过扩展而非修改现有代码实现
- 模块边界清晰，职责明确

### 5.2 可测试性 (Testability)

**核心保障**: 关注点分离 (SoC)、依赖倒置原则 (DIP)

- **关注点分离**:
  - 业务逻辑（依赖分析、打包流程）与基础设施（文件操作、进程管理）解耦
  - 启动器逻辑与 Python 解释器调用解耦

- **依赖注入**:
  - 通过构造函数或参数注入依赖，便于 Mock
  - 文件系统操作、进程管理等外部依赖可注入

- **纯函数优先**:
  - 依赖分析逻辑应为纯函数
  - 减少副作用，提升测试可靠性

- **接口抽象**:
  - 为文件系统、进程管理等外部依赖定义抽象接口

**实践要求**:
- 核心业务逻辑必须可独立测试
- 集成测试与单元测试覆盖关键路径
- 避免全局状态和硬编码依赖

### 5.3 可读性 (Readability)

**核心保障**: KISS 原则 (Keep It Simple, Stupid)

- **简单性**:
  - 优先选择简单直接的实现，避免过度设计
  - 启动器逻辑清晰明了，易于理解

- **命名清晰**:
  - 变量、函数、类名应准确表达其意图
  - 使用领域术语（如 DependencyAnalyzer、PackageBuilder）

- **一致性**:
  - 遵循项目既定的代码风格和命名约定
  - 与现有 astronverse 代码风格保持一致

- **适度注释**:
  - 解释"为什么"而非"是什么"
  - 代码应自解释

**实践要求**:
- 代码应像自然语言一样易读
- 避免复杂的嵌套和过长的函数
- 优先使用项目已有的模式和约定

### 5.4 复用性 (Reusability)

**核心保障**: DRY 原则 (Don't Repeat Yourself)

- **消除重复**:
  - 提取公共逻辑到可复用模块
  - 文件操作、路径处理等通用逻辑统一实现

- **通用化设计**:
  - 识别并抽象通用模式
  - 打包流程可支持不同的打包格式

- **组合优于继承**:
  - 通过组合构建复杂功能
  - 启动器由多个可组合的组件构成

- **模块化**:
  - 将功能拆分为独立、可组合的单元
  - 每个模块职责单一，可独立测试和复用

**实践要求**:
- 相同逻辑只实现一次
- 优先使用项目现有的工具和组件
- 新增的可复用资产应纳入项目文档

## 6. 技术架构设计

### 6.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     导出流程（服务端）                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  代码生成器  │──▶│ 依赖分析器  │──▶│   打包器     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Python脚本  │  │  依赖清单    │  │  打包产物    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  打包产物结构（客户端）                       │
├─────────────────────────────────────────────────────────────┤
│  my_rpa_script/                                             │
│  ├── launcher.exe          (自定义启动器)                   │
│  ├── python_runtime/       (嵌入式 Python 运行时)          │
│  │   ├── python.exe                                         │
│  │   ├── python313.dll                                     │
│  │   ├── Lib/                                               │
│  │   └── ...                                                │
│  ├── packages/             (依赖包)                         │
│  │   ├── astronverse-system/                               │
│  │   ├── astronverse-excel/                                │
│  │   └── ...                                                │
│  ├── scripts/              (用户脚本)                       │
│  │   ├── main.py                                           │
│  │   ├── process1.py                                        │
│  │   └── ...                                                │
│  ├── config.json           (配置文件)                       │
│  └── requirements.txt      (依赖清单)                       │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 核心模块设计

#### 6.2.1 依赖分析器 (DependencyAnalyzer)

**职责**: 分析 Python 脚本的依赖关系，生成依赖清单

**接口定义**:
```python
from abc import ABC, abstractmethod
from typing import List, Set

class IDependencyAnalyzer(ABC):
    @abstractmethod
    def analyze(self, script_path: str) -> Set[str]:
        """分析脚本依赖，返回依赖的组件名称集合"""
        pass

    @abstractmethod
    def filter_excluded(self, dependencies: Set[str]) -> Set[str]:
        """过滤掉排除的组件"""
        pass
```

**实现类**:
- `StaticDependencyAnalyzer`: 基于静态代码分析，通过 import 语句识别依赖
- `ManifestDependencyAnalyzer`: 基于现有的 manifest 文件分析依赖

#### 6.2.2 打包器 (PackageBuilder)

**职责**: 将 Python 运行时、依赖包和用户脚本打包成可分发的格式

**接口定义**:
```python
from abc import ABC, abstractmethod
from typing import Dict

class IPackageBuilder(ABC):
    @abstractmethod
    def build(self, config: Dict) -> str:
        """构建打包产物，返回输出路径"""
        pass

    @abstractmethod
    def get_output_format(self) -> str:
        """返回打包格式（directory/zip/exe）"""
        pass
```

**实现类**:
- `DirectoryBuilder`: 打包为自包含目录
- `ZipBuilder`: 打包为 ZIP 压缩包
- `ExeBuilder`: 打包为单个可执行文件（可选）

#### 6.2.3 启动器 (Launcher)

**职责**: 初始化 Python 环境并执行用户脚本

**核心功能**:
1. 解压运行时和依赖到临时目录
2. 设置 Python 路径和环境变量
3. 执行用户脚本
4. 清理临时资源

**接口定义**:
```python
class ILauncher:
    def launch(self, script_path: str, args: List[str]) -> int:
        """启动脚本执行，返回退出码"""
        pass

    def cleanup(self):
        """清理临时资源"""
        pass
```

#### 6.2.4 启动器退出码约定（最小集）

> 约定目的：保证“终端/弹窗提示 + 日志落盘 + 机器可判定退出码”三者一致，便于排障与自动化回归。

建议最小覆盖以下 4 类（阶段一必须具备）：

| 场景 | 含义 | 退出码（建议） | 用户可见提示（最低要求） |
|---|---|---:|---|
| 成功 | 脚本执行完成 | 0 | 可选（或仅 INFO 日志） |
| Manifest 缺失 | 找不到 `manifest.json` | 10 | `原因 + 日志路径` |
| Manifest 损坏/不合法 | JSON 解析失败 / schema 校验失败 / 必填字段缺失 | 11 | `原因 + 日志路径` |
| 运行时异常 | 用户脚本抛错 / 启动器内部异常 | 30 / 90 | `原因 + 日志路径`（日志含 traceback） |

其中：
- “Manifest 缺失/损坏”必须在启动最早期失败，且不进入脚本执行阶段。
- 错误提示必须包含：简要原因、日志落盘路径（参考 3.1 标准 5）。


### 6.3 依赖管理策略

#### 6.3.1 核心组件清单

**必须包含的组件**:
- `astronverse-baseline`: 核心框架
- `astronverse-actionlib`: 原子操作定义
- `astronverse-executor`: 执行引擎
- `astronverse-system`: 系统操作
- `astronverse-excel`: Excel 操作
- `astronverse-word`: Word 操作
- `astronverse-pdf`: PDF 操作
- `astronverse-email`: 邮件操作
- `astronverse-database`: 数据库操作
- `astronverse-network`: 网络请求
- `astronverse-encrypt`: 加密解密
- `astronverse-dataprocess`: 数据处理

**必须排除的组件**:
- `astronverse-vision`: 包含 OpenCV
- `astronverse-vision-picker`: 包含 OpenCV
- `astronverse-browser`: 包含浏览器自动化
- `astronverse-browser-bridge`: 包含浏览器自动化
- `astronverse-browser-plugin`: 包含浏览器自动化
- `astronverse-verifycode`: 依赖浏览器自动化

#### 6.3.2 依赖解析流程

```
1. 解析用户脚本的 import 语句
2. 映射到对应的 astronverse 组件
3. 递归解析组件的依赖关系
4. 过滤排除的组件
5. 生成最终的依赖清单
```

> 重要说明：仅靠“解析 import 语句”的静态分析会在以下场景漏依赖：动态导入、插件/entrypoints、条件分支、资源驱动加载、可选依赖等。因此依赖解析必须支持“多来源合并”，并提供可追踪的输出（见 6.5 Manifest）。

#### 6.3.2.1 依赖解析输入来源（v1）

最终依赖清单由以下来源合并得到：

1. **静态扫描**：扫描导出脚本及其本地模块的 `import/from import`。
2. **组件映射表**：将抽象能力（如 excel/system）映射到 astronverse 组件（白名单优先）。
3. **组件元数据**：读取组件自身声明的依赖（如 `pyproject.toml` / `requires-dist` / 内部依赖清单）。
4. **手工补丁机制**：允许在导出 UI/配置中追加 `extraPackages` / `extraFiles`（解决动态依赖与边缘场景）。

#### 6.3.2.2 依赖解析输出（必须可审计）

- 输出 `manifest.json` 中的 `astronverse.includedComponents/excludedComponents` 与 `pythonPackages.requirements`。
- 输出 “依赖解析报告”（可作为日志/构建产物的一部分），至少包含：每个依赖的来源（静态扫描/映射/元数据/补丁）、是否被过滤及原因。

#### 6.3.2.3 过滤与阻断策略（必须一致）

- 被排除的 astronverse 组件不得进入产物。
- 与被排除组件强相关的三方包（如 `opencv-python`、浏览器自动化相关包）默认加入 `blockedImports`。
- 运行时若出现 `blockedImports` 中的导入，应立即以“可读错误”终止，并给出替代建议（见 3.1 标准 4）。

### 6.3.3 分发形态与运行模式（必须明确）

本功能支持两种导出产物形态，二者共享同一套依赖解析/裁剪规则与清单（Manifest），但运行方式不同：

#### 形态 A：自包含目录（Portable Directory）

- **产物**：一个目录，可被拷贝到任意位置直接运行。
- **运行方式**：就地运行（不解压到 `%TEMP%`）。
- **优点**：启动快、便于排障、资源可见。
- **适用**：内网分发、调试/测试、需要可追溯文件结构的场景。

#### 形态 B：单文件可执行（Single Executable）

- **产物**：单个 `.exe`，内部嵌入运行时与依赖（或携带旁路资源）。
- **运行方式**：首次运行解压到缓存目录（默认 `%LOCALAPPDATA%\\AstronRPA\\StandaloneCache\\{appId}\\{buildId}`），后续复用缓存（热启动）。
- **优点**：分发简单、文件少。
- **风险与约束**：需要并发互斥、缓存版本管理、杀软兼容（UPX 默认不启用）。

> 说明：PRD 默认以“形态 A”为 MVP 首选（启动更确定、问题更少）。形态 B 作为后续增强，在阶段计划中单独验收。

### 6.4 启动器实现细节

#### 6.4.1 启动流程

```
1. 检查临时目录是否存在
   - 如果不存在，解压运行时和依赖
   - 如果存在，跳过解压步骤

2. 设置 Python 环境变量
   - PYTHONHOME: 指向运行时目录
   - PYTHONPATH: 添加 packages 和 scripts 目录

3. 执行用户脚本
   - 调用 python.exe 执行 main.py
   - 传递命令行参数

4. 处理执行结果
   - 捕获退出码
   - 记录日志
   - 显示错误信息

5. 清理临时资源（可选）
   - 根据配置决定是否保留临时目录
```

> 修订：对“自包含目录（形态 A）”不应默认解压到 `%TEMP%`；对“单文件（形态 B）”应使用稳定缓存目录并带版本/并发控制（见 6.4.4）。

#### 6.4.2 临时目录管理

**临时目录结构**:
```
%TEMP%\astron_rpa_{timestamp}/
├── python_runtime/
├── packages/
└── scripts/
```

**清理策略**:
- 默认在脚本执行完成后清理
- 支持保留临时目录用于调试
- 支持手动清理命令

#### 6.4.3 运行目录与路径策略（就地运行优先）

- **形态 A（自包含目录）**：以产物根目录作为 `BASE_DIR`，所有路径相对 `BASE_DIR` 解析。
- **形态 B（单文件）**：以缓存根目录作为 `BASE_DIR`，启动器负责将嵌入资源解压/还原到缓存后再运行。
- 运行时需要显式屏蔽用户环境污染：启动器应在进程级清理/覆盖 `PYTHONHOME`、`PYTHONPATH` 等关键变量，确保不读取系统 Python 或用户 site-packages。

#### 6.4.4 并发、缓存与升级（单文件必备）

- **缓存键**：`{appId}/{buildId}`，其中 `buildId` 由（manifest + runtime + packages）的内容哈希决定。
- **并发互斥**：同一 `buildId` 首次解压需文件锁（例如 `cache.lock`），防止多进程写入冲突。
- **缓存失效**：当 `buildId` 变化视为新版本，保留旧版本缓存但可按策略清理。
- **清理策略**：默认不自动删除缓存（避免下次冷启动）；提供手动清理命令或按“最近 N 个版本/总大小阈值”回收。

### 6.5 产物结构与 Manifest（必须具备，可用于排障与验收）

#### 6.5.1 自包含目录（形态 A）推荐目录结构

```
export/
├── launcher.exe                # 自定义启动器
├── manifest.json               # 产物清单（必需）
├── runtime/                    # Python 3.13 Embedded（裁剪后）
│   ├── python.exe
│   ├── python313.dll
│   ├── python313.zip
│   └── python313._pth
├── packages/                   # 第三方依赖（wheel 解压后或按策略存放）
├── scripts/                    # 用户导出的脚本（main.py 等）
└── resources/                  # 业务资源（模板、图片、配置等）
```

#### 6.5.2 单文件可执行（形态 B）推荐结构

- `launcher.exe` 内部嵌入：`manifest.json`、`runtime/`、`packages/`、`scripts/`、`resources/`。
- 运行时解压/还原到缓存目录后执行，缓存目录结构与形态 A 的 `export/` 基本一致。

#### 6.5.3 Manifest 内容规范（v1）

`manifest.json` 作为导出产物的“唯一真相来源”，至少包含：

- `schemaVersion`: 清单版本（例如 `"1.0"`）。
- `appId`: 导出流程唯一标识（用于缓存/日志隔离）。
- `buildId`: 构建内容哈希（用于缓存命中、升级判断）。
- `createdAt`: 构建时间（ISO8601）。
- `python`: `{ "version": "3.13.x", "distribution": "embedded", "arch": "x64" }`。
- `entrypoint`: `{ "module": "main", "path": "scripts/main.py" }`。
- `paths`: `{ "runtimeDir": "runtime", "packagesDir": "packages", "scriptsDir": "scripts", "resourcesDir": "resources" }`。
- `astronverse`: `{ "baselineVersion": "...", "includedComponents": [...], "excludedComponents": [...] }`。
- `pythonPackages`: `{ "locked": true, "requirements": [...], "wheelFiles": [...] }`。
- `blockedImports`: `["astronverse_vision", "selenium", ...]`（用于运行时明确报错）。
- `nativeArtifacts`: `{ "dll": [...], "pyd": [...], "notes": "..." }`（用于自检与排障）。
- `runtimeOptions`: `{ "logLevel": "INFO", "keepCache": false, "keepTemp": false }`。

> 要求：启动器启动时必须校验 `manifest.json` 存在且可解析，否则以明确错误退出。

## 7. 实现方案

### 7.1 开发阶段划分

> 节奏原则：Week 1-6 优先交付“形态 A（自包含目录）”闭环；Week 7-8 在形态 A 稳定的前提下，补齐质量门槛并启动“形态 B（单文件）”增强的最小可用版本。

#### 阶段一：框架与契约（Week 1-2）——先把“可插拔 + 可验收”打牢

- 交付物
  - 依赖分析器/打包器/启动器的接口定义与最小实现骨架（可运行空流程）。
  - `manifest.json`（v1）schema/字段约定落地（至少能生成与校验）。
  - 基准示例流程与冒烟测试脚本（不含 vision/browser）。
- 验收
  - 形态 A 的目录结构可被生成（`runtime/ packages/ scripts/ resources/ manifest.json`）。
  - `launcher.exe` 能读取并校验 `manifest.json`，缺失/损坏时给明确错误并非 0 退出。

#### 阶段二：依赖解析与裁剪（Week 3-4）——让产物“够用且可控”

- 交付物
  - 依赖解析“多来源合并”（静态扫描 + 组件映射 + 组件元数据 + 手工补丁）。
  - 过滤/阻断策略实现：`excludedComponents` 与 `blockedImports` 生成规则。
  - UV 集成（导出阶段）：生成锁定信息（requirements/lock）并离线化依赖（下载 wheel 或导出可复现的依赖集合）。
  - 依赖解析报告（可审计）：记录每个依赖的来源、是否被过滤及原因。
- 验收
  - 运行阶段离线：产物运行时不触发 uv/pip 下载（断网可运行）。
  - 命中 `blockedImports` 时错误提示满足 3.1 标准 4（含模块名/原因/建议），并记录日志。

#### 阶段三：形态 A MVP 闭环（Week 5-6）——“自包含目录”可直接交付用户

- 交付物
  - 目录打包器（形态 A）：生成可拷贝运行的 `export/` 目录。
  - 启动器就地运行：以产物根目录为 `BASE_DIR`，正确设置 `PYTHONHOME/_pth` 路径，屏蔽外部 Python 污染。
  - 原生依赖收集规则落地（`.dll/.pyd` 等），并写入 `manifest.nativeArtifacts` 便于自检。
  - 集成到现有“代码生成/导出流程”UI/CLI：增加“导出独立脚本（形态 A）”选项。
- 验收
  - 在未安装 Python 的 Win10/Win11 机器上可运行通过（见 3.1 标准 2/3）。
  - 冷启动性能与体积达到 3.1 标准 6/7 的目标线（基准机/基准流程）。

#### 阶段四：质量门槛 + 形态 B 最小增强（Week 7-8）——先做“可控单文件”，再谈极致体验

- 交付物（质量门槛）
  - 集成测试矩阵：Win10/Win11、非管理员、离线、错误注入（缺包/阻断/运行异常）。
  - 日志与错误体验统一：默认日志落盘路径、退出码规范、提示模板。
  - 性能与体积回归基线：形成可重复的测量脚本与阈值。
- 交付物（形态 B 最小增强）
  - 单文件启动器原型：支持将形态 A 的目录内容“嵌入/携带”并解压到缓存目录再运行。
  - 缓存/并发锁/版本失效规则落地（见 6.4.4），提供手动清理命令。
  - 默认不启用 UPX；如需压缩，作为可选构建参数并评估杀软风险。
- 验收
  - 形态 B：首次运行可成功解压并执行；缓存命中时满足 3.1 标准 6（热启动目标）。
  - 多开并发不互相破坏缓存（同一 `buildId` 并发启动不报错、不产生半成品目录）。

### 7.2 关键技术点

#### 7.2.1 嵌入式 Python 配置

需要修改 `python313._pth` 文件，配置模块搜索路径：
```
python313.zip
.
./packages
./scripts
import site
```

#### 7.2.2 原生依赖处理

确保所有 `.dll` 和 `.pyd` 文件正确打包：
- pywin32 的 DLL 文件
- numpy 的二进制文件
- pandas 的二进制文件

#### 7.2.3 路径处理

使用相对路径，确保打包后的脚本可以在任意位置运行：
```python
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGES_DIR = os.path.join(BASE_DIR, 'packages')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
```

### 7.3 风险评估与缓解措施

#### 风险 1: 打包体积过大
**影响**: 用户体验差，分发困难
**概率**: 中
**缓解措施**:
- 精简 Python 运行时，移除不必要的模块
- 使用 UPX 压缩可执行文件
- 优化依赖包，只打包必要的文件

#### 风险 2: 启动时间过长
**影响**: 用户体验差
**概率**: 中
**缓解措施**:
- 实现增量解压，只解压必要的文件
- 使用缓存机制，避免重复解压
- 优化启动器代码，减少初始化时间

#### 风险 3: 兼容性问题
**影响**: 部分系统无法运行
**概率**: 低
**缓解措施**:
- 在多种 Windows 版本上进行测试
- 提供详细的错误日志
- 支持回退机制

#### 风险 4: 依赖冲突
**影响**: 脚本无法正常运行
**概率**: 低
**缓解措施**:
- 使用虚拟环境隔离依赖
- 严格版本控制
- 提供依赖冲突检测机制

## 8. 测试计划

### 8.1 单元测试

- 依赖分析器测试
- 打包器测试
- 启动器测试
- 路径处理测试

### 8.2 集成测试

- 完整的打包流程测试
- 脚本执行测试
- 错误处理测试

### 8.3 兼容性测试

- Windows 10 x64 测试
- Windows 11 x64 测试
- 非管理员权限测试
- 离线环境测试

### 8.4 性能测试

- 启动时间测试
- 内存占用测试
- 打包体积测试

## 9. 交付物

### 9.1 代码交付

- 依赖分析器实现代码
- 打包器实现代码
- 启动器实现代码
- 单元测试代码
- 集成测试代码

### 9.2 文档交付

- 技术设计文档
- API 文档
- 用户使用手册
- 开发者指南

### 9.3 工具交付

- 打包工具
- 测试工具
- 文档生成工具

## 10. 附录

### 10.1 术语表

- **嵌入式 Python**: Python 官方提供的嵌入式运行时，用于集成到应用程序中
- **启动器**: 负责初始化 Python 环境并执行用户脚本的可执行程序
- **依赖分析**: 分析 Python 脚本依赖的组件和库的过程
- **打包**: 将 Python 运行时、依赖包和用户脚本组合成可分发格式的过程

### 10.2 参考资料

- [Python Embedded Distribution](https://www.python.org/downloads/windows/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Python Packaging User Guide](https://packaging.python.org/)

### 10.3 变更记录

| 版本 | 日期 | 作者 | 变更内容 |
|------|------|------|----------|
| 1.0 | 2025-12-30 | AI | 初始版本 |
