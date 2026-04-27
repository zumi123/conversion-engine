# Conversion Engine
### Automated Lead Generation and Conversion System for Tenacious Consulting and Outsourcing

**Challenge:** Week 10 — The Conversion Engine
**Submission:** Interim (Acts I and II)
**Date:** April 23, 2026

---

## What This System Does

The Conversion Engine finds companies that match Tenacious's ideal customer profile, researches them using public data, writes personalized outreach emails grounded in verifiable signals, logs everything to HubSpot, and books discovery calls automatically.

The core insight: **qualification is the filter, research is the value proposition.** Every email the system sends arrives with a specific, verifiable finding about the prospect — not a generic pitch.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  DATA SOURCES                       │
│  Crunchbase ODM (1000 companies)                    │
│  RemoteOK Job Posts (Playwright + API)              │
│  layoffs.fyi CSV                                    │
│  Leadership change detection                        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              ENRICHMENT PIPELINE                    │
│  enrichment/crunchbase.py   → firmographics         │
│  enrichment/job_posts.py    → hiring velocity       │
│  enrichment/layoffs.py      → cost pressure signal  │
│  enrichment/ai_maturity.py  → AI maturity (0-3)     │
│  enrichment/competitor_gap.py → top-quartile gap    │
│  enrichment/pipeline.py     → orchestrates all      │
│                                                     │
│  Output: hiring_signal_brief.json                   │
│          competitor_gap_brief.json                  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              ICP CLASSIFIER                         │
│  Segment 1: Recently-funded Series A/B              │
│  Segment 2: Mid-market restructuring                │
│  Segment 3: New CTO/VP Engineering                  │
│  Segment 4: Specialized capability gap              │
│  Abstain:   confidence < 0.6                        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│               EMAIL AGENT                           │
│  agent/email_handler.py                             │
│  <- seeds/seed/style_guide.md (5 tone markers)     │
│  <- seeds/seed/bench_summary.json (capacity gate)  │
│  <- seeds/seed/icp_definition.md (segment rules)   │
│                                                     │
│  Tone check: Direct, Grounded, Honest,              │
│              Professional, Non-condescending        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────┬────────────────┬─────────────────────┐
│   CHANNEL 1  │   CHANNEL 2    │   CHANNEL 3         │
│   (Primary)  │   (Secondary)  │   (Final)           │
│              │                │                     │
│   Resend     │  Africa's      │   Cal.com           │
│   Email      │  Talking SMS   │   Discovery Call    │
│              │  (warm leads   │   (booked by agent  │
│              │   only - gated │   delivered by      │
│              │   on email     │   human lead)       │
│              │   reply)       │                     │
└──────┬───────┴────────────────┴──────────┬──────────┘
       │                                   │
       ▼                                   ▼
┌─────────────────────────────────────────────────────┐
│                   HUBSPOT CRM                       │
│  Write 1: Contact + ICP segment + enrichment data   │
│  Write 2: Booking reference (after Cal.com books)   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                   LANGFUSE                          │
│  Per-step latency tracking                          │
│  Cost attribution                                   │
│  Full trace logging with trace IDs                  │
└─────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
conversion-engine/
│
├── agent/
│   ├── __init__.py
│   ├── email_handler.py       # Resend integration, tone check,
│   │                          # downstream reply handler
│   ├── orchestrator.py        # End-to-end flow orchestrator
│   │                          # with Langfuse tracing
│   └── sms_handler.py         # Africa's Talking integration
│                              # Channel hierarchy enforcement
│
├── enrichment/
│   ├── __init__.py
│   ├── ai_maturity.py         # AI maturity scoring (0-3)
│   │                          # 6-signal rubric with confidence
│   ├── competitor_gap.py      # Top-quartile gap analysis
│   ├── crunchbase.py          # Crunchbase ODM firmographic lookup
│   ├── job_posts.py           # Playwright + RemoteOK job scraping
│   │                          # No login logic anywhere
│   ├── layoffs.py             # layoffs.fyi CSV parser
│   └── pipeline.py            # Main enrichment orchestrator
│                              # produces hiring_signal_brief.json
│
├── integrations/
│   ├── __init__.py
│   ├── cal_com.py             # Cal.com v2 API booking
│   └── hubspot.py             # HubSpot CRM (two writes per prospect)
│
├── eval/
│   ├── baseline.md            # Official facilitator baseline
│   ├── baseline_self_run.md   # Self-run reference (Qwen3 free tier)
│   ├── score_log.json         # Official facilitator score log
│   ├── score_log_self_run.json# Self-run score log
│   ├── trace_log.jsonl        # Official facilitator traces (159 sims)
│   ├── trace_log_self_run.jsonl # Self-run traces
│   └── act2_metrics.json      # Act II latency and quality metrics
│
├── data/
│   ├── crunchbase_sample.csv  # 1000 company ODM sample (raw)
│   ├── crunchbase_sample.json # 1000 company ODM sample (parsed)
│   └── job_posts_test.json    # Job post scrape snapshot
│
├── outputs/
│   ├── hiring_signal_brief_*.json   # Per-prospect enrichment briefs
│   ├── competitor_gap_brief_*.json  # Per-prospect gap analysis
│   ├── batch_results.json           # 20-prospect batch run results
│   └── traces/                      # Per-prospect flow traces
│       └── trace_*.json
│
├── seeds/                     # Tenacious confidential materials
│   └── (excluded from git - see seeds/README.md)
│
├── tests/
│   ├── test_end_to_end.py     # Single prospect full flow test
│   ├── test_batch.py          # 20-prospect batch test
│   ├── test_email_agent.py    # Email composition + tone check
│   ├── test_email.py          # Resend send test
│   ├── test_hubspot.py        # HubSpot contact creation test
│   ├── test_hubspot_enrichment.py # HubSpot with brief test
│   ├── test_calcom.py         # Cal.com booking test
│   ├── test_langfuse.py       # Langfuse trace test
│   └── test_sms.py            # Africa's Talking SMS test
│
├── main.py                    # FastAPI webhook server
│                              # /webhooks/resend (email replies)
│                              # /webhooks/sms (inbound SMS)
├── README.md
├── requirements.txt
├── .env.example               # Environment variable template
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
# Fill in all required keys
```

### 3. Install Playwright browsers
```bash
playwright install chromium
```

### 4. Add seed materials
Obtain from program staff and place in `seeds/seed/`:
- `icp_definition.md`
- `style_guide.md`
- `bench_summary.json`
- `pricing_sheet.md`
- `baseline_numbers.md`
- `email_sequences/`
- `discovery_transcripts/`

### 5. Start the webhook server
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn main:app --port 8000
```

### 6. Start ngrok tunnel (local development)
```bash
ngrok http --domain=YOUR_DOMAIN.ngrok-free.dev 8000
```

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

# Kill switch - default must be true
DRY_RUN=true
```

---

## Running the System

### Single prospect end-to-end
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python tests/test_end_to_end.py
```

### 20-prospect batch run
```bash
python tests/test_batch.py
```

### Enrichment pipeline only
```bash
python -m enrichment.pipeline
```

### tau2-Bench evaluation (1 trial per facilitator update)
```bash
cd ../tau2-bench
uv run tau2 run \
  --domain retail \
  --agent-llm openrouter/qwen/qwen3-next-80b-a3b-thinking \
  --user-llm openrouter/qwen/qwen3-next-80b-a3b-thinking \
  --num-trials 1 \
  --num-tasks 30
```

---

## Production Stack

| Layer | Tool | Status |
|---|---|---|
| Email (primary) | Resend free tier | Live |
| SMS (secondary, warm leads only) | Africa's Talking sandbox | Live |
| CRM | HubSpot Developer Sandbox | Live |
| Calendar | Cal.com Cloud (v2 API) | Live |
| Observability | Langfuse cloud free tier | Live |
| Evaluation | tau2-Bench retail domain | Live |
| LLM dev tier | OpenRouter Qwen3 | Live |
| LLM eval tier | Claude Sonnet 4.6 | Configured |
| Enrichment | Playwright + requests | Live |

---

## Act I Results — tau2-Bench Baseline

Official baseline provided by program facilitators (April 23, 2026).
Model: `openrouter/qwen/qwen3-next-80b-a3b-thinking`

| Metric | Value |
|---|---|
| Domain | Retail |
| Tasks | 30 |
| Trials | 5 |
| Evaluated simulations | 150 |
| Infra errors | 0 |
| pass@1 | 0.7267 |
| 95% CI | [0.6504, 0.7917] |
| Avg agent cost | $0.0199 |
| p50 latency | 105.95s |
| p95 latency | 551.65s |
| Git commit | d11a97072c49d093f7b5a3e4fe9da95b490d43ba |

Self-run reference using free Qwen3-235b (dev tier):
- pass@1: 0.268, 95% CI: [0.195, 0.341], cost: $0.00

---

## Act II Results — Production Stack

20 synthetic prospects processed end-to-end.

| Metric | Value |
|---|---|
| Total prospects | 20 |
| p50 latency | 3.52s |
| p95 latency | 4.54s |
| Min latency | 2.60s |
| Max latency | 4.54s |
| Average tone score | 5.0 / 5 |
| Tone violations | 0 |
| Abstain rate | 45% (9/20) |
| Human baseline median | 42 minutes |
| Speedup vs human | 715x |
| Speedup vs tau2-Bench p50 | 30x |

### Segment distribution (20 prospects)
| Segment | Count |
|---|---|
| Segment 4 - specialized capability gap | 11 |
| Abstain - low confidence | 9 |

---

## Key Design Decisions

**Rule-based email composition (no LLM cost)**
Email composition uses deterministic rules from `hiring_signal_brief.json` and `icp_definition.md`. This eliminates LLM cost per email, ensures consistent tone, and makes the system fully auditable. The honesty constraint is structural — the composer cannot assert claims not present in the brief.

**Confidence-gated segment classification**
Prospects with segment confidence below 0.6 receive a generic exploratory email rather than a segment-specific pitch. This prevents the most damaging failure mode — sending the wrong pitch to the wrong segment.

**Channel hierarchy enforcement**
Email is always the first outreach channel. SMS is gated on a prior email reply — the `is_warm_lead()` check in `sms_handler.py` blocks cold SMS outreach. Voice (discovery call) is the final channel, booked by the agent and delivered by a human Tenacious delivery lead.

**Bench-to-brief match gating**
Before composing any outreach the system checks `bench_summary.json`. If the prospect's required tech stacks are not available, the agent flags this in the context brief rather than over-committing capacity that does not exist.

**Booking triggers second HubSpot write**
When a discovery call is successfully booked, a second HubSpot note is written to the same contact record referencing the booking ID, UID, and start time. This keeps the CRM record complete without a separate sync process.

**Tone preservation check**
Every email draft is scored against the 5 Tenacious tone markers before sending. Drafts scoring below 4/5 are flagged. All 20 batch-run prospects scored 5/5.

---

## Known Limitations (Act II)

- `layoffs.fyi` CSV not auto-downloaded — returns no layoff signal by default. Download manually from layoffs.fyi and place at `data/layoffs.csv`
- Leadership change detection uses mock data — Crunchbase People API integration pending
- Job post velocity uses RemoteOK API — Wellfound and LinkedIn blocked by Cloudflare on server
- Cal.com booking fires at confidence >= 75% — most synthetic test prospects score 70%, so booking is skipped in test runs by design

---

## Kill Switch

Default is always dry run. Set explicitly to disable:

```bash
# In .env
DRY_RUN=true   # routes all outbound to staff sink (default)
DRY_RUN=false  # live mode - only after program staff approval
```

Verify before any run:
```bash
grep DRY_RUN .env
```

---

## Data Handling

- All prospect interactions use synthetic profiles during the challenge week
- No real Tenacious customer data is stored in this repository
- Seed materials are excluded from git via `.gitignore`
- All outbound during testing routes to staff-controlled sink when `DRY_RUN=true`
