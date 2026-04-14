# PROMETHEUS — Adversarial Venture Engine

> **AI that builds a company, attacks it with 5 specialized critics, and ships the survivor.**

---

## What It Does

PROMETHEUS is a fully autonomous venture engine that runs this pipeline on every mission:

1. **GENESIS** — You type a plain-English business problem. Claude claude-sonnet-4-6 generates a complete company blueprint: company name, tech stack, database schema, API endpoints, pricing, compliance requirements.

2. **CONSTRUCTION** — 4 AI sub-agents run in parallel to generate a complete MVP codebase: Next.js frontend, FastAPI backend, SQL migrations, and full documentation.

3. **ATTACK** — 5 specialized critic agents simultaneously assault the generated company from every angle:
   - 🔴 **THE BREACH** — Security penetration tester (SQL injection, auth bypass, IDOR, CSRF)
   - 🟣 **THE ADVOCATE** — Product UX expert (missing onboarding, empty states, dead ends)
   - 🟡 **THE REGULATOR** — Compliance officer (GDPR, PCI-DSS, HIPAA, CCPA violations)
   - 🔵 **THE ARCHITECT** — Scalability engineer (N+1 queries, missing pagination, SPOFs)
   - 🩷 **THE INVESTOR** — VC partner (unit economics, moat, go-to-market, pricing cannibalization)

4. **DEFENSE** — An autonomous loop processes every kill report. High-severity threats are patched immediately. Low-severity threats are challenged and sent to an arbiter (Claude) who rules ACCEPTED or REJECTED. A live Survival Score (0–100%) rises as threats are resolved.

5. **DEPLOY** — When the defense loop completes, the survivor is deployed and you receive a live URL. Click it to see a working company landing page.

---

## Quickstart (3 Commands)

```bash
# 1. Clone and enter
git clone <your-repo-url> prometheus && cd prometheus

# 2. Add your Google Gemini API key
cp backend/.env.example backend/.env
# Edit backend/.env and set GEMINI_API_KEY=AIza...

# 3. Run
start.bat        # Windows
./start.sh       # Mac/Linux
```

Then open **http://localhost:3000**

---

## Requirements

- Python 3.11+
- Node.js 18+
- A Google Gemini API key (free tier works perfectly!): https://aistudio.google.com/app/apikey

---

## Tech Stack

### PROMETHEUS Engine (This App)
| Layer | Technology |
|---|---|
| Backend | FastAPI 0.110 + Python 3.11 |
| AI Model | Gemini (e.g., 1.5 Flash) via Google GenAI SDK |
| Agent Framework | LangGraph 0.1.0 |
| Data Models | Pydantic v2 |
| Streaming | Server-Sent Events (SSE) |
| Storage | In-memory (missions) |
| Frontend | Next.js 14 + TypeScript |
| Styling | CSS Modules (military aesthetic) |
| Fonts | Rajdhani + Share Tech Mono + Orbitron |

### Generated Applications (What PROMETHEUS Builds)
| Layer | Technology |
|---|---|
| Frontend | Next.js 14 + TypeScript + Tailwind |
| Backend | FastAPI + Python |
| Database | SQLite + SQLAlchemy |
| Auth | JWT |
| Docs | Markdown |

---

## Architecture

```
User Input
    │
    ▼
[BUILDER AGENT] ──── Claude claude-sonnet-4-6 ───→ SharedContract (Company Blueprint)
    │
    ├── [FRONTEND AGENT] ──── Claude ──→ Next.js App Files
    ├── [BACKEND AGENT]  ──── Claude ──→ FastAPI App Files
    ├── [DATABASE AGENT] ──── Claude ──→ SQL Migration Files
    └── [DOCS AGENT]     ──── Claude ──→ README + API Docs
    │
    ▼
[CRITIC COUNCIL] ── 5 agents run in parallel ──
    ├── [THE BREACH]     Security vulnerabilities
    ├── [THE ADVOCATE]   Product UX gaps
    ├── [THE REGULATOR]  Compliance violations
    ├── [THE ARCHITECT]  Scalability bottlenecks
    └── [THE INVESTOR]   Business model flaws
    │
    ▼
[DEFENSE LOOP] ──── For each KillReport:
    ├── kill_potential ≥ 7 → PATCH (immediate fix)
    ├── kill_potential ≤ 3 → CHALLENGE → [ARBITER] → ACCEPTED/REJECTED
    └── kill_potential 4-6 → PATCH
    │
    ▼
[DEPLOYER] ──→ Live Preview URL
```

---

## Cost

**$0** to run. Here's the breakdown:

| Service | Cost |
|---|---|
| Gemini API | Free tier works for development (up to 15 Requests/Min, 1 million Tokens/Min) |
| Backend hosting | Fly.io free tier OR localhost |
| Frontend hosting | Vercel free tier OR localhost |
| Database | SQLite (local file, zero cost) |

For demo purposes, everything runs locally with zero cloud costs.

---

## Demo Script (6 Minutes)

Use this for live judging demos:

**0:00** — Open http://localhost:3000. Show the military war room aesthetic. Point out the 5 armed critic agents.

**0:30** — Type: *"A freelance invoicing tool with time tracking and automated payment reminders"*. Click INITIATE MISSION.

**0:45** — Navigate to the Mission HUD. Point out: 3-column layout, Phase Tracker (left), Survival Meter (center), Threat Intelligence feed (right).

**1:00** — Watch GENESIS: The company name appears live. Point out the combat log streaming in real-time.

**2:00** — Watch CONSTRUCTION: 4 parallel agents building the codebase. Show the file count ticking up.

**3:00** — Watch ATTACK: Kill reports start appearing in the right column. Point out severity levels. Survival score starts dropping. "CRITICAL open threats = -15% each."

**4:00** — Watch DEFENSE: Reports flip from OPEN to PATCHED or CHALLENGED. Score climbs. Point out the arbiter dismissing low-threat items.

**5:00** — Score hits 100%. DEPLOY button unlocks, glows green. Click DEPLOY SURVIVOR.

**5:30** — Live URL appears. Click it. Show a polished landing page for the generated company — complete with features, pricing, badges.

**6:00** — "PROMETHEUS built, attacked, defended, and deployed a complete company in under 6 minutes. Zero human code written."

---

## Team

Add your team members here.

---

## License

MIT License — build anything with it.

---

*Built for hackathons, demos, and anyone who wants to watch AI eat startups for breakfast.*
