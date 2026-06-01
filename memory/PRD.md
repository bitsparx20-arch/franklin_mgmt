# Franklin Wardcorpp CRM — PRD

## Problem Statement
Full-stack Sales Intelligence & Employee Management Platform with 9 modules: Visit Tracking, POC + Follow-up System, Kanban Deal Pipeline, Product Catalogue & Billing Engine, Sales Performance Tracker, CEO/Admin Dashboard, Employee Management, Reminders & Notifications, Reports & Exports.

## Architecture
- **Frontend**: React 19 + Tailwind + Shadcn/UI · Chivo + IBM Plex Sans + JetBrains Mono · recharts · dnd-kit (Kanban) · react-leaflet (map) · jsPDF + SheetJS (exports) · sonner toasts
- **Backend**: FastAPI · Motor + MongoDB · PyJWT + bcrypt · UUID ids
- **Auth**: JWT (Bearer + httpOnly cookie). Roles: CEO > Admin > Sales Manager > Salesperson
- **Integrations**: MOCKED SpringEdge SMS/WhatsApp (logged to `db.sms_logs`)

## User Personas
- **CEO** — sees everything, drill-downs across team
- **Admin** — manages products, can seed managers/salespeople
- **Sales Manager** — sees own team's visits/deals/bills + receives overdue escalations
- **Salesperson** — field user; logs visits, captures POCs, manages own pipeline + bills

## Core Requirements (static)
- Role-based data scoping (sp → self; manager → team; admin/ceo → all)
- GST-compliant invoice generation + PDF export
- Drag-and-drop Kanban with 6 stages
- Color-coded follow-ups (red/amber/green) + auto-escalation
- Per-salesperson target vs actual + conversion rate (≥80 green, ≥50 amber, <50 red)
- Live agent map from last visit GPS
- 12-month rolling revenue trend chart
- PDF + Excel exports of all major datasets

## Implemented (Feb 2026)
- Auth (login/logout/me) + 5 seeded demo accounts
- Employees CRUD with role hierarchy enforcement
- Visit Tracking with browser GPS (mobile-friendly card layout)
- POC capture + linked follow-up scheduling
- Follow-ups with action logs + overdue escalation
- Kanban Pipeline (6 stages) with drag-drop, filters, touchpoints
- Product Catalogue CRUD
- Bills with GST + discount + needs-approval flag + **beautified jsPDF invoice** (header band, status pill, grand-total accent, footer)
- Sales Performance per salesperson + top/under panels + comparison chart
- Dashboard: KPIs, pipeline-by-stage bar, funnel, 12-month trend, top products, performance cards
- **Enhanced Live Agent Map**: shows ALL salespeople + managers; colored DivIcons by source (visit/ping/default); legend; auto-fit bounds; **timestamp-based precedence** (newer ping overrides older visit GPS)
- **Ping My Location** button for salespeople — broadcasts GPS without needing a visit
- **Franklin-AI Chatbot** (Claude Sonnet 4.5 via Emergent Universal LLM key) — floating FAB for CEO/Admin/Manager with quick prompts, multi-turn sessions, live CRM context injection
- In-app notifications + MOCKED SpringEdge channel
- Reports & Exports (Visits / Bills / Pipeline / POCs) as PDF + Excel
- **Executive Snapshot PDF**: 4-page beautifully formatted report — cover, KPI grid, conversion funnel, pipeline by stage, top performers, target-vs-actual bars, 12-month revenue trend chart, top products, recent invoices
- Dark/light theme toggle · Mobile responsive (sidebar → hamburger sheet, table → cards)

## Prioritized Backlog
### P0 (next iteration)
- Real SpringEdge wiring once API key provided
- Scope checks on PATCH/DELETE deals + GET user-by-id
- Brute-force lockout (5 attempts → 15min)

### P1
- WhatsApp templates with media for follow-ups
- Excel import for products/employees
- Manager approval workflow for discounted bills
- Email digests (daily/weekly)

### P2
- Salesperson mobile PWA install banner
- Custom report builder
- Goal-setting workflow + quarterly OKRs
- Voice-note attachments on visits

## Test Credentials
See `/app/memory/test_credentials.md`
