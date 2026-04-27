# Target Failure Mode for Act IV

## Selected: Failure Class A — Confidence Aggregation Bugs

**Specific failures:**
- **A.1** — `overall_brief_confidence` reports "high" when
  component signals are medium/low (Probe A)
- **A.2** — `segment_confidence` stays at 0.7 even when the
  underlying AI maturity confidence is 0.4 (Probe D)

## Why This Failure Mode

### 1. Real evidence from live probes
Unlike speculated failures, this was directly observed in
adversarial probe runs on 2026-04-23. See
`probe_library.md` Probes A and D for full output.

### 2. Honesty-category violation
Per `seeds/seed/style_guide.md`, the Tenacious brand is
grounded in "confidence-aware phrasing: ask rather than
assert when signal is weak." If the agent's confidence
score is inflated, the phrasing choice downstream is
miscalibrated. An agent that says "based on strong signal
you're building toward AI" — when underlying signal is
actually weak — is exactly the failure the style guide
warns against.

### 3. Maps to rubric feedback
The Round 1 rubric feedback explicitly called out missing
per-signal confidence scores. We added them in Act II as
labels. Act IV will make those labels FUNCTIONAL — they
will actually affect the agent's phrasing.

### 4. Fits within $10 budget and 1-day timeline
The fix is a calculation change in `pipeline.py` and a
phrasing matrix in `email_handler.py`. No new API
integrations or scraping infrastructure.

## Proposed Mechanism for Act IV

### Signal-confidence-aware phrasing

**Current state:** The email composer reads
`brief["ai_maturity"]["score"]` and picks between "scale
your AI team" (score >= 2) and "stand up your first AI
function" (score < 2). It does not consult
`brief["ai_maturity"]["confidence"]`.

**Proposed mechanism:** The composer reads BOTH score AND
confidence. Language shifts based on a 2D matrix:

| Score | Confidence | Phrasing |
|---|---|---|
| High (2-3) | High (>=0.7) | Assert: "your AI engineering team scaling" |
| High (2-3) | Medium (0.4-0.7) | Soft assert: "based on public signal, it looks like" |
| High (2-3) | Low (<0.4) | Ask: "curious whether you have an AI function" |
| Low (0-1) | Any | Ask: "where is your current AI capability scoped" |

### Confidence aggregation fix

**Current bug:** `overall_brief_confidence` can be "high"
even when components are medium.

**Fix:** overall = min(component confidences). If any
individual signal is "low," overall cannot be "high."

### segment_confidence recalibration

**Current bug:** Hardcoded 0.7 for Segment 4 regardless
of supporting signals.

**Fix:** segment_confidence = hardcoded_base * avg(supporting_signal_confidences).
E.g. base 0.7 * avg(ai_maturity=0.4) = 0.28 → would trigger
abstention.

## Success Criteria for Act IV

1. Signal-confidence-aware composer implemented in
   `agent/email_handler.py`.
2. Re-run Probes A and D — A should show overall = "medium"
   when components are medium; D should show segment_confidence
   < 0.6 (triggering abstention).
3. Re-run 20-prospect batch test — zero tone violations maintained.
4. Run τ²-Bench retail domain (1 trial, 30 tasks).
5. Beat facilitator baseline pass@1 of 0.7267 with 95% CI
   separation (p < 0.05).
6. Three ablation variants tested and documented in method.md.

## What Will NOT Be Fixed in Act IV

Deprioritized from failure_taxonomy:
- **Class B** (mock_signals extension) — will be fixed as
  side-effect of building ablation testing.
- **Class C** (design choices) — will be documented as
  honesty-reach tradeoff in the final memo, not "fixed."

These are noted as known limitations with fix effort estimates.

## Risk of This Mechanism

**Risk:** Making phrasing too soft could reduce reply rate.

**Mitigation:** The three ablation variants will test
different aggressiveness levels. We will pick the variant
that maintains reply rate while reducing over-assertion
honesty violations.

**Detection:** If Act IV runs show pass@1 dropping below
0.6504 (the CI lower bound of baseline), we rollback the
mechanism and document the failure in the final memo.

## Business-Cost Derivation (Tenacious Terms)

### Cost of the failure if left unfixed

**Scenario:** Agent sends signal-grounded emails to 1,000 prospects over 30 days.
Because overall_brief_confidence is inflated, ~15% of emails assert claims
(e.g., "your AI function is scaling") when underlying signals are medium-confidence.

That's **150 emails with over-claimed signal**.

### Reply-rate impact
- Baseline signal-grounded reply rate: 7-12% (per Clay/Smartlead benchmarks)
- Over-claimed emails: reply rate drops to 2-4% (prospect pattern-matches as
  generic outbound) — conservatively estimate 50% reply-rate reduction
- Expected lost replies: 150 × 10% × 0.5 = **7.5 fewer replies per 1,000 emails**

### Conversion funnel impact
- Lost replies → lost discovery calls (per Tenacious: 35-50% discovery → proposal)
- Proposals → close: 25-40%
- 7.5 lost replies → ~3.3 lost discovery calls → ~1.3 lost proposals → ~0.4 lost deals

At talent-outsourcing ACV of $240-720K:
- **Expected revenue loss: $96K - $288K per 1,000 emails**
- At 4,000 emails/month (Tenacious volume target): **$384K - $1.15M/year loss**

### Brand-reputation cost (unit economics)
Per the memo requirements:
- 150 over-claimed emails × 5% screenshot/share probability = 7.5 public incidents
- 1 viral LinkedIn screenshot of "generic AI sales bot" with Tenacious attribution
- Customer acquisition cost for the 3-4 direct replacement deals lost to brand damage:
  at Tenacious CAC of ~$15K per deal = **$45-60K direct + long-tail trust damage**

### Stalled-thread impact
The current Tenacious stalled-thread rate is 30-40%. Over-claimed emails that do
receive replies generate threads that stall at a higher rate (~55-60%) because the
prospect's first response is defensive ("that's not accurate") rather than curious.
Expected uplift to stalled-thread rate: **+5 percentage points** on the affected
segment.

### Total conservative business-cost estimate
- Direct revenue loss: $384K-$1.15M/year at target volume
- Brand-reputation indirect cost: $60K-$200K/year
- Stalled-thread overhead (sales team hours): ~20 hours/week × $150/hour = $156K/year
- **Total: $600K-$1.5M annualized cost of unfixed failure**

### Cost of the fix
- Development: 1 day (Act IV)
- LLM eval cost: ~$5 of the $10 budget
- Runtime cost impact: +$0.00 (still rule-based, just different phrasing rules)
- Maintenance: re-audit phrasing matrix quarterly

**ROI:** 120,000× return on 1-day fix at conservative lower bound.