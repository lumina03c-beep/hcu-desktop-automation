# Dynamic UI RPA Skill V2 — 架构审计与实施计划

日期：2026-11-10  
阶段：Phase 0（只读审计；未修改实现代码）  
基线：`main` / `253c6594baf54c8fa9fed42eb35cfe869eb93a46`

## 1. 审计结论

当前仓库应作为 V2 的 **HCU Desktop 决策、安全治理、安装配置和离线评估底座**保留，不应重建或替换。

V2 的主要新增价值是：

1. Browser=ego-browser 与 Desktop=HCU 的双引擎路由。
2. 一个用户任务对应一个跨引擎 Task Workspace。
3. 已验证步骤、语义交接、局部恢复和跨引擎防重复执行。
4. Browser/Desktop/Hybrid 的真实评估与成本对照。

当前仓库尚不具备上述 V2 能力。本阶段只验证文档、离线测试和 ego-browser 当前指南，不声明真实 UI、跨引擎或性能验收已通过。

## 2. 本次实际核验范围

### 2.1 已检查

- `SKILL.md`、中英文 README、CHANGELOG、CONTRIBUTING、SECURITY。
- `docs/`、现有 8 个 `references/` 文件。
- `scripts/` 中安装配置、结构验证和结果聚合实现。
- `tests/`、`evaluations/`、`.github/workflows/validate.yml`。
- Git 工作区、最近提交和基线版本。

### 2.2 已执行并通过

- `python scripts/validate_skill.py`：通过；验证器口径为 113 个核心行，项目上限 120 行。
- `python -m unittest discover -s tests -v`：15/15 通过。
- `python scripts/summarize_results.py evaluations/example-results.json`：成功聚合 3 条明确标记为 synthetic 的示例。
- `python scripts/hcu_setup.py --help`：正常。
- `ego-browser skill`：退出码 0，完整读取 **v2.2.0 (windows)** 指南，并确认 `[ego-browser:skill] end of guide v2.2.0`。

### 2.3 NOT RUN

- HCU doctor、安装、配置写入和客户端重连。
- HCU AX/GUI 实际调用、窗口操作和 L3 桌面验证。
- ego-browser 真实 TaskSpace、页面导航、上传下载或浏览器结果验证。
- Browser → Desktop → Browser 真实混合任务。
- 模型调用、Token、延迟、恢复率和交接耗时的真实对照实验。
- 远端 CI 状态查询。

因此，本报告中的通过项仅是离线基线，不是 V2 端到端能力证明。

## 3. 当前架构与可复用能力

当前仓库是 HCU v4.0 策略层，不携带 Microsoft HCU 源码或二进制。核心闭环为 Task Contract → 最小观察 → 通道路由 → 风险分批 → 证据验证 → 副作用感知恢复。

### 3.1 可直接保留

| 能力 | 现有位置 | V2 用途 |
| --- | --- | --- |
| Goal/Target/Constraints/Risk/Success Oracle | `SKILL.md`、`references/contract.md` | 通用 Task Contract |
| 按真实状态所有者选择通道 | `references/routing.md` | 动态 UI 环境路由的基础原则 |
| R0/R1/R2 风险分级 | `SKILL.md`、`references/contract.md` | 跨引擎统一风险策略 |
| L1/L2/L3 证据等级 | `references/contract.md` | 防止把输入发送当作任务成功 |
| Mutation Ledger、effect_unknown 禁重放 | `references/recovery.md` | 跨引擎恢复与防重复副作用 |
| Two-Strike、安全停止与完成状态分离 | `references/recovery.md` | 局部恢复治理 |
| AX/GUI、refs、frame lease、平台规则 | `references/platforms.md` | Desktop Workflow 专用知识 |
| 单桌面单输入流、会话隔离 | `references/environments.md` | 防止多引擎并发控制同一桌面 |
| HCU stdio 安装与客户端适配 | `references/setup.md`、`scripts/hcu_setup.py` | Desktop 依赖接入 |
| Holdout、独立 L3、A/B/C 和至少 5 次运行 | `references/testing.md` | V2 评估卫生 |
| 离线结构和单元测试、三 OS CI | `scripts/`、`tests/`、`.github/workflows/validate.yml` | 回归门禁 |

### 3.2 必须保留的安全不变量

- `doctor` 和 `print-config` 保持只读；安装和配置写入必须明确批准。
- 不静默 sudo、不覆盖无关客户端配置、写入前备份。
- 通用 HCU 部署继续以 `<absolute-path>/computer-use mcp` stdio 为入口。
- 只有当前 HCU 会话返回的 refs 可用；Workspace 不延长其生命周期。
- R2 必须隔离、确认目标与载荷，并优先取得独立 L3。
- safe stop 不计任务成功；开发案例不得改名为 holdout。

## 4. 需要调整的现有能力

1. **可用性按引擎拆分**：当前“AX/GUI 不可用即停止”只适用于 Desktop 阶段，不能阻塞 Browser-only 任务。
2. **浏览器默认路由改变**：现有浏览器案例以 HCU AX/GUI 为主；V2 应默认 ego-browser，HCU 只处理原生桌面 UI 或明确的桌面回退。
3. **内部契约外化**：当前 Task Contract、route record 和 ledger 主要是内部推导；V2 需要最小、可审计、可恢复的 Workspace 记录。
4. **通用与 HCU 专有规则分层**：HCU refs、64 步、frame lease、Windows 输入 guard 不得套用到 ego-browser。
5. **恢复语义扩展**：需增加浏览器导航、页面无响应、下载、文件选择和页面变化等状态，但不能编造统一错误码。
6. **安装就绪模型拆分**：HCU smoke/doctor 只能证明 Desktop 的相应阶段，不能证明 Browser 或整个 V2 就绪。
7. **凭据策略统一**：`references/environments.md` 与 `SECURITY.md` 对凭据输入的表述需统一为一种明确策略。
8. **证据术语消歧**：架构层编号与 L1/L2/L3 证据等级不得在同一数据模型中混用。

## 5. ego-browser v2.2.0 核验结果与规格修正

以下仅来自本次实际读取的已安装指南，不从 Playwright 或旧规格推断。

### 5.1 已验证能力

- 每个用户目标使用一个 ego TaskSpace；后续轮次通过 `spaceId` 恢复同一空间。
- Page label 可跨轮次使用；JavaScript 变量不跨进程保留。
- 页面观察使用 `page.snapshot()`，视觉观察使用 `page.screenshot()`。
- 元素操作支持 snapshot refs、`loc=css:`、`loc=role:`、`loc=href:`、文本、XPath 和 CSS 等已列出的形式。
- 上传使用 `page.setInputFiles()` 或 `waitForFileChooser()` + `chooser.setFiles()`。
- 下载必须先等待 download event，并在本轮结束前 `saveAs()` 到绝对路径。
- 连续动作可与条件等待、最终观察放在同一脚本轮次；动态分支处拆分。
- action receipt 只证明动作派发及即时弹窗观察，不证明业务结果。
- 原始 CDP 会使 refs 失效；`page.targetId` 不得跨轮次持久化。
- 用户接管、空间 inactive/unassigned 时必须停止，不得绕过。
- 整体任务成功时 `finish()` 只调用一次；错误或用户接管时不调用。

### 5.2 原规格中不可直接落地的表述

| 原表述 | 当前已验证口径 |
| --- | --- |
| `snapshotText()` | 使用 `page.snapshot()` |
| `uploadFile` | 使用 `page.setInputFiles()` 或 FileChooser API |
| 每次 snapshot 重建 refMap 的固定实现描述 | 只保留“页面变化后重新 snapshot，旧 refs 不跨变化复用”的策略，不断言未验证内部实现 |
| 切换 Desktop 时结束 Browser TaskSpace | 若后续还要返回浏览器，应保持同一 ego TaskSpace；只在整个用户目标最终成功时 `finish()` |
| Browser Task Space 等同 Task Workspace | 两者关联但不同：前者是 ego 会话，后者是跨引擎语义任务上下文 |
| 可推断 Playwright API | 禁止；仅使用当前指南显式列出的 API 或 documented `evaluate()`/`cdp()` |
| 页面动作返回成功即可继续宣称完成 | receipt 不是业务证据，仍需页面或远端状态验证 |

## 6. V2 职责边界

### 6.1 Main Skill / Orchestrator

负责适用性判断、Task Contract、Workspace 生命周期、阶段级路由、引擎交接和最终完成判断。不得复制两套引擎手册，不得逐点击重新路由。

### 6.2 Browser Workflow

负责加载当前 ego-browser 指南、维护同一 ego TaskSpace、最小页面观察、批量确定性动作、动态等待和浏览器证据。Browser 文件上传优先留在 Browser；原生 Windows 对话框才进入 Desktop。

### 6.3 Desktop Workflow

负责复用现有 HCU 规则、AX/GUI 选择、当前会话 refs、桌面批次边界、effect/diff 和桌面证据。不得为了 V2 删除平台专项约束。

### 6.4 Shared Governance

负责 Workspace、风险、证据、mutation、恢复和完成验证。文件/Shell/CLI 是辅助能力，不构成第三个 UI 引擎，也不进入 Browser/Desktop 一级路由。

### 6.5 Evaluation

负责路由 fixtures、结构测试、真实 Browser/Desktop/Hybrid 任务和性能对照。文档测试不得冒充真实 UI 测试。

## 7. Task Workspace 契约方向

建议保留用户规格中的三个逻辑文件与 artifacts：

- `task.json`：目标、约束、成功标准、计划、阶段状态、验证状态。
- `execution.json`：活动引擎、切换原因、最后确认状态、下一动作、目标环境摘要。
- `mutations.jsonl`：仅有业务意义或副作用的变更。
- `artifacts/`：确需保留的下载、修改后文件和证据 manifest。

强制规则：

1. 一个用户任务只有一个 Workspace；ego TaskSpace ID 可作为 Browser 会话关联信息，但不是跨引擎永久 ref。
2. 只在任务开始、计划实质变化、阶段完成、切换、重要副作用、关键验证、阻塞/恢复和终止时更新。
3. 不保存完整对话、完整 DOM/AX、无关截图、凭据或模型内部推理。
4. 不保存 ego refs、`targetId`、HCU refs、GUI frame 或旧坐标作为可复用标识。
5. 已完成步骤必须带验证依据；`effect_unknown` 不得被标记完成或盲目重放。
6. 临时切换引擎不结束整个 Workspace，也不重新理解原始任务。
7. Workspace 的磁盘根目录、保留期、脱敏和并发所有权需在 Phase 2 明确；运行时数据不应默认写入 Skill 安装目录。

## 8. 建议的文件级演进

不删除现有 8 个 references，也不新增与其重复的“同义政策文件”。

| 文件 | 处理方式 |
| --- | --- |
| `SKILL.md` | 改为轻量双引擎入口，保持不超过 120 行 |
| `references/routing.md` | 扩展为 Browser/Desktop 一级路由及 HCU 内部通道规则 |
| `references/contract.md` | 保留 HCU 专有执行契约；公共契约新增 `task-contract.md` |
| `references/recovery.md` | 扩展统一副作用和跨引擎恢复语义，保留 HCU 错误知识 |
| `references/testing.md` | 扩展 V2 测试矩阵，保留 holdout 和独立 L3 约束 |
| `references/setup.md` | 保持 HCU Desktop 安装权威文档，明确不是全局 readiness |
| `references/platforms.md`、`environments.md`、`scenarios.md` | 保留并按双引擎边界调整引用 |
| `scripts/hcu_setup.py` | 继续只负责 HCU，不改造成 V2 总安装器 |
| `scripts/validate_skill.py` | 增量加入 V2 资源、schema 和链接校验 |
| `scripts/summarize_results.py` | 保持 v1 兼容，新增 V2 指标并隔离 synthetic |
| `evaluations/result.schema.json` | 保留 v1 语义；新增版本化 V2 schema，不静默改写旧结果 |

Phase 1–2 建议新增：

- `references/product-scope.md`
- `references/task-contract.md`
- `references/workspace-policy.md`
- `references/browser-workflow.md`
- `references/desktop-workflow.md`
- `references/hybrid-workflow.md`
- `references/execution-policy.md`

风险、证据和 ledger 优先由现有 contract/recovery 与 Workspace 政策承载，避免再建内容重叠的政策副本。

## 9. 分阶段实施计划与门禁

### Phase 1 — 产品边界、主 Skill 和路由

- 明确双引擎范围、非目标和辅助工具边界。
- 更新 `SKILL.md`、产品范围、路由和两个 Workflow 的加载入口。
- 保留现有 HCU 能力和原回归测试。
- 验收：结构/链接/单元测试通过；主文件不超行；路由 fixtures 覆盖不应切换和依赖不可用场景。
- 不宣称真实 UI 已验证。

### Phase 2 — Task Workspace

- 定义版本化 Workspace 示例/schema、状态更新、artifact manifest 和语义 handoff。
- 加入 refs 禁止持久化、已完成步骤验证依据和 `effect_unknown` 规则测试。
- 验收：单任务单 Workspace；跨引擎只传语义上下文；缺失/损坏上下文可安全停止或恢复。

### Phase 3 — Browser / Desktop Workflow

- Browser 仅采用已核验 ego API，并规定每轮指南加载、TaskSpace 恢复、批次和验证边界。
- Desktop 复用 HCU，不复制或削弱 AX/GUI 与平台规则。
- 验收：结构测试之外，分别执行真实 Browser 和 Desktop smoke；未执行项明确 NOT RUN。

### Phase 4 — Hybrid Workflow

- 实现 PREPARE → handoff → SELECT → 环境确认 → 重新观察 → CONTINUE。
- 验证 Browser → Desktop → Browser 连续任务，不重建 Workspace、不重复已验证步骤、不复用旧 refs。
- 临时离开 Browser 时不提前 `finish()`；最终成功才结束 ego TaskSpace。

### Phase 5 — Governance 与 Recovery

- 统一 R0/R1/R2、L1/L2/L3、Mutation Ledger、副作用分类、Two-Strike 和终止状态。
- 验收：R2 不进入普通批次；不确定副作用不盲目重试；未验证不得完成。

### Phase 6 — Evaluation 与性能

- 保留旧评估格式，新增 V2 schema、路由/浏览器/桌面/混合/性能用例。
- 开发、回归、冻结 holdout 分开；holdout 污染后替换。
- 主对照：A=原始逐步交互，B=V2 混合自适应；若保留旧 A/B/C 实验，必须在独立协议中定义，禁止复用旧 synthetic 数字。
- 相同任务、环境、模型、预算和成功标准；每条件至少 5 次新鲜会话；独立 L3 判定。
- 成功率与成本同时报告，单次案例不得宣称性能提升。

## 10. V2 指标口径

| 指标 | 最小定义 |
| --- | --- |
| Task Completion Rate | 独立验证完成的任务数 / 有效运行数；safe stop 单列 |
| End-to-End Latency | 任务开始到最终验证终止状态的墙钟时间 |
| Model Calls per Task | 客户端实际模型决策调用数；无遥测则 unknown，不估算 |
| Tool Round Trips | Browser、Desktop、辅助工具分别计数并汇总 |
| Observation Calls | snapshot、screenshot、AX/GUI 等观察分别计数 |
| Token Cost per Task | 输入/输出 Token 分列；无可靠价格时不虚构货币成本 |
| Recovery Rate | recovered / eligible failures；safe stop 不计恢复成功或任务成功 |
| Cross-Engine Handoff Latency | PREPARE 开始到下一引擎环境确认并可继续执行；用户等待另列，端到端时间仍包含 |

同时报告 False Success Rate、非必要切换率、恢复失败和原始错误。合成数据不得与真实数据混合形成性能结论。

## 11. 已发现的既有实现差距（非 V2 阻塞，但应登记）

- setup 确认预览未完整展示所有实际配置差异和命令。
- 多客户端写入不是事务，部分失败不会自动回滚。
- native doctor 失败可继续配置并返回成功，退出码不等于桌面就绪。
- 已有 HCU 源码树的 remote/ref 信任校验有限，tag 未固定到 commit SHA。
- 当前“JSON Schema 校验”主要是字段集合检查，不是完整 draft 2020-12 校验。
- summarizer 未强制 schema 的全部必填字段，synthetic 与真实 run 也未自动隔离汇总。

这些差距应在对应 Phase 小规模修正并补测试，不能借 V2 重写安装器。

## 12. 尚未验证的假设

1. 当前 HCU 二进制、上游工具集合和客户端适配在本机可用。
2. ego-browser CLI 指南可用即代表真实浏览器会话可用（目前不成立，仅是指南就绪）。
3. 两个引擎可在目标 Windows 桌面和浏览器环境中安全交接。
4. Workspace 文件在具体宿主客户端中可跨轮次可靠保留和恢复。
5. 模型调用和 Token 遥测能从目标客户端准确取得。
6. 当前远端 CI 通过；本地离线通过不能替代远端状态。
7. V2 能带来成功率或性能提升；在冻结 holdout 和真实对照前没有此结论。

## 13. Phase 0 退出状态

- 只读仓库审计：完成。
- ego-browser 当前指南核验：完成，v2.2.0。
- 离线基线：通过，15/15 单元测试。
- 实现代码修改：未进行。
- 真实 UI / Hybrid / 性能验收：NOT RUN。
- 下一步：等待确认本报告与 Phase 1 范围后，再修改主 Skill 和路由相关文件。
