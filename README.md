# Blockchain Asset Audit Agent MVP

🔗 **[中文说明文档](README-cn.md)**

## 📖 Project Overview & Vision

The Blockchain Asset Audit Agent is an AI agent framework specifically designed for "highly efficient, automated auditing based on blockchain asset states". Its core mission is to encapsulate professional auditing standards (SOPs) into a series of reusable, schedulable "Skills". Powered by robust Large Language Models (leveraging Google Vertex AI and Gemini 2.5 Flash native capabilities), it automates complex reconciliation, risk identification, counterparty assessment, and authorization (Approve/Allowance) security reviews.

This project utilizes a **Backend-Only (No-UI)** architecture, exposing standardized RESTful HTTP APIs. It is highly suitable for seamless integration with existing middle-/back-office systems, data lakes, or cron-time DAG audit workflows.

---

## 🛠 Core Features

1. **Structured Execution Mechanism**
   * Supports multi-step reasoning driven by intelligent Tool Calling.
   * Outputs strictly align with predefined Pydantic schemas (e.g., `AuditReport`, `SkillDefinition`) to prevent systemic failures caused by LLM "hallucinations".
2. **Dynamic Multi-Modal Skill Execution Gateway**
   * Drops rigid enum-based routing in favor of dynamically reading the `output_schema` instruction defined within a skill's YAML specification, routing the payload to the correct execution pipeline.
   * **Built-in Expert Skills**:
     * ⚖️ `ledger_reconciliation_review`: Core asset reconciliation (On-chain cash flows vs. Internal ledger registry).
     * 🛡️ `counterparty_risk_review`: Counterparty risk analysis (Exposure to unknown addresses, alerts on massive first-time outbound transfers).
     * 🔓 `approval_risk_review`: Token authorization audits (Unlimited allowance detection, unverified contract approvals, anomalous massive allowances).
3. **"AI Building AI" (SOP-to-Skill Conversion)**
   * A bespoke `skill_generator_basic` interface translates a security auditor's plain-language Standard Operating Procedure (SOP) into standard, ready-to-mount structured `.yaml` agent task definitions.
4. **Strictly Compliant Access & Environmental Isolation**
   * **Complete deprecation of basic API Keys.** Tailored for enterprise deployment and strictly regulated regions (e.g., Hong Kong, CN), the system solely relies on **Google Cloud Application Default Credentials (ADC)** connecting directly to Vertex AI.
   * Layered environment variables (`.env` -> `.env.local` -> `.env.vertex.local` -> Shell Env) safeguard credentials from being committed to version control.

---

## 🏛 Core Architecture & Components

The system is constructed based on an Onion Architecture pattern, focusing on LLM core communication and expanding outwards:

```text
HTTP API Layer (FastAPI) [Ingress]
  ├─ /v1/skills        -> Skill Management (CRUD)
  ├─ /v1/audit/run     -> Entrypoint for structured asset & transaction bridging
  ├─ /v1/agent/run     -> General plain-text parsing agent entry
  └─ /v1/runs          -> Check audit jobs, execution logs, and generated artifacts

Orchestrator Layer [Core Logic]
  ├─ Agent Context       -> Traces the entire Run Session, maintains logs
  ├─ Tool Factory        -> Binds SQLite, retrieval DBs. Safely registers local functions to LLM Tool Calling via type deduction (Annotation Wrapping)
  └─ Skill Executor      -> Payload validation -> Assembles Prompts -> Evaluates `output_schema` -> Dispatches LLM Request

LLM Provider Interface Layer
  ├─ Mock Client         -> High-speed unit test mode for local sandboxing (Zero cost)
  └─ Vertex AI Client    -> Leverages google-genai SDK combined with local GCP ADC & Region parameters

Storage & Knowledge Support Layer
  ├─ DB: SQLite          -> Persists `runs` (status), `tool_calls` (hook triggers), `skills` (dynamic updateable agents)
  └─ Mock Retrieval      -> Lightweight internal documentation recall (entity mapping, compromised wallet intel, compliance rules)
```

### Key Technical Decisions:
* **Why FastAPI**: Interlocks flawlessly with Pydantic V2 to support heavily typed data throughput and deliver unambiguous JSON Schema bindings to the LLM context.
* **Why Vertex ADC Verification**: Mandatory for maximum-security institutional deployments (or access in restricted zones like Hong Kong), preventing unauthorized invocation through local compromised standard API keys via Service Account validation.
* **Why Tool Factory Annotations Hijack (`functools.wraps`)**: When registering native generic functions to `gemini-2.5-flash` natively, metadata (`__annotations__`) is strictly required. Our wrapper proxies ensure no parameters get stripped during runtime mapping, eradicating dict `KeyError` crashes automatically.

---

## 🎯 Use Cases Detail

### Use Case 1: Institutional Asset Monthly Verification (Ledger Reconciliation)
**Background**: At the end of every month, an enterprise must verify that on-chain data for institutional whale accounts successfully correlates with their Centralized Ledger entries.
**Execution**:
1. A CRON Job scrapes this month's inbound/outbound transfers from internal DBs and Etherscan transaction lists.
2. Formats the data into an `AuditRunRequest` (`transactions`, `ledger_entries`, `balances`).
3. Dispatches the payload targeting the `ledger_reconciliation_review` skill to our FastAPI endpoint.
4. The Agent cross-references timestamp horizons, hashes, and amounts, detecting 2 specific trades that show "Internal Completion" but remain suspended on-chain.
5. Emits a structured standard `AuditReport` containing concrete Evidence References and Severity Markers for the accounting team review.

### Use Case 2: Sudden Black Swan / Unknown Counterparty Risk Sweeping
**Background**: Abnormal liquidity drains noticed in a hot wallet. SecOps needs an emergency risk matrix applied to the unknown recipient.
**Execution**:
1. The security operator batches the anomalous time window `TransactionRecord` inputs.
2. Triggers the `counterparty_risk_review` skill context.
3. The Agent autonomously triggers `mock_search` (the Enterprise Knowledge Base DB) searching for the address, concluding it is "untagged" internally.
4. Paired with direction-mapping logic, the Agent verifies it's a massive, uncollateralized one-way outflow to an origin-fresh address.
5. The Agent concludes with a Risk Level flag: `CRITICAL` immediately to halt further contract operations.

### Use Case 3: Pre-flight Check Before DeFi Interaction (Approval Risk)
**Background**: A Portfolio Manager wants to collateralize funds in a newly launched decentralized lending pool.
**Execution**:
1. System intercepts the imminent Approval Tx pending broadcast.
2. Evaluates the context using the `approval_risk_review` skill.
3. The Agent inspects variable bounds and discovers: Standard deducted quota reads `Unlimited (Type(uint256).max)`, drastically overexposing all holding volume.
4. Outputs remediations proposing: "Restrict Exact Allowance to current investment ticket size."

### Use Case 4: Business Analyst Writing a New Core Compliance Rule (SOP Translation)
**Background**: The Compliance Chief writes a text document titled "Multi-Sig Anti-Money Laundering (AML) Rules". They cannot code an Agent module.
**Execution**:
1. The Chief submits their original plain-text Word docs containing the business rules to the system utilizing the `skill_generator_basic` interface.
2. The Agent translates and dismantles these rules into rigid validation segments, generating a pristine `aml_multisig_audit` YAML template.
3. Persists directly into SQLite storage. After dev team sanity checking, the enterprise immediately inherited a brand-new internal systemic skill dynamically.

---

## 🚀 Quick Start Guide

### Prerequisites:
Python version `3.11` minimum required.

```bash
# Instantiate environment & dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Google Vertex AI ADC Configuration:
In highly regulated areas preventing arbitrary API usages, you must assign defaults specifically tied to your Google tenant bounds:
```bash
# Proceed through browser or terminal callback to authenticate standard scope credentials locally
gcloud auth application-default login

# Declare your default Vertex deployment attributes. Favor 'global' to avoid quota mismatches occasionally seen in smaller regions (e.g., asia-east2 limits)
export GOOGLE_CLOUD_PROJECT="your-google-project-id"
export GOOGLE_CLOUD_LOCATION="global"
```
Alternatively, insert this straight into a `.gitignore` restricted `.env.local` initialized in the root path. The bootstrapper maps it immediately.

### Development & Sandbox:

Leverage the embedded mock client. No Google environment is legally required to parse integration testing natively:

```bash
# Run mocked backend
LLM_MODE=mock uvicorn app.main:app --reload

# Execute safety unit tests:
python -m pytest -v
```

Using Real System Execution:

```bash
# Run Vertex backing
LLM_MODE=vertex uvicorn app.main:app --reload

# Run synthetic data injection testing
curl -X POST http://127.0.0.1:8042/v1/audit/run \
  -H 'Content-Type: application/json' \
  -d @examples/audit_request.json
```

---

## 🖥️ Web Console (React Frontend)

A flat, light-themed React SPA shipped under [`frontend/`](frontend/) gives every backend capability a UI: dashboard, skills library, structured audit submission, run history & replay, and the SOP→Skill generator.

### Stack
- Vite + React 18 + TypeScript
- Tailwind CSS (custom `brand` palette, indigo-based)
- TanStack Query for server state, React Router for navigation
- React Hook Form + Zod, react-markdown + remark-gfm, Sonner toasts, Lucide icons

### Prerequisites
- Node.js ≥ 18 (tested on 20 / 24)
- Backend running on `http://localhost:8042` (see Quick Start above)

### Run in development
```bash
cd frontend
npm install
npm run dev
# open http://localhost:5215
```
The dev server proxies `/api/*` to `http://localhost:8042` (see `frontend/vite.config.ts`), so no extra config is needed. To call the backend directly, copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL=http://localhost:8042`.

### Build for production
```bash
cd frontend
npm run build       # outputs to frontend/dist
npm run preview     # serves the build on :5215
```

### CORS
The FastAPI app enables `CORSMiddleware` for `http://localhost:5215` and `http://127.0.0.1:5215` by default. Override with the `CORS_ORIGINS` env var (comma-separated):
```bash
export CORS_ORIGINS="http://localhost:5215,https://audit.example.com"
```

### Pages
| Route | Backend endpoints | Purpose |
|---|---|---|
| `/` Dashboard | `GET /health`, `GET /v1/runs?limit=5`, `GET /v1/skills` | Health + recent runs + shortcuts |
| `/skills` | `GET /v1/skills` | Skill library card grid |
| `/skills/:id` | `GET /v1/skills/{id}` | System prompt, allowed tools, risk rules |
| `/audit/new` | `POST /v1/audit/run` | Structured form + JSON editor + “load example” |
| `/runs` | `GET /v1/runs` | Full run history table |
| `/runs/:runId` | `GET /v1/runs/{id}` | AuditReport / Markdown / Tool-call timeline / raw payload |
| `/skills/new` | `POST /v1/skills/generate`, `POST /v1/skills/save` | SOP→Skill draft & persist |

---

## 🔑 Invite-Code Gate (write endpoints)

To prevent anonymous traffic from draining your LLM quota when the API is exposed on the public internet, every **mutating** endpoint requires an `X-Invite-Code` header. Read endpoints (`GET /health`, `GET /v1/skills`, `GET /v1/runs`, …) remain open.

**Hard-coded valid codes** (see [`app/api/auth.py`](app/api/auth.py)):

```
Chrissy
Ethan
```

Protected routes:

| Method | Path |
|---|---|
| POST | `/v1/audit/run` |
| POST | `/v1/agent/run` |
| POST | `/v1/skills/generate` |
| POST | `/v1/skills/save` |

Missing or wrong code → HTTP `401 {"detail": "invalid_invite_code"}`.

**Frontend**: open the UI, click the *邀请码* badge in the top-right, paste a valid code. It is persisted in `localStorage` and auto-attached to every non-GET request by the axios interceptor.

**curl example**:

```bash
curl -X POST http://127.0.0.1:8042/v1/audit/run \
  -H 'Content-Type: application/json' \
  -H 'X-Invite-Code: Chrissy' \
  -d @examples/audit_request.json
```

> Treat this as a lightweight deterrent, not real authentication. For a true production deployment, put the API behind a reverse proxy with proper auth, or replace the hard-coded list with a managed secret.

---

## ☁️ One-Click Cloud Deployment

For a fresh Ubuntu/Debian cloud server with nothing pre-installed, two scripts under [`scripts/`](scripts/) handle everything. Default ports are **8042** (backend) and **5215** (frontend) so they coexist with other web services on common ports.

### 1. Bootstrap (install everything)

```bash
bash scripts/bootstrap.sh
```

What it does (idempotent):

1. `apt-get` installs Python 3.11+, build tools, `curl`, `git`. Falls back to the deadsnakes PPA if the distro Python is too old.
2. Installs Node.js 20.x via NodeSource (only if missing or `< 18`).
3. Creates `.venv/` and runs `pip install -e ".[dev]"`.
4. Runs `npm ci` (or `npm install`) and `npm run build` inside `frontend/`.
5. Writes `.env` (backend, mock LLM mode) and `frontend/.env.local` (`VITE_API_BASE_URL=http://localhost:8042`) if missing.

Override ports:
```bash
BACKEND_PORT=18042 FRONTEND_PORT=15215 bash scripts/bootstrap.sh
```

### 2. Deploy (start / stop / status / logs)

```bash
bash scripts/deploy.sh           # start (default) — both services in background
bash scripts/deploy.sh status
bash scripts/deploy.sh logs backend     # tail -F backend log
bash scripts/deploy.sh logs frontend
bash scripts/deploy.sh restart
bash scripts/deploy.sh stop
```

- Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8042` (PID + log under `.run/`).
- Frontend: `python3 -m http.server 5215 --directory frontend/dist --bind 0.0.0.0` (zero extra deps).

After `start`, open:

- UI: `http://<server-ip>:5215`
- API docs: `http://<server-ip>:8042/docs`

> Remember to open inbound TCP **8042** and **5215** in your cloud security group / firewall.

For production with Vertex AI:

1. Edit `.env` (or use `.env.local` / `.env.vertex.local`):
   ```
   LLM_MODE=vertex
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=global
   ```
2. Run `gcloud auth application-default login` on the server (or mount a service-account key).
3. `bash scripts/deploy.sh restart`.

