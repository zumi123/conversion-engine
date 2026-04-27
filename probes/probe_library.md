# Adversarial Probe Library — Conversion Engine

## Overview
Adversarial probes designed to find real failure modes in the
Conversion Engine. Every probe was actually executed against
the live pipeline. Results come from real runs — not predictions.

Run log: `adversarial/probe_results.log`
Test runner: `tests/test_probes_advanced.py`

---

## Probe Results — Executed on 2026-04-23

### Probe A — All AI signals set to true via mock
**Hypothesis:** System would accept 3/3 AI maturity from
purely mocked data without verification, which would be a
honesty concern.

**Input:** All 6 AI sub-signals = true, via mock_signals.

**Expected:** Classify Segment 4 at 0.7 confidence.

**Actual:**
- Segment: segment_4_specialized_capability
- Confidence: 0.7
- AI maturity: 3/3 with internal confidence 0.5
- signal_confidence_summary.ai_maturity = "medium"
- overall_brief_confidence = "high"

**Status:** ✅ PASS classification, but ⚠️ PARTIAL on honesty
**Finding:** The system DOES classify Seg 4 from mocked signals
without source verification. When mock data is injected, the
system treats it as real. This is not a bug per se (mock is a
test input) but reveals that the pipeline has no integrity check
distinguishing real vs mocked signal origin.

**Honesty bug found:** overall_brief_confidence is labeled "high"
even when individual components are medium-to-low. A confidence
aggregator should not upgrade individual signal confidence.

**Severity:** HIGH (honesty category)

---

### Probe B — New CTO at small startup (10 employees expected,
but mock default gives 45)
**Hypothesis:** Segment 3 classification should gate on
50-500 headcount per ICP definition. A 45-person company
should not fire Segment 3.

**Input:**
- leadership.detected = True, role = "cto"
- No AI signals

**Expected:** abstain (headcount gate fails 50-500 rule)

**Actual:** abstain (confidence: 0.4)

**Status:** ✅ PASS

**Finding:** Headcount gate is enforced correctly for
sub-threshold companies. This is correct behavior.

**Severity:** n/a

---

### Probe C — New CTO at 45-person company (mock default)
**Hypothesis:** Segment 3 should fire when leadership is
detected AND headcount is within 50-500.

**Input:**
- leadership.detected = True, role = "cto"
- Mock default company: 45 employees (the mock
  crunchbase.py default)

**Expected:** segment_3_leadership_transition at 0.85 confidence

**Actual:** abstain (confidence: 0.4)

**Status:** ❌ FAIL

**Root cause analysis:**
The mock Crunchbase company has 45 employees, which is
BELOW the 50-500 headcount threshold. So Segment 3 correctly
fails, but the classifier then falls through to abstain
rather than trying the next rule.

Actually this is consistent with the ICP rules — a 45-person
company with no other signals SHOULD abstain.

**Re-classification:** This is not a failure. My expected
value was wrong. The system correctly abstained because no
other segment signals fired either.

**Finding:** Mock Crunchbase defaults need to be updated to
include a 100-employee variant for testing Segment 3 paths.

**Severity:** LOW (test data issue, not system bug)

---

### Probe D — AI score with mixed-confidence inputs
**Hypothesis:** High AI score from medium/low-confidence
inputs should either drop confidence or trigger
weak_ai_maturity_signal.

**Input:**
- ai_open_roles = 3, total = 5
- has_ai_leadership = True
- All other AI signals = false
- modern_ml_stack = True

**Expected:** segment_4_specialized_capability at 0.7

**Actual:** segment_4_specialized_capability at 0.7
- AI maturity 2/3 with confidence 0.4
- weak_ai_maturity_signal appears in honesty_flags ✅
- signal_confidence_summary.ai_maturity = "medium"

**Status:** ✅ PASS

**Finding:** The honesty flag fires correctly when AI
maturity confidence is low. However, segment_confidence
remains at 0.7 rather than being discounted. This means
the classifier doesn't use ai_maturity.confidence in its
segment_confidence calculation.

**Severity:** MEDIUM
**Fix needed:** segment_confidence should incorporate
underlying signal confidence scores.

---

### Probe E — Boundary AI score of exactly 2
**Hypothesis:** An AI score of exactly 2 (the segment 4
threshold) should fire Segment 4.

**Input:**
- Only has_ai_leadership = True
- All other AI signals = false

**Expected:** segment_4_specialized_capability

**Actual:** abstain (confidence: 0.4)
- AI maturity 1/3 with confidence 0.25

**Status:** ❌ FAIL (my hypothesis was wrong)

**Root cause:** has_ai_leadership alone scores 1 point
(high-weight), not 2. My test input was incorrect. The
scorer requires either 2 high-weight signals OR
1 high-weight + 2+ medium-weight signals to reach 2.

**Re-classification:** This is CORRECT behavior, not a bug.
The scoring rubric is working as designed.

**Finding:** AI maturity requires multiple confirming signals
to reach Segment 4 threshold. This is the expected honesty
behavior — a single leadership mention is not enough to
assert specialized capability gap.

**Severity:** n/a (working as designed)

---

### Probe F — Fresh funding with 8 open roles (no AI)
**Hypothesis:** Segment 1 should fire when mock funding
is valid and job signal is strong.

**Input:**
- mock_signals gave ai_open_roles = 0, total_open_roles = 8
- Mock default funding = fresh Series A $14M

**Expected:** segment_1_series_a_b

**Actual:** abstain (confidence: 0.4)

**Status:** ❌ FAIL

**Root cause analysis:**
Looking at the pipeline code, segment 1 classification
requires `job_count >= 5`. But `job_count` comes from the
real RemoteOK fetch, not from `mock_signals.total_open_roles`.
RemoteOK returned 0 jobs for "ScalingStartup" (because that
company doesn't exist on the platform).

**This is a real bug.** The mock_signals system is
INCOMPLETE — it can override AI signals and leadership, but
NOT hiring velocity / job count. So a Segment 1 test is
impossible to run without real companies in the data.

**Severity:** HIGH (testing infrastructure)
**Fix needed:** Extend mock_signals to override
`hiring_velocity.open_roles_today`.

---

### Probe G — Determinism check
**Hypothesis:** Running the same company twice should
produce identical classifications.

**Input:** Same mock_signals, two sequential runs.

**Expected:** Both runs produce same segment.

**Actual:**
- Run 1: segment_4_specialized_capability (conf 0.7)
- Run 2: segment_4_specialized_capability (conf 0.7)

**Status:** ✅ PASS

**Finding:** System is deterministic for identical inputs.
No hidden randomness in the classifier or email composer.

**Severity:** n/a

---

## Summary

| Probe | Expected | Actual | Status | Finding |
|---|---|---|---|---|
| A | Seg 4 | Seg 4 | ✅ + ⚠️ | overall_confidence = "high" when components are "medium" |
| B | abstain | abstain | ✅ | Headcount gate works |
| C | Seg 3 | abstain | ❌→n/a | Mock headcount below threshold (test issue) |
| D | Seg 4 | Seg 4 | ✅ | Honesty flag fires correctly |
| E | Seg 4 | abstain | ❌→n/a | My input didn't reach score 2 (test issue) |
| F | Seg 1 | abstain | ❌ | mock_signals cannot override hiring_velocity |
| G | deterministic | deterministic | ✅ | No hidden randomness |

### Real Bugs Found

1. **Overall brief confidence aggregation is incorrect.**
   When individual signals are medium/low, the overall should
   not be "high." (Probe A)

2. **segment_confidence does not use underlying signal
   confidence.** A segment can be classified at 0.7 even when
   the supporting signals are confidence 0.4. (Probe D)

3. **Testing infrastructure gap: mock_signals cannot override
   hiring_velocity or funding data.** This prevents
   end-to-end testing of Segment 1 and Segment 2. (Probe F)

### Working Correctly

- Headcount gating for Segment 3 (Probe B)
- Honesty flags firing when AI signal is weak (Probe D)
- AI maturity requires multiple confirming signals (Probe E)
- Determinism across runs (Probe G)
- Abstention when no clear segment match (all passes)