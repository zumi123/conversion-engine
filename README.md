# Conversion Engine
### Automated Lead Generation and Conversion System for Tenacious Consulting and Outsourcing

**Challenge:** Week 10 — The Conversion Engine  
**Submission:** Final (Acts I–V)  
**Date:** April 25, 2026

---

## ⚠️ Kill Switch — Read This First

```bash
# In .env — DEFAULT IS ALWAYS DRY RUN
DRY_RUN=true   # All outbound routes to staff sink (default — must be set)
DRY_RUN=false  # Live mode — only after explicit Tenacious staff approval
```

**Before any run, verify:**
```bash
grep DRY_RUN .env
```

If `DRY_RUN` is not explicitly set to `false`, the system routes all outbound to the staff sink. This is not optional. Do not remove this check.

**Automatic kill-switch trigger:** If wrong-signal complaint rate exceeds 2 per 100 emails in any rolling 7-day window, set `DRY_RUN=true` immediately and audit before re-enabling. See `memo.pdf` Page 2 for full kill-switch clause.

---

## What This System Does

The Conversion Engine finds companies that match Tenacious's ideal customer profile, researches them using public data, writes personalized outreach emails grounded in verifiable signals, logs everything to HubSpot, and books discovery calls automatically.

The core insight: **qualification is the filter, research is the value proposition.** Every email the system sends arrives with a specific, verifiable finding about the prospect — not a generic pitch.

Key metrics from 20-prospect batch run:
- **p50 latency:** 3.52s (vs 42 minutes human baseline — 715x faster)
- **Tone score:** 5/5 across all 20 prospects, zero violations
- **Abstain rate:** 45% (9/20) — correct abstentions, not failures
- **Cost per lead:** <$0.01 (rule-based email composition, no LLM per message)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  DATA SOURCES                       │
│  Crunchbase ODM (1,000 companies, Apache 2.0)       │
│  RemoteOK Job Posts (Playwright + public API)       │
│  layoffs.fyi CSV (CC-BY)                            │
│  Google News RSS (leadership change detection)      │
└──────────────────────┬──────────────────────────────┘
                       │  public signals
                       ▼
┌─────────────────────────────────────────────────────┐
│              ENRICHMENT PIPELINE                    │
│  enrichment/crunchbase.py   -> firmographics        │
│  enrichment/job_posts.py    -> hiring velocity      │
│  enrichment/layoffs.py      -> cost pressure signal │
│  enrichment/leadership.py   -> CTO/VP Eng changes   │
│  enrichment/ai_maturity.py  -> AI maturity (0-3)    │
│  enrichment/competitor_gap.py -> top-quartile gap   │
│  enrichment/pipeline.py     -> orchestrates all     │
│                                                     │
│  Output: hiring_signal_brief.json                   │
│          competitor_gap_brief.json                  │
└──────────────────────┬──────────────────────────────┘
                       │  structured brief + confidence scores
                       ▼
┌─────────────────────────────────────────────────────┐
│              ICP CLASSIFIER                         │
│  Segment 1: Recently-funded Series A/B              │
│  Segment 2: Mid-market restructuring                │
│  Segment 3: New CTO/VP Engineering                  │
│  Segment 4: Specialized capability gap              │
│  Abstain:   confidence < 0.6                        │
└──────────────────────┬──────────────────────────────┘
                       │  segment + confidence
                       ▼
┌─────────────────────────────────────────────────────┐
│               EMAIL AGENT                           │
│  agent/email_handler.py                             │
│  <- seeds/seed/style_guide.md  (5 tone markers)    │
│  <- seeds/seed/bench_summary.json (capacity gate)  │
│  <- seeds/seed/icp_definition.md (segment rules)   │
│                                                     │
│  Rule-based composition — no LLM per email         │
│  Tone check: Direct · Grounded · Honest ·           │
│              Professional · Non-condescending       │
└──────────┬──────────────┬────────────────┬──────────┘
           │              │                │
           ▼              ▼                ▼
    ┌──────────┐  ┌──────────────┐  ┌───────────────┐
    │CHANNEL 1 │  │  CHANNEL 2   │  │   CHANNEL 3   │
    │(Primary) │  │ (Secondary)  │  │    (Final)    │
    │  Resend  │  │  Africa's    │  │   Cal.com     │
    │  Email   │  │  Talking SMS │  │  Discovery    │
    │          │  │ (warm leads  │  │     Call      │
    │          │  │  only —      │  │ (agent books, │
    │          │  │  gated on    │  │  human closes)│
    │          │  │  email reply)│  │               │
    └──────────┘  └──────────────┘  └───────────────┘
                         │
                         ▼
           ┌─────────────────────────┐
           │      HUBSPOT CRM        │
           │  Write 1: enrichment +  │
           │  ICP segment at outreach│
           │  Write 2: booking ref   │
           │  after Cal.com confirms │
           └─────────────────────────┘
                         │
                         ▼
           ┌─────────────────────────┐
           │       LANGFUSE          │
           │  Per-step tracing       │
           │  Latency + cost logging │
           └─────────────────────────┘
```

---

## Repository Structure

```
conversion-engine/
├── agent/
│   ├── email_handler.py       # Rule-based composer, 5-marker tone check
│   ├── orchestrator.py        # End-to-end flow with Langfuse tracing
│   └── sms_handler.py         # Africa's Talking — channel hierarchy gate
│
├── enrichment/
│   ├── ai_maturity.py         # AI maturity scoring (0-3), 6-signal rubric
│   ├── competitor_gap.py      # Top-quartile gap analysis by sector
│   ├── crunchbase.py          # Crunchbase ODM firmographic lookup
│   ├── job_posts.py           # RemoteOK API + Playwright careers scraper
│   ├── layoffs.py             # layoffs.fyi CSV parser (CC-BY dataset)
│   ├── leadership.py          # CTO/VP Eng change detection (3 sources)
│   └── pipeline.py            # Orchestrator -> hiring_signal_brief.json
│
├── integrations/
│   ├── cal_com.py             # Cal.com v2 API booking
│   └── hubspot.py             # HubSpot CRM — two writes per prospect
│
├── eval/
│   ├── baseline.md            # Official facilitator baseline (do not edit)
│   ├── score_log.json         # Official facilitator score log
│   ├── trace_log.jsonl        # Official facilitator traces (150 sims)
│   ├── act2_metrics.json      # Act II latency and quality metrics
│   └── act4/
│       ├── method.md              # Mechanism design + ablation analysis
│       ├── ablation_results.json  # All 4 conditions with stats
│       ├── held_out_traces.jsonl  # Raw traces from all 3 variants
│       ├── variant_a_results.json # 10 strict rules (pass@1: 0.467)
│       ├── variant_b_results.json # 4 light reminders (pass@1: 0.600)
│       └── variant_c_results.json # Original prompt (pass@1: 0.600)
│
├── data/
│   ├── crunchbase_sample.csv  # 1,000-company Crunchbase ODM (Apache 2.0)
│   ├── crunchbase_sample.json # Parsed ODM sample
│   ├── layoffs.csv            # layoffs.fyi export (CC-BY, 4,358 rows)
│   └── job_posts_test.json    # Job post scrape snapshot
│
├── outputs/
│   ├── hiring_signal_brief_*.json   # Per-prospect enrichment briefs
│   ├── competitor_gap_brief_*.json  # Per-prospect gap analysis
│   ├── batch_results.json           # 20-prospect batch run results
│   └── traces/                      # Per-prospect flow traces
│
├── probes/
│   ├── probe_library.md        # 35 adversarial probes across 10 categories
│   ├── failure_taxonomy.md     # Failure classes A-G with trigger rates
│   ├── target_failure_mode.md  # Act IV target: confidence aggregation bugs
│   └── real_company_probes.md  # 7 real-company probes (pre/post fix)
│
├── seeds/                     # Tenacious confidential materials (gitignored)
│
├── tests/
│   ├── test_end_to_end.py          # Single prospect full flow
│   ├── test_batch.py               # 20-prospect batch
│   ├── test_probes.py              # Adversarial probe runner
│   └── test_probes_advanced.py     # Extended probe runner (7 probes)
│
├── memo.pdf                   # Act V — 2-page decision memo
├── evidence_graph.json        # Act V — every number traced to source
├── main.py                    # FastAPI webhook server
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/conversion-engine.git
cd conversion-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

```bash
cp .env.example .env
nano .env
```

### 3. Add seed materials

Obtain from program staff and place in `seeds/seed/`:
- `icp_definition.md`
- `style_guide.md`
- `bench_summary.json`
- `pricing_sheet.md`
- `baseline_numbers.md`

### 4. Download layoffs.fyi CSV

Download CC-BY export and place at `data/layoffs.csv`. Required for Segment 2 classification.

### 5. Start the webhook server

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn main:app --port 8000
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

# Kill switch — default MUST be true
DRY_RUN=true
```

---

## Results Summary

### Act I — tau2-Bench Baseline (facilitator-provided)

| Metric | Value |
|---|---|
| Model | openrouter/qwen/qwen3-next-80b-a3b-thinking |
| Tasks / Trials | 30 / 5 (150 sims) |
| **pass@1** | **0.7267** |
| 95% CI | [0.6504, 0.7917] |
| p50 latency | 105.95s |

### Act II — Production Stack

| Metric | Value | Source |
|---|---|---|
| p50 latency | **3.52s** | eval/act2_metrics.json |
| Speedup vs human (42 min) | **715x** | Derived |
| Speedup vs tau2-Bench p50 | **30x** | Derived |
| Tone score (20 prospects) | **5.0 / 5** | outputs/batch_results.json |
| Tone violations | **0** | outputs/batch_results.json |
| Abstain rate | **45% (9/20)** | outputs/batch_results.json |
| Cost per interaction | **$0.00** | Rule-based, no LLM per email |

### Act IV — Ablation Results

| Condition | pass@1 | 95% CI |
|---|---|---|
| Facilitator baseline (5 trials) | 0.7267 | [0.6504, 0.7917] |
| Variant C: original prompt (1 trial) | 0.600 | [0.4267, 0.7506] |
| Variant B: 4 light reminders (1 trial) | 0.600 | [0.4267, 0.7506] |
| Variant A: 10 strict rules (1 trial) | 0.467 | [0.2981, 0.6419] |

**Finding:** Instruction augmentation hurts thinking models. Variant A vs facilitator: z=-2.915, p=0.0018.

---

## Known Limitations

| Limitation | Impact | Fix Required Before |
|---|---|---|
| Segment 1 untestable end-to-end | ~60-70% Segment 1 candidates excluded | Segment 1 deployment |
| ODM data freshness lag | Stale funding claims after 180 days | Segment 1 deployment |
| bench_summary.json not auto-updated | Bench over-commitment mid-week | Live deployment |
| Segment 3 untested in batch flow | Cal.com booking path untested at scale | Segment 3 deployment |

---

## For the Engineer Who Inherits This

1. Read `seeds/seed/icp_definition.md` before changing any segment logic — segment names are fixed for grading.
2. Read `seeds/seed/style_guide.md` before changing any email templates — 5 tone markers must be preserved.
3. Never modify `bench_summary.json` manually — it updates weekly from Tenacious ops.
4. The `segment_confidence` threshold (0.6 for abstain, 0.75 for booking) is the primary quality lever.
5. All numeric claims in `eval/` trace back to tau2-Bench simulation files — do not edit manually.
6. `DRY_RUN` must be explicitly set to `false` for live deployment — default is always `true`.
7. **Do not add explicit rules to the LLM system prompt** to fix honesty issues — Act IV showed this makes performance significantly worse (p=0.0018). Fix honesty at the data/pipeline level instead.
8. The kill-switch trigger is 2 wrong-signal complaints per 100 emails in any rolling 7-day window. Track this in HubSpot from day one of live deployment.
9. Segment 1 is undeployable without a job-data API fallback (Wellfound or Coresignal). RemoteOK only covers remote-first companies.
10. Seeds are gitignored. Never commit seed materials to GitHub.