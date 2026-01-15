# 离线绿色便携运行（Stand-alone Portable Offline）审计报告

Spec: `docs/specs/26011501-offline-standalone-local-run`

## Review Summary

- 结论：**请求修改（2 个阻塞项）**
- 审计范围：仅针对 `tasks.csv` 标注“已完成”的任务（T001–T010）做需求/实现一致性审计；对未在代码层实现但在文档宣称已完成的点，按风险优先级提出阻塞。
- 风险概览：
  - [阻塞] **默认离线/完全离线未形成“单一配置源 + 全链路约束”**：当前实现存在多处“离线假设”是硬编码或仅 UI 置灰，仍可能出现网络出站（尤其是 Electron 的 `webRequest` 白名单、`resources/conf.yaml` 默认 remote 配置、以及运行时 authType 逻辑）。
  - [阻塞] **构建链路与“bun 一律”规范冲突**：`build.bat` 使用 `bun install`，但 `frontend/package.json` 的 `preinstall` 强制 `pnpm`，导致一键构建无法按文档/脚本路径执行。
  - [高] **/health 闭环未完全落在“主进程探活驱动 ready”**：引擎侧已有 `GET /health`，但当前 Electron 主进程启动链路未见对 `http://127.0.0.1:13159/health` 的轮询与 UI ready 驱动（当前 Boot 流程依赖 `scheduler-event` 的 `sync_cancel` 事件）。
  - [中] **便携落盘与配置读取仍有歧义**：诊断包读取的是解压根目录 `conf.yaml`，而运行时配置读取的是 `resources/conf.yaml`（打包后 `appPath/../conf.yaml`），这会导致“用户修改配置文件到底改哪一个”的不确定性。

## 验证记录

本次审计通过静态检索与代码阅读完成，未执行完整构建与运行（原因：前端依赖安装被 `preinstall` 阻断，详见阻塞项 #2）。

- 代码检索：`rg -n "RunProfile|PathPolicy|FeatureGate|/health|13159|0.0.0.0" -S`
- 版本与构建脚本审阅：`build.bat`、`frontend/package.json`、`frontend/packages/electron-app/electron-builder.json`
- 关键实现文件抽样：
  - `frontend/packages/shared/src/platform/policy.ts`
  - `frontend/packages/electron-app/src/main/updater.ts`
  - `frontend/packages/electron-app/src/main/policies/pathPolicy.ts`
  - `frontend/packages/electron-app/src/main/diagnostics.ts`
  - `engine/servers/astronverse-scheduler/src/astronverse/scheduler/apis/route.py`
  - `resources/conf.yaml`

## 逐任务审计结论（T001–T010）

### T001 拆分运行配置维度（RunProfile + TerminalMode）

- 现象：共享层定义了 `RunProfile`、`NetworkPolicy`、`FeatureGate`、`CapabilityMatrix`（`frontend/packages/shared/src/platform/policy.ts`）。
- 缺口：未发现 `TerminalMode` 的枚举/默认值/读取优先级在代码层落地；`RunProfile` 也未见由配置驱动（当前在 `frontend/packages/electron-app/src/main/updater.ts` 直接硬编码 `RunProfile.OFFLINE`）。
- 影响：
  - 运行行为不可配置、不可验证，后续 “ONLINE + NORMAL / OFFLINE + SCHEDULING” 等组合会退化为到处 if 或硬编码。
  - 文档声称的“固定配置读取优先级与落盘位置”无法审计为真。
- 判定：**部分达成（文档/类型已建，但缺少端到端配置落地）**。

### T002 PathPolicy 统一落盘到解压目录

- 现象：Electron 主进程已使用 `resolveWorkDirs()` 计算 `data/runtime/exports/logs`（`frontend/packages/electron-app/src/main/policies/pathPolicy.ts`），并在 `frontend/packages/electron-app/src/main/path.ts` 将 `appWorkPath` 指向 `workDir`，覆盖了 `%APPDATA%` 的默认行为。
- 关注点：`resourcePath` 在 packaged 时取 `appPath/../`，意味着运行期资源与配置仍紧贴包体目录；这符合“绿色便携”，但需要明确：哪些文件允许用户修改、哪些是不可变资源。
- 判定：**达成（portable-first 写入路径基本闭环）**。

### T003 离线门禁与网络策略（默认不出网）

- 现象：
  - Updater 侧：`frontend/packages/electron-app/src/main/updater.ts` 在 `RunProfile.OFFLINE` 下禁止 `checkForUpdates()` 执行，且仅在 `canCheckUpdate` 时 `setFeedURL`。
  - UI 侧：`DEFAULT_OFFLINE_CAPABILITY_MATRIX` + `OfflineGate` 用于禁用“检查更新”按钮（`frontend/packages/web-app/src/components/SettingCenterModal/components/about.vue`）。
- 缺口（关键）：
  - Electron 主进程仍配置了 `webRequest` 的 `REQUEST_WHITE_URL` 白名单，包含外部域名（`frontend/packages/electron-app/src/main/env.ts`），并且会对匹配 URL 写入 `Cookie: jwt=...`（`frontend/packages/electron-app/src/main/index.ts` 的 `sessionHanlder()`）。这属于明确的“出网通道”与“敏感会话构造”，与 PRD 的“默认行为不得主动访问互联网”冲突。
  - `resources/conf.yaml` 默认 `remote_addr` 指向内网 IP；Web 端 `useAppConfigStore` 读取 `remote_addr` 并展示为 `remotePath`；同时 Electron updater 拼接 `config.remote_addr`。虽然 OFFLINE 下不调用 updater，但这套配置表明“离线/在线”并没有以配置维度隔离清楚。
- 判定：**表层达成（更新检查被门禁），但“默认不出网”的系统性约束未闭环（阻塞项 #1）**。

### T004 固定入口端口 13159 + 健康检查闭环

- 现象：引擎侧 `GET /health` 已实现并返回 `status` 与 `route_port`（`engine/servers/astronverse-scheduler/src/astronverse/scheduler/apis/route.py`）。
- 缺口：Electron 主进程未见对 `http://127.0.0.1:13159/health` 的轮询探活；Web 端启动页 Boot 的完成依赖 `scheduler-event` 中 `sync_cancel` 事件携带 `route_port`（`frontend/packages/web-app/src/views/Boot/Index.vue`）。
- 风险：端口占用、服务未就绪时，UI 可能表现为“卡在 boot”或依赖某个事件才能推进，达不到 PRD/TECHNICAL_APPROACH 所描述的“探活驱动 ready”。
- 判定：**部分达成（/health 已有，但闭环驱动链路需补全）**。

### T005 移除登录流程与鉴权依赖

- 现象：
  - 路由守卫中登录跳转逻辑被注释掉，且无权限访问回退到 `/index.html`（`frontend/packages/web-app/src/router/index.ts`）。
  - HTTP 401 的处理提示“离线便携模式下无需登录”（`frontend/packages/web-app/src/api/http/env.ts`）。
- 缺口：
  - 仍存在 `app_auth_type: casdoor` 的配置项（`resources/conf.yaml`）以及 `useAppConfigStore` 对 `app_auth_type` 的解析（`frontend/packages/web-app/src/stores/useAppConfig.ts`），说明鉴权体系仍在配置层“被保留”，需要明确 OFFLINE 下这些字段是否被忽略。
  - Electron 层仍存在 jwt cookie 注入逻辑（`frontend/packages/electron-app/src/main/index.ts`），与“无登录/无授权”目标冲突。
- 判定：**部分达成（UI/路由层已去登录，但主进程/配置层仍残留登录假设，纳入阻塞项 #1）**。

### T006 离线置灰能力矩阵

- 现象：共享层提供 `CapabilityMatrix`，并在 about 页用 `OfflineGate` 对“检查更新”统一置灰与 reason（`frontend/packages/web-app/src/components/SettingCenterModal/components/about.vue`）。
- 缺口：目前矩阵覆盖范围较小（UPDATE/MARKET/CLOUD_AI），且在 UI 中的落地仅见 about 页；PRD 期望“入口层统一渲染（按钮/菜单/页面）”。
- 判定：**达成度一般（机制已建立，但覆盖面与“一致性”需要扩展）**。

### T007 诊断包导出

- 现象：Electron 侧实现 `export-diagnostics` IPC，输出到 `data/exports/diagnostics/diag-<ts>`，并包含 `meta.json`、`conf.yaml`（若存在于 rootDir）、最近日志等（`frontend/packages/electron-app/src/main/diagnostics.ts`）。Web 端 about 页提供“导出诊断包”按钮调用该 IPC（`frontend/packages/web-app/src/api/diagnostics/index.ts`、`frontend/packages/web-app/src/components/SettingCenterModal/components/about.vue`）。
- 缺口：诊断包“端口状态/进程状态（可选）”目前未实现；可接受，但建议在 `meta.json` 增加对 `13159` 端口探测结果，提升可运维性。
- 判定：**达成（MVP 可用，增强项可迭代）**。

### T008 离线便携 zip 打包与构建流水线固化

- 现象：`build.bat` 已包含引擎 runtime 生成（`python_core.7z` + sha256），并调用前端 `bun run build:desktop`（见 `build.bat`）。文档 `docs/specs/26011501-offline-standalone-local-run/build.md` 也描述了一键构建与产物。
- 缺口（关键）：`frontend/package.json` `preinstall` 强制 `pnpm`，导致 `bun install` 在仓库默认配置下失败，进而 `build.bat` 的“一键构建”不可执行。
- 判定：**未达成（阻塞项 #2）**。

### T009 全局 loopback-only 收敛

- 现象：至少 browser-bridge 服务默认 host 已为 `127.0.0.1`（`engine/servers/astronverse-browser-bridge/src/astronverse/browser_bridge/config.py`），且大量内部调用显式使用 `127.0.0.1`。
- 缺口：未发现统一的 `BindPolicy` 读取 `resources/conf.yaml` 并注入到所有服务；仍可能存在个别服务默认 `0.0.0.0`（审计中在前端 dev server 配置见 `host: '0.0.0.0'`，但 dev 环境不一定影响 packaged）。
- 判定：**基本达成（核心服务倾向 loopback），但“全局统一配置源/强约束”仍建议补全**。

### T010 Windows 无管理员权限 + zip 便携

- 现象：`frontend/packages/electron-app/electron-builder.json` 配置 `win.target=zip` 且 `requestedExecutionLevel=asInvoker`。
- 判定：**达成（配置层满足 PRD 要求）**。

## 详细问题（按优先级）

1. [阻塞] 默认离线未形成“单一配置源 + 全链路禁出网”闭环
   - 现象：
     - `frontend/packages/electron-app/src/main/env.ts` 中 `REQUEST_WHITE_URL` 包含外部域名；`frontend/packages/electron-app/src/main/index.ts` 会对这些请求附加 `Cookie: jwt=...`。
     - `resources/conf.yaml` 仍包含远端 `remote_addr` 与 `app_auth_type`，Web 端/Updater 仍读取该配置。
   - 影响：
     - 无法向安全审计证明“默认不出网”，且存在将会话/凭证构造注入到外部请求的风险面。
     - “无登录/无授权”在主进程网络层被破坏，容易引入隐形依赖与后续回归。
   - 建议：
     - 在 Electron 主进程引入“默认 OFFLINE profile”的配置读取（落盘到解压目录），并在 `webRequest` 层做硬拦截：OFFLINE 下只允许 `127.0.0.1`/`localhost` 的请求；任何外域请求直接 `cancel` 并可选记录日志。
     - 将 `REQUEST_WHITE_URL` 外域条目迁移为 ONLINE profile 才启用（或按 feature gate 注入）。
     - 明确 `resources/conf.yaml` 的默认内容：OFFLINE 交付包内应默认不包含需要远端的配置，或将其置空并保证读取逻辑可容错。
   - 优先级：P0
   - 状态：未解决

2. [阻塞] 构建脚本与包管理器约束冲突（bun vs pnpm）
   - 现象：`build.bat` 执行 `bun install`，但 `frontend/package.json` 的 `preinstall` 强制 `pnpm`，实际运行 `bun install` 会失败。
   - 影响：`docs/specs/26011501-offline-standalone-local-run/build.md` 与 `build.bat` 描述的一键构建不可用，无法支撑“可复现构建”。
   - 建议：统一选择一种包管理策略：
     - 若项目规则是“Node.js 一律用 bun”，则移除/调整 `preinstall`（允许 bun），并确保 workspace + lockfile 与 bun 的行为一致。
     - 若必须用 pnpm，则应修改 `build.bat` 使用 `pnpm install`/`pnpm -r`，并移除对 bun 的硬依赖（或在脚本开关中兼容）。
   - 优先级：P0
   - 状态：未解决

3. [高] 健康检查闭环与 UI ready 驱动不一致
   - 现象：引擎有 `GET /health`，但当前 UI 启动推进依赖 `scheduler-event` 的 `sync_cancel`。
   - 影响：启动时序复杂，且端口占用/服务卡死时缺少统一的 “ready/failed” 状态机。
   - 建议：按 TECHNICAL_APPROACH 明确的方案落地：主进程轮询 `/health`（超时、重试、错误提示），并把结果作为 Boot 页 ready 的唯一数据源。
   - 优先级：P1

4. [中] 诊断包内容可运维性不足
   - 现象：诊断包未包含端口占用/服务存活等信息。
   - 影响：离线环境排障仍需要人工复现。
   - 建议：在 `meta.json` 中加入对 `13159` 的探测结果（HTTP 状态、响应 body 摘要、耗时），以及进程名 `astronverse.scheduler` 是否存活的检测结果。
   - 优先级：P2

## 结论与下一步

建议在合并/发布离线便携包之前，先完成两个阻塞项：

1) OFFLINE profile 的系统性“禁出网”收敛（配置源 + webRequest 硬拦截 + 清理外域白名单 + 移除 jwt 注入链路）

2) 统一构建工具链（bun vs pnpm），确保 `build.bat` 可在干净环境一键成功

