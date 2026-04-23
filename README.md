# Conversion Engine
### Automated Lead Generation and Conversion System for Tenacious Consulting and Outsourcing
 
**Trainee:** Zemzem Hibet
**Week:** 10 — The Conversion Engine Challenge
**Date:** April 2026
 
---
 
## What This System Does
 
The Conversion Engine finds companies that match Tenacious's ideal customer profile, researches them using public data, writes personalized outreach emails grounded in verifiable signals, logs everything to HubSpot, and books discovery calls automatically.
 
The core insight: qualification is the filter, research is the value proposition. Every email the system sends arrives with a specific, verifiable finding about the prospect — not a generic pitch.
 
---
 
## Architecture
 
```
Crunchbase ODM (1000 companies)
RemoteOK Job Posts
layoffs.fyi CSV
          │
          ▼
┌─────────────────────────┐
│   Enrichment Pipeline   │
│  crunchbase.py          │
│  job_posts.py           │
│  layoffs.py             │
│  ai_maturity.py         │
│  competitor_gap.py      │
│  pipeline.py            │
└────────────┬────────────┘
             │ hiring_signal_brief.json
             │ competitor_gap_brief.json
             ▼
┌─────────────────────────┐
│     ICP Classifier      │
│  Segment 1: Series A/B  │
│  Segment 2: Restructure │
│  Segment 3: New CTO     │
│  Segment 4: AI Gap      │
│  Abstain: low confidence│
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│      Email Agent        │
│  email_handler.py       │
│  ← style_guide.md       │
│  ← bench_summary.json   │
│  Tone check (5 markers) │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐     ┌──────────────┐
│   Resend (Email out)    │────▶│   HubSpot    │
│   Africa's Talking SMS  │     │   CRM + Note │
│   Cal.com Booking       │     └──────────────┘
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Langfuse Tracing      │
│  Per-step latency       │
│  Cost attribution       │
│  Full trace logging     │
└─────────────────────────┘
```
 
---
 
## Repository Structure
 
```
conversion-engine/
├── agent/
│   ├── __init__.py
│   ├── email_handler.py       # Resend integration + tone check
│   ├── orchestrator.py        # End-to-end flow orchestrator
│   └── sms_handler.py         # Africa's Talking integration
├── enrichment/
│   ├── __init__.py
│   ├── ai_maturity.py         # AI maturity scoring (0-3)
│   ├── competitor_gap.py      # Top-quartile gap analysis
│   ├── crunchbase.py          # Firmographic lookup
│   ├── job_posts.py           # RemoteOK job scraping
│   ├── layoffs.py             # layoffs.fyi parser
│   └── pipeline.py            # Main enrichment orchestrator
├── integrations/
│   ├── __init__.py
│   ├── cal_com.py             # Cal.com v2 booking
│   └── hubspot.py             # HubSpot CRM integration
├── eval/
│   ├── score_log.json         # τ²-Bench scores with 95% CI
│   ├── trace_log.jsonl        # Full τ²-Bench trajectories
│   └── baseline.md            # Act I baseline writeup
├── data/
│   ├── crunchbase_sample.json # 1000 company ODM sample
│   └── layoffs.csv            # layoffs.fyi snapshot
├── outputs/
│   ├── traces/                # Per-prospect flow traces
│   ├── hiring_signal_brief_*.json
│   └── competitor_gap_brief_*.json
├── seeds/
│   └── seed/
│       ├── icp_definition.md
│       ├── style_guide.md
│       ├── bench_summary.json
│       ├── pricing_sheet.md
│       ├── baseline_numbers.md
│       └── email_sequences/
├── tests/
│   ├── test_end_to_end.py
│   ├── test_batch.py
│   ├── test_email_agent.py
│   ├── test_hubspot_enrichment.py
│   ├── test_calcom.py
│   └── test_langfuse.py
├── main.py                    # FastAPI webhook server
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```
 
---
 
## Setup Instructions
 
### 1. Clone and create virtual environment
```bash
git clone https://github.com/YOUR_USERNAME/conversion-engine.git
cd conversion-engine
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```
 
### 2. Configure environment variables
```bash
cp .env.example .env
nano .env
```
 
Fill in all required keys (see `.env.example` for full list).
 
### 3. Install Playwright browsers
```bash
playwright install chromium
```
 
### 4. Start the webhook server
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn main:app --port 8000
```
 
### 5. Start ngrok tunnel (for local development)
```bash
ngrok http --domain=YOUR_STATIC_DOMAIN.ngrok-free.dev 8000
```
 
---
 
## Running the System
 
### Run a single prospect end-to-end
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python tests/test_end_to_end.py
```
 
### Run 20 synthetic prospects (batch)
```bash
python tests/test_batch.py
```
 
### Run enrichment pipeline only
```bash
python -m enrichment.pipeline
```
 
### Run τ²-Bench baseline
```bash
cd ../tau2-bench
uv run tau2 run \
  --domain retail \
  --agent-llm openrouter/qwen/qwen3-235b-a22b \
  --user-llm openrouter/qwen/qwen3-235b-a22b \
  --num-trials 5 \
  --num-tasks 30
```
 
---
 
## Production Stack
 
| Layer | Tool | Status |
|---|---|---|
| Email (primary) | Resend free tier | ✅ Live |
| SMS (secondary) | Africa's Talking sandbox | ✅ Live |
| CRM | HubSpot Developer Sandbox | ✅ Live |
| Calendar | Cal.com Cloud (v2 API) | ✅ Live |
| Observability | Langfuse cloud free tier | ✅ Live |
| Evaluation | τ²-Bench retail domain | ✅ Live |
| LLM dev tier | OpenRouter Qwen3-235B | ✅ Live |
| LLM eval tier | Claude Sonnet 4.6 | Configured |
| Enrichment | Playwright + requests | ✅ Live |
 
---
 
## Environment Variables
 
```bash
# Email
RESEND_API_KEY=re_...
 
# SMS
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=atsk_...
 
# CRM
HUBSPOT_ACCESS_TOKEN=...
 
# Calendar
CALCOM_API_KEY=cal_live_...
CALCOM_EVENT_TYPE_ID=...
 
# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
 
# Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
 
# Kill switch
DRY_RUN=true
```
 
---
 
## Act I Results — τ²-Bench Baseline
 
| Metric | Value |
|---|---|
| Domain | Retail |
| Model | openrouter/qwen/qwen3-235b-a22b |
| Tasks | 30 |
| Trials | 5 |
| Evaluated simulations | 147 |
| **pass@1** | **0.268** |
| 95% CI | [0.195, 0.341] |
| Published reference | ~0.42 |
| Delta vs reference | -0.152 |
| Cost per run | $0.00 (free tier model) |
 
---
 
## Act II Results — Production Stack
 
| Metric | Value |
|---|---|
| Total prospects tested | 20 |
| **p50 latency** | **3.52s** |
| **p95 latency** | **4.54s** |
| Min latency | 2.60s |
| Max latency | 4.54s |
| Average tone score | 5.0/5 |
| Tone violations | 0 |
| Abstain rate | 45% (9/20) |
| Human baseline (median) | 42 minutes |
| **Speedup factor** | **715×** |
 
### Segment distribution across 20 prospects
| Segment | Count |
|---|---|
| Segment 4 (specialized capability) | 11 |
| Abstain (low confidence) | 9 |
 
---
 
## Key Design Decisions
 
**Rule-based email composition (no LLM for outreach)**
Email composition uses deterministic rules from the hiring signal brief and ICP definition. This eliminates LLM cost per email, ensures tone consistency, and makes the system auditable. The honesty constraint is enforced structurally — the composer cannot assert claims not present in the brief.
 
**Confidence-gated segment classification**
Prospects with segment confidence below 0.6 receive a generic exploratory email rather than a segment-specific pitch. This prevents the most damaging failure mode — sending the wrong pitch to a prospect who clearly doesn't match.
 
**Bench-to-brief match gating**
The system checks `bench_summary.json` before composing any outreach. If the prospect's required stacks are not available, the agent flags this in the context brief rather than over-committing capacity.
 
**Tone preservation check**
Every email draft is scored against the 5 Tenacious tone markers (Direct, Grounded, Honest, Professional, Non-condescending) before sending. Drafts with violations are flagged.
 
---
 
## Kill Switch
 
Set `DRY_RUN=true` in `.env` to route all outbound emails to the staff sink instead of real prospects. This is the default — the system must be explicitly switched to live mode.
 
To verify kill switch is active:
```bash
grep DRY_RUN .env
# Should show: DRY_RUN=true
```
 
---
 
## Data Handling
 
- All prospect interactions during the challenge week use synthetic profiles
- No real Tenacious customer data is stored in this repository
- Seed materials (sales deck, pricing, case studies) are excluded from git via `.gitignore`
- All outbound during testing routes to staff-controlled sink
---
 
## Inheriting This Codebase
 
**For the engineer who takes this over:**
 
1. Read `seeds/seed/icp_definition.md` before changing any segment logic
2. Read `seeds/seed/style_guide.md` before changing any email templates
3. Never modify `bench_summary.json` manually — it updates weekly from Tenacious ops
4. The `segment_confidence` threshold (currently 0.6 for abstain, 0.75 for booking) is the primary quality lever — lower it to increase volume, raise it to increase precision
5. All numeric claims in `eval/` trace back to τ²-Bench simulation files — do not edit these manually
6. The kill switch (`DRY_RUN`) must be explicitly set to `false` before any live deployment — default is always `true`
---
 
## Known Limitations (Act II)
 
- `layoffs.fyi` CSV not yet auto-downloaded — returning no layoff signal by default
- Leadership change detection uses mock data — Crunchbase People API not yet integrated
- Job post velocity uses RemoteOK only — Wellfound and LinkedIn blocked by Cloudflare
- Cal.com booking fires only at confidence ≥ 75% — most synthetic prospects score 70%

These are addressed in Acts III and IV.
 
