# 技术实现路径（Technical Approach）

本文件基于 `docs/specs/26011501-offline-standalone-local-run/prd.md`，给出“离线绿色便携版（zip 免安装）”的技术实现路径。

目标优先级：可维护性 > 可测试性 > 可读性 > 复用性。

## 0. 实施原则（把 PRD 约束落到工程决策）

- **离线优先**：默认启动链路不得产生外网请求；在线能力仅作为“扩展能力”存在。
- **绿色便携优先**：默认数据目录在解压目录内（portable-first）；删除目录即卸载。
- **最小权限**：不申请管理员权限，不写系统目录/系统注册表，不注册服务。
- **最小暴露面（全局非功能性需求）**：全部本地服务仅允许监听 `127.0.0.1`；禁止绑定 `0.0.0.0`；不要求防火墙入站。
- **固定入口端口**：复用现有 `route_port=13159` 作为唯一固定入口端口（第一个固定接口）。
- **功能尽量保留**：能在离线 + 用户态 + loopback 下实现的能力必须保留；真正离线不可达的入口先置灰并标注原因。
- **无登录、无授权**：移除登录/许可相关流程与依赖。

## 1. 现状代码心智地图（与本需求强相关的真实代码线索）

### 1.1 Electron 桌面端：本地引擎启动与“解压 Python 包”机制已存在

- `frontend/packages/electron-app/src/main/server.ts`
  - 使用 `pythonExe` 运行 `-m ${envJson.SCHEDULER_NAME} --conf="${confPath}"` 启动 Python 侧调度/服务。
  - Windows 下会扫描 `resourcePath` 的 `.7z` 包并解压到 `appWorkPath`，通过 `.sha256.txt` 做增量判断。
  - 已包含 7z 解压器调用：`frontend/packages/electron-app/src/main/file.ts` / `frontend/packages/electron-app/src/main/path.ts`。

这意味着：**“允许首次启动自初始化/解压 runtime”已经有成熟模式**，只需把“落盘位置”和“离线策略”收敛到 PRD 要求。

### 1.2 当前落盘路径不满足 portable-first，需要做“路径策略抽象”

- `frontend/packages/electron-app/src/main/path.ts`
  - `appWorkPath = app.isPackaged ? userDataPath : path.join(appPath, 'data')`

在 packaged 场景下默认写入 `userDataPath`（%APPDATA%），与 PRD 的“绿色便携”冲突。因此实现路径必须引入 **PathPolicy（路径策略）**：portable 模式强制把工作目录固定为“解压目录相对路径”。

### 1.3 默认更新检查存在（离线最大破坏源）

- `frontend/packages/web-app/src/views/Home/App.vue`：`onMounted(() => appStore.checkUpdate())`
- `frontend/packages/electron-app/src/main/updater.ts`：`electron-updater` 的 `checkForUpdates()`

实现路径必须引入 **OfflineGate（离线门禁）**，在离线便携模式下：
- 不允许自动触发更新检查
- 相关 UI 入口置灰

### 1.4 route_port 已是事实入口端口（建议复用为固定入口）

- Python 侧多处使用 `gateway_port/route_port`（默认 `13159`）作为网关/路由端口。
- 因此本迭代“固定入口端口”建议直接复用 `route_port=13159`，避免引入第二个入口端口配置。

### 1.5 loopback-only 当前不统一（必须收敛为全局 NFR）

- `engine/servers/astronverse-browser-bridge/.../config.py` 默认 `app_host="0.0.0.0"`（风险：对外暴露）。
- `engine/servers/astronverse-trigger/.../__main__.py` 使用 `uvicorn.run(... host="127.0.0.1")`（说明部分服务已满足要求）。

结论：需要一个统一的 **BindPolicy（绑定策略）** 或统一配置源，确保所有服务默认仅绑定 `127.0.0.1`。

## 2. 总体架构：以“配置维度拆分 + 门禁（Gate）+ 策略（Policy）”解耦

为保证 SOLID + 可测试性，本迭代核心新增能力不以“到处 if (offline)”的方式散落，而以策略注入完成。

### 2.1 配置维度：RunProfile + TerminalMode（避免 AppMode 冲突）

- `RunProfile`（网络/交付形态维度）
  - `OFFLINE`（本迭代默认）
  - （未来扩展）`ONLINE`

- `TerminalMode`（运行角色/拓扑维度）
  - `NORMAL`
  - `SCHEDULING`

这两个维度独立组合，避免与现有“调度模式/终端模式”概念冲突，也避免把网络与拓扑耦合在一个枚举里。

### 2.2 关键抽象

- `PathPolicy`（路径策略）
  - 输入：`appPath/resourcePath` 等基础路径
  - 输出：`workDir`、`runtimeDir`、`dataDir`、`logsDir`、`exportsDir`
  - 目标：将“路径选择”从业务逻辑中剥离，便于单测与未来扩展（OCP）。

- `BindPolicy`（监听绑定策略，全局 NFR）
  - 输出：`bindHost = 127.0.0.1`
  - 目标：所有服务统一读取，不允许散落写死 `0.0.0.0`。

- `NetworkPolicy`（网络策略）
  - `allowInternet: false`
  - `allowLoopback: true`
  - 目标：统一决定“哪些网络行为允许”，所有会出网的模块必须依赖该抽象。

- `FeatureGate`（功能门禁）
  - `canCheckUpdate()`、`canUseMarket()`、`canUseCloudAI()` 等
  - UI 层：决定是否置灰/展示提示
  - 基础设施层：决定是否直接阻断调用（双保险）

- `ProcessOrchestrator`（进程编排）
  - 启动/停止/健康检查 Python 引擎及必要的本地服务
  - 对外暴露 `route_port=13159` 的探活与状态

> 原则：UI/业务代码只依赖抽象（DIP），具体实现按 profile/mode 注入（OCP）。

## 3. 端到端实现路径（按交付闭环拆解）

### 3.1 交付物结构（zip 免安装）

目标 zip 内至少包含：
- Electron 桌面端（已打包）
- `resources/`（现有资源目录机制）
- 内置 Python runtime 与依赖（以 `.7z` 包或其它方式）

首次启动允许在解压目录内生成：
- `./data/`、`./runtime/`、`./exports/`（PRD 目录结构）

实现复用点：直接复用 `server.ts` 的“扫描 resources 下 .7z → 解压到工作目录”的流水线。

### 3.2 Portable-first 落盘：实现 PathPolicy 并贯穿主进程

- 新增（建议位置）：`frontend/packages/electron-app/src/main/policies/pathPolicy.ts`
  - `resolveWorkDirs(appPath): { workDir, runtimeDir, dataDir, exportsDir, logsDir }`
  - packaged 场景也固定输出为 `path.join(appPath, 'data')` 等相对路径

- 修改（最小化影响）：
  - 将 `frontend/packages/electron-app/src/main/path.ts` 中的 `appWorkPath`、`pythonCore` 等改为通过 `PathPolicy` 计算
  - `server.ts`、`log.ts`、`file.ts` 等使用统一的路径来源

可测试性：对 `PathPolicy` 做纯函数单测（无需 Electron 环境）。

### 3.3 固定入口端口：复用 route_port=13159

实现建议：
- 统一由配置源提供 `route_port`（固定为 `13159`），作为“系统网关/路由/入口”端口。
- Python 侧在该端口提供：
  - `/health`（基本健康）
  - `/capabilities`（可选：返回功能可用性/依赖是否就绪）

主进程职责：
- 启动 Python 引擎后轮询 `http://127.0.0.1:13159/health` 来决定 UI 的“已就绪”状态。

异常处理：
- 若 `13159` 端口被占用：MVP 直接报错并提示用户（避免不确定状态）。

### 3.4 全局 loopback-only：引入 BindPolicy 并收敛所有服务监听

- 明确禁止 `0.0.0.0` 默认监听。
- 收敛方式建议：
  1) 统一配置文件（例如 `conf.yaml`）提供 `bind_host=127.0.0.1`
  2) 各 Python 服务启动时读取该值并传给 uvicorn/fastapi/flask
  3) 对于默认 `0.0.0.0` 的服务（如 browser-bridge），必须在实现中收敛

可测试性：
- 对配置解析做单测
- 启动时可通过探测 `/health` 仅能从 127.0.0.1 访问来验证（集成测试）

### 3.5 离线门禁：阻断默认更新检查 + UI 置灰

两层门禁：
- UI 层：Home/App 启动不自动 checkUpdate；入口统一置灰
- 主进程层：`electron-updater` 在 `RunProfile=OFFLINE` 下不执行任何网络调用

### 3.6 移除登录流程（无登录、无授权）

- 路由/入口层面去掉登录页跳转与入口按钮
- 若存在鉴权拦截器（HTTP 401 → 跳登录），在离线模式下变为“提示离线不可用”或“直接放行本地能力”

## 4. 测试策略（让核心路径可测）

### 4.1 单元测试（优先、快速、稳定）

- `PathPolicy`：输入不同 `appPath`，断言输出目录结构正确（纯函数）。
- `BindPolicy`：断言输出 host 恒为 127.0.0.1。
- `FeatureGate/NetworkPolicy`：断言离线 profile 下各能力正确置灰。

### 4.2 集成测试（最小闭环）

- Electron 主进程在“OFFLINE + NORMAL”下启动：
  - 不调用 updater
  - 能启动 Python 进程并在 `127.0.0.1:13159` 探活成功

## 5. 复用资产清单（尽量不重复造轮子）

- 复用“首次启动解压 Python 包”能力：
  - `frontend/packages/electron-app/src/main/server.ts`
  - `frontend/packages/electron-app/src/main/file.ts`（7z 解压）

- 复用现有配置读取：
  - `frontend/packages/web-app/src/stores/useAppConfig.ts` 已有读取 `conf.yaml` 的路径与解析模式

## 6. 风险清单与验证顺序（最小化返工）

1) **默认出网点清单化**：梳理所有 update/market/cloud api 的调用入口，确保 OFFLINE 下不会触发。
2) **portable 落盘一致性**：任何写入点必须走 `PathPolicy`，避免散落硬编码。
3) **全局 loopback-only 收敛**：确认所有服务都只监听 127.0.0.1（重点排查默认 0.0.0.0 的服务）。
4) **固定入口端口**：13159 占用的处理必须在 MVP 明确（提示 + 退出）。
5) **权限风险**：确认是否有需要管理员的 manifest/驱动/hook；如有，先隔离为可选能力并与产品确认。

## 7. 里程碑拆分（建议）

- M1：引入 RunProfile + TerminalMode + PathPolicy，确保 packaged 场景也落盘到解压目录
- M2：引入 FeatureGate，关闭默认更新检查，UI 入口置灰
- M3：复用 `route_port=13159` 完成健康检查闭环（启动 → ready）
- M4：全局 loopback-only 收敛（BindPolicy + 服务监听统一）
- M5：移除登录流程（路由/拦截器/后端鉴权按需收敛）
- M6：离线诊断包导出（目录结构 + 一键打包）

