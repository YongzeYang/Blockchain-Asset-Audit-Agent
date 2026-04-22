# Blockchain Asset Audit Agent MVP

🔗 **[English Documentation](README.md)**

## 📖 项目全景与愿景

Blockchain Asset Audit Agent 是一个专注于“基于区块链资产状态的高效自动审计”的 AI 智能体框架。它的核心使命是通过将专业的审计标准（SOP）泛化封装成一系列可复用、可调度的“技能 (Skills)”，结合强大的大模型（基于 Google Vertex AI 和 Gemini 2.5 Flash原生能力），自动化处理繁杂的对账、风险排查、对手方分析以及授权（Approve）安全审查。

本项目采用**纯后端无 UI（Backend-Only）**架构进行设计，对外提供标准化的 RESTful HTTP APIs，非常适合与现有的中后台系统、数据湖或定时审计任务（Crontab/DAG）集成。

---

## 🛠 功能亮点 (Core Features)

1. **结构化流程执行机制**
   * 支持多步骤推理（Tool Calling 驱动）。
   * 输出格式严格对齐预定义的 Pydantic 数据模型（如 `AuditReport`, `SkillDefinition`），避免大模型“幻觉”引发应用崩溃。
2. **动态多模态技能网关 (Dynamic Skill Execution)**
   * 取消了生硬的枚举判断，而是通过读取技能的 YAML 规范中所定义的 `output_schema` 自动路由至相应的执行管线。
   * **内置专家级技能**：
     * ⚖️ `ledger_reconciliation_review`：核心资产对账（链上资金流向 vs 内部账本登记）。
     * 🛡️ `counterparty_risk_review`：对手方风险排查（未知地址敞口、首笔大额转账告警）。
     * 🔓 `approval_risk_review`：代币授权审计（未设限权限授信、未经验证协约、异常大额 Allowance）。
3. **“AI 制作 AI”（SOP-to-Skill Conversion）**
   * 自建的 `skill_generator_basic` 接口可将安全/审计专家的自然语言指导手册（SOP），自动化翻译成标准的、可立刻挂载运行的 `.yaml` 结构化代理任务定义文件。
4. **强隔离合规访问与环境管控**
   * **彻底弃用基础 API Key。专门针对于企业与严格监管地域（如中国香港）的合规场景，只集成基于 Google Cloud 的 Application Default Credentials（ADC）认证，直连 Vertex AI。**
   * 分层环境变量（`.env` -> `.env.local` -> `.env.vertex.local` -> Shell Env），确保证书不被提交进 Git。

---

## 🏛 核心架构图解 (Architecture & Components)

本系统采用典型的洋葱架构构建思路，核心层侧重 LLM 通信并向外拓展：

```text
HTTP API 层 (FastAPI) [入口端]
  ├─ /v1/skills        -> 技能的管理（CRUD）
  ├─ /v1/audit/run     -> 资产与交易的结构化审计入口 (同步/异步任务运行)
  ├─ /v1/agent/run     -> 基于文本的通用代理解析
  └─ /v1/runs          -> 查看审计作业、执行日志、生成的工件

代理协调层 (Orchestrator) [核心逻辑]
  ├─ Agent Context       -> 追踪整个 Run Session、日志记录
  ├─ Tool Factory        -> 对接 SQLite、检索库，并通过类型推演(Annotation Wrapping)安全注册本地函数供 LLM Tool Calling
  └─ Skill Executor      -> 检查入参 -> 装配系统提示词 (Prompt) -> 分析 `output_schema` -> 调度 LLM 发射请求

模型适配层 (LLM Provider Interface)
  ├─ Mock Client         -> 用于本地沙盒的高速单元测试模式，零成本消耗
  └─ Vertex AI Client    -> 利用 google-genai SDK 结合 GCP Default Region 与 ADC 原生联机

持久化与知识支持层 (Storage & Knowledge)
  ├─ DB: SQLite          -> 存储 `runs` (状态)，`tool_calls` (调用的函数记录)，`skills` (动态更新代理)
  └─ Mock Retrieval      -> 轻量化内部知识（实体映射，黑客钱包情报，合规指引）文档召回
```

### 关键技术选型考量：
* **为何使用 FastAPI**：完美结合 Pydantic V2 以支撑强类型的数据进出，并为 LLM 提供清晰的 Schema 校验。
* **为何选用 Vertex ADC 验证**：在安全等级要求极高的机构部署（或受限出海可用区如香港的限制），通过服务账户（Service Account/ADC）替代易被窃取的纯文本 API Key。
* **为何劫持 Tool Factory 类型标注 (`functools.wraps`)**：在接入 `gemini-2.5-flash` 函数调用时需要保留元数据（`__annotations__`），我们的代理组件自动封装日志逻辑，彻底避免云端调用因为缺参数而导致的 KeyError 等报错。

---

## 🎯 业务用例详解 (Use Cases)

### 用例一：机构级资管月度核查（Ledger Reconciliation）
**背景**：企业每月末需核实以太坊链上大户地址与中心化财务系统（Ledger）数据一致性。
**执行**：
1. CRON Job 拉取内部数据库本月登记转账，以及对应区块链浏览器（Etherscan）中的记录数据。
2. 将数据组装为 `AuditRunRequest`（包含 `transactions`, `ledger_entries`, `balances`）。
3. 指定 `skill_id="ledger_reconciliation_review"` 提交给本系统的 FastAPI 端点。
4. Agent 交叉比对时间戳、哈希与转账数额，发现 2 笔内部已确认，但是链上迟迟未完结的卡单。
5. 自动吐出带有证据引用和严重性标记的结构化 `AuditReport` 供财务稽核。

### 用例二：突发黑天鹅/未知对手方风险排雷（Counterparty Risk）
**背景**：发现热钱包异常资金外流。需要紧急定位该收款“对手方”的风险指数。
**执行**：
1. 安全人员将异常时间段的 `TransactionRecord` 批量提交。
2. 调度触发 `counterparty_risk_review`。
3. Agent 主动调用 `mock_search` (企业内部知识库) 检索该地址，发现未标记/内部标签库不存在。
4. Agent 结合资金方向，分析认为该笔支出为无担保单向流出且目标地址首次被启用。
5. Agent 输出告警（Risk Level: `CRITICAL`），并且阻断进一步授权。

### 用例三：DeFi交互之前的预检查（Approval Risk）
**背景**：基金经理想要在一个新上线的去中心化借贷池抵押资金。
**执行**：
1. 系统爬取即将被确认的 Approve Tx (授权交易上下文) 推向系统。
2. 应用 `approval_risk_review` 技能。
3. Agent 判断出：允许扣款额度为 `Unlimited (Type(uint256).max)`，这过度曝光了用户的代币仓位。
4. 生成整改意见：“建议缩简 Allowance 到确切单笔投资额。”

### 用例四：业务专家创建全新合规制度（SOP translation）
**背景**：合规组长刚下发了新的《多重签名钱包反洗钱行为准则 (AML)》。由于不懂代码，无法添加 Agent 防御条件。
**执行**：
1. 组长将自己的 Word 文档准则丢入此接口，选择 `skill_generator_basic` 技能。
2. Agent 将这份纯文字说明解构出核心校验项，按照 YAML 模板自动生成一个 `aml_multisig_audit`。
3. 存储于数据层中。开发人员验证无误后，该企业立即拥有了全新审计技能！

---

## 🚀 快速启动指南

### 环境准备：
项目需要最低 `Python 3.11`。

```bash
# 激活环境与安装
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Google Vertex AI ADC 配置：
在受到严格风控管控地区，必须先通过你的 Google Cloud 租户做企业默认证书注册：
```bash
# 执行完毕后会弹窗，或提供命令行认证连接
gcloud auth application-default login

# 设置你的默认项目，最好设置 global 的地区环境以规避资源池不足（比如 asia-east2 不能部署某些模型）
export GOOGLE_CLOUD_PROJECT="your-google-project-id"
export GOOGLE_CLOUD_LOCATION="global"
```
你也可以在根目录新建被 `.gitignore` 隐藏的 `.env.local` 写入上述属性，系统启动时会自动读取映射。

### 开发调测：

使用内置的 mock 客户端，你无需验证凭证即可进行本地测试：

```bash
# 使用 Mock 模式运行
LLM_MODE=mock uvicorn app.main:app --reload

# 或执行测试用例：
python -m pytest -v
```

真实的 API 服务使用：

```bash
# 启动真实 Vertex 服务
LLM_MODE=vertex uvicorn app.main:app --reload

# 测试投递
curl -X POST http://127.0.0.1:8042/v1/audit/run \
  -H 'Content-Type: application/json' \
  -d @examples/audit_request.json
```

---

## 🖥️ 前端控制台（React UI）

[`frontend/`](frontend/) 提供一套浅色调、扁平化的 React 单页应用，覆盖后端所有能力：总览面板、技能库、结构化审计提交、运行历史与回放、SOP→Skill 生成器。

### 技术栈
- Vite + React 18 + TypeScript
- Tailwind CSS（自定义 `brand` 调色，indigo 系）
- TanStack Query 管理服务端状态、React Router 管理路由
- React Hook Form + Zod、react-markdown + remark-gfm、Sonner 提示、Lucide 图标

### 环境要求
- Node.js ≥ 18（在 20 / 24 上验证通过）
- 后端运行在 `http://localhost:8042`（参考上方快速启动）

### 开发启动
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5215
```
开发服务器已将 `/api/*` 代理到 `http://localhost:8042`（见 `frontend/vite.config.ts`），无需额外配置。如需直连后端，复制 `.env.example` 为 `.env.local` 并设置 `VITE_API_BASE_URL=http://localhost:8042`。

### 生产构建
```bash
cd frontend
npm run build       # 输出到 frontend/dist
npm run preview     # 以 :5215 预览构建产物
```

### CORS
FastAPI 默认为 `http://localhost:5215` 和 `http://127.0.0.1:5215` 启用了 `CORSMiddleware`。可通过 `CORS_ORIGINS` 环境变量覆盖（逗号分隔）：
```bash
export CORS_ORIGINS="http://localhost:5215,https://audit.example.com"
```

### 页面一览
| 路由 | 对接接口 | 用途 |
|---|---|---|
| `/` 总览 | `GET /health`、`GET /v1/runs?limit=5`、`GET /v1/skills` | 健康状态 + 近期运行 + 快捷入口 |
| `/skills` | `GET /v1/skills` | 技能库卡片网格 |
| `/skills/:id` | `GET /v1/skills/{id}` | 系统提示、允许工具、风险规则 |
| `/audit/new` | `POST /v1/audit/run` | 结构化表单 + JSON 编辑器 + “载入示例” |
| `/runs` | `GET /v1/runs` | 完整运行历史 |
| `/runs/:runId` | `GET /v1/runs/{id}` | AuditReport / Markdown / 工具调用时间线 / 原始字段 |
| `/skills/new` | `POST /v1/skills/generate`、`POST /v1/skills/save` | SOP → Skill 草稿生成与保存 |

---

## 🔑 邀请码机制（写入接口限制）

为避免在公网部署后被匿名流量耗尽 LLM 额度，所有**写入接口**均要求请求头携带 `X-Invite-Code`。查询接口（如 `GET /health`、`GET /v1/skills`、`GET /v1/runs` 等）不受影响。

**写死的有效邀请码**（参见 [`app/api/auth.py`](app/api/auth.py)）：

```
Chrissy
Ethan
```

受保护的路由：

| 方法 | 路径 |
|---|---|
| POST | `/v1/audit/run` |
| POST | `/v1/agent/run` |
| POST | `/v1/skills/generate` |
| POST | `/v1/skills/save` |

未携带或错误邀请码 → HTTP `401 {"detail": "invalid_invite_code"}`。

**前端**：打开页面后点击右上角 *邀请码* 胶囊，填入并保存；axios 拦截器会自动为所有非 GET 请求追加该请求头，值持久化在 `localStorage`。

**curl 示例**：

```bash
curl -X POST http://127.0.0.1:8042/v1/audit/run \
  -H 'Content-Type: application/json' \
  -H 'X-Invite-Code: Chrissy' \
  -d @examples/audit_request.json
```

> 仅作为轻量防滥用措施，不代替身份认证。生产环境建议掏空该机制，改用反向代理 + 专业鉴权。

---

## ☁️ 云服务器一键部署

面向一台**什么都没装**的 Ubuntu / Debian 云服务器，[`scripts/`](scripts/) 下两个脚本包揽了全部流程。默认端口：**8042**（后端）与 **5215**（前端），与常见其他 Web 服务错开。

### 1. Bootstrap（一键装环境）

```bash
bash scripts/bootstrap.sh
```

脚本会（可重复运行）：

1. `apt-get` 安装 Python 3.11+、`build-essential`、`curl`、`git`；若发行版自带 Python 过低会自动加 deadsnakes PPA。
2. 检测到未安装或低于 v18 时，从 NodeSource 安装 Node.js 20.x。
3. 创建 `.venv/` 并 `pip install -e ".[dev]"`。
4. 进入 `frontend/` 执行 `npm ci`（或 `npm install`） + `npm run build`。
5. 如不存在则写入 `.env`（后端，mock 模式）与 `frontend/.env.local`（`VITE_API_BASE_URL=http://localhost:8042`）。

自定义端口：
```bash
BACKEND_PORT=18042 FRONTEND_PORT=15215 bash scripts/bootstrap.sh
```

### 2. Deploy（启动 / 停止 / 状态 / 日志）

```bash
bash scripts/deploy.sh           # 默认 = start，后台拉起两个服务
bash scripts/deploy.sh status
bash scripts/deploy.sh logs backend     # tail -F 后端日志
bash scripts/deploy.sh logs frontend
bash scripts/deploy.sh restart
bash scripts/deploy.sh stop
```

- 后端：`uvicorn app.main:app --host 0.0.0.0 --port 8042`，PID / 日志在 `.run/`。
- 前端：`python3 -m http.server 5215 --directory frontend/dist --bind 0.0.0.0`，零额外依赖。

启动成功后访问：

- UI：`http://<服务器公网地址>:5215`
- API 文档：`http://<服务器公网地址>:8042/docs`

> 请在云供应商的安全组 / 防火墙中放行入向 TCP **8042** 与 **5215**。

如需生产使用 Vertex AI：

1. 编辑 `.env`（或 `.env.local` / `.env.vertex.local`）：
   ```
   LLM_MODE=vertex
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=global
   ```
2. 在服务器上执行 `gcloud auth application-default login`（或挂载服务账号密钥）。
3. `bash scripts/deploy.sh restart`。

