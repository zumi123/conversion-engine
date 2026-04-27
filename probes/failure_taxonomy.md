# Failure Taxonomy — Conversion Engine

Categorization of failures discovered during Act III adversarial probing.
All findings come from actual probe runs executed against the live pipeline.
Updated 2026-04-25 with Batch 2 results (28 probes) and real-company probes (5 companies).

---

## Failure Class A — Confidence Aggregation Bugs

**Root cause:** The pipeline assembles individual signal confidences into a summary block, but the aggregation logic is broken in two places. Individual signal labels are correct, but the rollups to overall confidence and segment confidence do not respect them.

### A.1 — Overall confidence label contradicts component labels

**Evidence:** Probe A output (FakeAICorp with all signals mocked):
Individual components are rated "low" or "medium," but the overall rollup is reported as "high." This is mathematically impossible — an aggregate cannot be higher than its highest component.

**Business risk:** The agent downstream reads `overall_brief_confidence` to decide whether to assert versus ask. An inflated overall score causes the agent to assert claims when the underlying evidence only supports asking. This is exactly the honesty violation the Tenacious style guide warns against.

**Severity:** HIGH (honesty-category violation)

---

### A.2 — segment_confidence ignores component signal confidence

**Evidence:** Probe D output (WeakEvidenceAI with mixed-confidence inputs):
The system correctly identified that ai_maturity confidence is only 0.4 (low-to-medium) and fired the `weak_ai_maturity_signal` honesty flag. But `segment_confidence` was still set to the hardcoded 0.7 for Segment 4 classification — as if the supporting signal were fully trusted.

**Business risk:** Segment 4 classification at confidence 0.7 proceeds to email composition with Segment 4 pitch language. The Segment 4 pitch specifically cites competitor gap findings — which are inappropriate when the underlying AI maturity signal is only 40% confident.

**Severity:** MEDIUM (honesty-category violation)

---

## Failure Class B — Testing Infrastructure Gaps

**Root cause:** The `mock_signals` parameter in `run_pipeline()` only overrides SOME signals. Other signals (job count, funding amount) come from real fetches, making certain test scenarios impossible to construct.

### B.1 — mock_signals cannot override hiring_velocity

**Evidence:** Probe F output (ScalingStartup with mocked total_open_roles=8):
The `mock_signals.ai_signals.total_open_roles` field is used only for AI maturity scoring. The actual `hiring_velocity.open_roles_today` value comes from a live RemoteOK API call that filters jobs by company name. For non-real company names (ScalingStartup), RemoteOK returns 0 jobs.

The classifier requires `job_count >= 5` for Segment 1 — so any Segment 1 test is impossible without registering the fake company on a real job board.

**Business risk:** Segment 1 classification path cannot be tested end-to-end. Ablation variants in Act IV cannot validate Segment 1 behavior without this fix.

**Severity:** HIGH (blocks Segment 1 and Segment 2 end-to-end testing)

---

### B.2 — mock_signals cannot override funding data

**Evidence:** When a company is not in the Crunchbase ODM sample, funding data comes from `_mock_company()` hardcoded defaults — always Series A, always $14M, always 90 days ago. No way to test "Segment 1 with Series B at $25M" without editing the mock defaults or adding to the ODM.

**Business risk:** Variance in Segment 1 classification across different funding profiles cannot be tested. Also prevents testing the $5M-$30M boundary rule.

**Severity:** MEDIUM

---

## Failure Class C — Honesty-vs-Reach Tradeoff (Design Choices, Not Bugs)

**Root cause:** The classifier's rules are intentionally strict about abstention — favoring honesty over volume. This reduces classification coverage but aligns with the Tenacious brand constraint.

### C.1 — Segment 1 requires 5+ real observable open roles

**Evidence:** Probe F — mock indicated fresh funding and declared hiring intent, but classifier refused to fire Segment 1 because RemoteOK returned 0 jobs.

**Interpretation:** This is working as DESIGNED. The style guide says the agent should never assert "aggressive hiring" without 5+ observable open roles. The classifier correctly refuses to pitch Segment 1 without the evidence to ground it.

**Severity:** n/a (design choice, documented in final memo)

---

### C.2 — AI maturity score requires multiple confirming signals

**Evidence:** Probe E — a single `has_ai_leadership = True` input produced AI maturity score 1/3, not 2/3.

**Interpretation:** Also by design. Prevents single-signal false positives for Segment 4. The scoring rubric requires either two high-weight signals OR one high-weight plus two medium-weight signals to reach score 2.

**Severity:** n/a (design choice, documented in final memo)

---

## Failure Class D — Signal Source False Positives (NEW — discovered in Batch 2 + real-company probes)

**Root cause:** The Google News RSS leadership detection checked whether the company name and a leadership keyword appeared ANYWHERE in the RSS response body. The feed-level `<title>` element contains the search query itself, which always includes both the company name and "CTO" — producing 100% false positives.

### D.1 — Google News RSS 100% false positive rate on real companies

**Evidence:** 5 real Crunchbase companies tested (Wit.ai, Semantica, Wickr, SnapTrade, Whitehill Technologies). ALL 5 returned `leadership detected: True` via `google_news_rss` method BEFORE the fix. None of these companies had a genuine leadership change.

- Wickr: incorrectly classified Segment 3 at 0.85 confidence
- Whitehill Technologies: incorrectly classified Segment 3 at 0.85 confidence
- Other 3: correctly abstained despite false leadership signal

**Fix applied:** Title extraction now uses `<item>` blocks only (skips feed-level title), requires appointment verb in same title, and checks company appears as subject not object. Post-fix: 0/6 false positives on small/medium companies. 2/6 borderline matches on mega-companies (Snap, Meta) where articles about executives LEAVING those companies match.

**Severity:** CRITICAL (honesty-category violation — would send wrong-segment pitches to real prospects)

---

### D.2 — Input validation gaps

**Evidence:** Batch 2 probes 6.1 and 6.3:
- Empty company name accepted silently (no validation error)
- String passed as `mock_signals` instead of dict accepted silently

**Business risk:** Low — these are testing-path issues, not production-path. But they indicate missing input guards.

**Severity:** MEDIUM

---

## Observed Trigger Rates (Updated with all batches)

### By Failure Class

| Class | Total probes | Failures triggered | Trigger rate |
|---|---|---|---|
| A. Confidence aggregation | 2 | 2 | 100% |
| B. Testing infrastructure | 2 | 2 | 100% |
| C. Honesty-vs-reach design | 2 | 0 (by design) | 0% |
| D. Signal source false positives | 7 | 7 (pre-fix), 2 (post-fix) | 100% → 33% |

### By Probe Category (Batch 2 — 28 probes)

| Category | Probes | Passed | Failed | Fail rate |
|---|---|---|---|---|
| ICP Misclassification | 2 | 2 | 0 | 0% |
| Signal Over-claiming | 3 | 3 | 0 | 0% |
| Bench Over-commitment | 2 | 2 | 0 | 0% |
| Tone Drift | 4 | 4 | 0 | 0% |
| Multi-thread Leakage | 2 | 2 | 0 | 0% |
| Cost Pathology | 3 | 1 | 2 | 67% |
| Dual Control | 2 | 2 | 0 | 0% |
| Scheduling | 2 | 2 | 0 | 0% |
| Signal Reliability | 6 | 6 | 0 | 0% |
| Gap Over-claiming | 2 | 2 | 0 | 0% |

### Real Company Probes (5 companies)

| Company | Pre-fix leadership | Post-fix leadership | Correct? |
|---|---|---|---|
| Wit.ai | True (false positive) | False | YES |
| Semantica | True (false positive) | False | YES |
| Wickr | True (false positive) | False | YES |
| SnapTrade | True (false positive) | False | YES |
| Whitehill Technologies | True (false positive) | False | YES |
| Snap | True (false positive) | True (borderline) | BORDERLINE |
| Meta | True (false positive) | True (borderline) | BORDERLINE |

---

## Summary by Class (Updated)

| Class | Failures | Highest Severity | Status |
|---|---|---|---|
| A. Confidence aggregation | 2 | HIGH | Fix in Act IV — target failure mode |
| B. Testing infrastructure | 2 | HIGH | Fix during Act IV as side-effect |
| C. Honesty-vs-reach | 2 | n/a | Document as design choice in memo |
| D. Signal false positives | 2 | CRITICAL | FIXED — RSS now uses per-article title matching |

---

## Act IV Focus

**Class A** (confidence aggregation) is the highest-priority failure mode for Act IV because:

1. **Honesty category** — direct brand risk. A single viral screenshot of an over-claiming email costs more than a week of volume gains.

2. **Maps to Round 1 rubric feedback** — the request for explicit per-signal confidence scores was satisfied in Act II with labels. Act IV makes those labels FUNCTIONAL — they will actually affect the agent's phrasing decisions.

3. **Clear mechanism fix available** — a calculation change in `pipeline.py` plus a phrasing matrix in `email_handler.py`. No new API integrations or scraping infrastructure needed.

4. **Fits budget** — fits within the $10 OpenRouter allocation and the 1-day Act IV timeline.

**Class D** (signal false positives) was the most critical bug found during probing but has been FIXED. The fix reduced false positive rate from 100% to 0% on ICP-sized companies. Remaining borderline matches on mega-companies (Snap, Meta) are documented as a known limitation — these companies are outside Tenacious's ICP anyway.

---

## Cross-reference

- Full probe details: `probes/probe_library.md`
- Batch 2 raw results: `probes/probe_results_batch2.json`
- Real company probe details: `probes/real_company_probes.md`
- Target failure mode and Act IV plan: `probes/target_failure_mode.md`
- Test runners: `tests/test_probes.py`, `tests/test_probes_advanced.py`, `tests/test_probes_batch2.py`