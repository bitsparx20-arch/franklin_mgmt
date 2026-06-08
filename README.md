# Franklin Wardcorpp CRM

Field-sales CRM: visits, POCs, follow-ups, Kanban pipeline, GST billing, performance analytics, live agent map, and AI assistant (when configured).

## Prerequisites

- **Python 3.11+** (3.13 works for core deps)
- **Node.js 18+** and npm
- **MongoDB** running locally (`mongodb://localhost:27017`) — the MongoDB Windows service is usually enough

## Quick start (Windows)

### 1. Environment files

Copy the examples (or use the `.env` files already created locally):

```powershell
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

| Variable | Purpose |
|----------|---------|
| `MONGO_URL` | MongoDB connection string |
| `DB_NAME` | Database name (`franklin_crm`) |
| `JWT_SECRET` | Auth signing secret |
| `REACT_APP_BACKEND_URL` | API base without `/api` (e.g. `http://localhost:8000`) |
| `LLM_PROVIDER` | `bedrock` (default if `BEDROCK_MODEL_ID` set) or `emergent` |
| `BEDROCK_MODEL_ID` | AWS Bedrock model ID for Franklin-AI chat |
| `AWS_REGION` | AWS region where Bedrock is enabled (e.g. `us-east-1`) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | IAM credentials with `bedrock:InvokeModel` |

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install fastapi uvicorn python-dotenv pymongo motor pydantic email-validator pyjwt bcrypt python-multipart
.\.venv\Scripts\uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

On first start the API seeds a CEO account, demo users, products, and rich sample CRM data (visits, pipeline, bills, etc.).

### Refresh demo data (existing database)

```powershell
cd backend
.\.venv\Scripts\python seed_demo.py
```

Or as CEO/admin via API: `POST http://localhost:8000/api/dev/seed-demo-data?replace=true` (Bearer token required).

### 3. Frontend

**Option A — production build + static server (most reliable on OneDrive paths):**

```powershell
cd frontend
npm install --legacy-peer-deps
npm install ajv@8 --legacy-peer-deps
npm run build
npx serve -s build -l 3000
```

**Option B — dev server:**

```powershell
cd frontend
$env:BROWSER = "none"
npm start
```

If `npm start` exits immediately, use Option A or set `WATCHPACK_POLLING=true`.

Open **http://localhost:3000**

## Demo logins

| Role | Email | Password |
|------|-------|----------|
| CEO — Vivek Wadhwa | `ceo@franklinwardcorpp.com` | `ceo12345` |
| CEO — OM Wadhwa | `om.wadhwa@franklinwardcorpp.com` | `ceo12345` |
| National Sales Head — Joe Jacob | `manager@franklinwardcorpp.com` | `manager123` |
| South — Swapnil | `swapnil@franklinwardcorpp.com` | `sales123` |
| East — ChiroDeep | `chirodeep@franklinwardcorpp.com` | `sales123` |
| North — Manish | `manish@franklinwardcorpp.com` | `sales123` |
| West — Thomas Philip | `thomas.philip@franklinwardcorpp.com` | `sales123` |
| Admin (ops) | `admin@franklinwardcorpp.com` | `admin123` |

## Feature map

| UI module | API | Notes |
|-----------|-----|-------|
| Dashboard | `/dashboard/*` | KPIs, charts, agent map, GPS ping |
| Visits | `/visits` | GPS capture on new visit |
| POCs | `/pocs` | Contact records |
| Follow-ups | `/followups` | Log actions; escalate overdue (manager+) |
| Broadcast | `/messaging/broadcast` | SMS + WhatsApp to POC contacts (SpringEdge / PinBot) |
| Pipeline | `/deals` | Drag-and-drop Kanban stages |
| Products | `/products` | Admin/CEO CRUD |
| Bills | `/bills` | GST invoicing from product catalog |
| Performance | `/dashboard/performance` | Manager+ |
| Employees | `/users` | Manager+ user management |
| Reports | `/reports/*` | PDF/Excel exports |
| AI chat (FAB) | `/ai/ask` | AWS Bedrock (`LLM_PROVIDER=bedrock`) or Emergent legacy |
| Notifications | `/notifications` | Header bell |

**SpringEdge** powers SMS and WhatsApp. SMS uses `web.springedge.com`; WhatsApp uses the PinBot API (`partnersv1.pinbot.ai`) per `WhatsApp_API_Pinned_Documentation.pdf`. Set in `backend/.env`:

- SMS: `SPRINGEDGE_API_KEY`, `SPRINGEDGE_SENDER_ID`
- WhatsApp: `SPRINGEDGE_WABA_API_KEY` (or same API key), `SPRINGEDGE_PHONE_NUMBER_ID`

Use the **Broadcast** tab in the app or `POST /api/messaging/broadcast`. Without keys, messages are logged only (mock mode).

## API docs

With the backend running: **http://localhost:8000/docs**

## Deploy to KVM / VPS (e.g. `194.238.19.53`)

Production layout: **nginx** serves the React build and proxies `/api` → **uvicorn** on `127.0.0.1:8000`, with **MongoDB** on the same host.

### 1. Allow SSH from your machine (one-time)

Your local public key (add via hosting panel KVM console if SSH password is awkward):

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

On the server as `root`:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo 'PASTE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 2. Deploy from Windows

From the repo root (will prompt for SSH password if no key is authorized):

```powershell
.\deploy\deploy-from-windows.ps1 -Server root@194.238.19.53
```

This installs MongoDB, Node 20, nginx, builds the frontend, and starts `franklin-backend` via systemd. Your local `backend/.env` is copied to the server (not committed to git).

### 3. Verify

- App: **http://194.238.19.53/**
- API docs: **http://194.238.19.53/docs**
- Logs: `ssh root@194.238.19.53 journalctl -u franklin-backend -f`

Re-deploy after code changes: run the same `deploy-from-windows.ps1` command again (add `-SkipBootstrap` after the first run).

## Troubleshooting

- **Login fails / network error** — Confirm backend on port 8000 and `REACT_APP_BACKEND_URL` matches (rebuild frontend after changing `.env`).
- **Empty dashboard** — Log in as CEO or run backend once to seed data; or create visits/deals as a salesperson.
- **AI chat errors** — Configure AWS Bedrock in `backend/.env` (see below). Check `GET /api/ai/status` while logged in as CEO/Admin/Manager.

### AWS Bedrock (Franklin-AI)

1. In [AWS Bedrock console](https://console.aws.amazon.com/bedrock/), enable **model access** for your chosen model (e.g. Claude 3.5 Sonnet).
2. Create an IAM user or role with `bedrock:InvokeModel` on that model.
3. Add to `backend/.env` (long-term API key — easiest):

```env
LLM_PROVIDER=bedrock
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_API_KEY=paste-your-long-term-key-here
```

Get the key: Bedrock console → **Discover** → **API keys** → **Long-term API keys** → Generate.

4. Restart the backend, then test:

```powershell
cd backend
.\.venv\Scripts\python test_bedrock_llm.py
```

**Alternatively**, use IAM access keys (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`) instead of `BEDROCK_API_KEY`.
- **MongoDB connection** — Ensure the MongoDB service is running: `Get-Service MongoDB`
