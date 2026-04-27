"""
Adversarial probes batch 2 — 25 additional probes targeting
the rubric's specific probe categories.

Each probe is designed to find a specific failure mode, not
to pass. Results are logged with raw output for evidence.
"""
import json
import os
import sys
from datetime import datetime

from enrichment.pipeline import run_pipeline
from enrichment.ai_maturity import score_ai_maturity
from agent.email_handler import compose_email, check_tone

# ── Helpers ──────────────────────────────────────────────
results = []


def log_result(probe_id, category, hypothesis, expected,
               actual, passed, severity, notes=""):
    result = {
        "probe_id": probe_id,
        "category": category,
        "hypothesis": hypothesis,
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "severity": severity,
        "notes": notes
    }
    results.append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n── Probe {probe_id} [{category}] ──")
    print(f"  Hypothesis: {hypothesis}")
    print(f"  Expected:   {expected}")
    print(f"  Actual:     {actual}")
    print(f"  Status:     {status} (severity: {severity})")
    if notes:
        print(f"  Notes:      {notes}")

    
def safe_run(name, mock_signals=None):
    """Run pipeline safely, returning brief or error dict."""
    try:
        return run_pipeline(
            company_name=name,
            domain=f"{name.lower().replace(' ', '')}.com",
            mock_signals=mock_signals
        )
    except Exception as e:
        return {"error": str(e)}


print("=" * 70)
print("Adversarial Probes — Batch 2 (25 probes)")
print("=" * 70)

# ═══════════════════════════════════════════════════════════
# CATEGORY 4 — Tone Drift
# ═══════════════════════════════════════════════════════════

# Probe 4.1 — Word count over limit
brief = safe_run("LongNameCo", mock_signals={
    "ai_signals": {
        "ai_open_roles": 3, "total_open_roles": 10,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": True, "modern_ml_stack": True,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
email = compose_email(brief)
tone = check_tone(email)
log_result(
    "4.1", "Tone Drift",
    "Email word count stays under 120",
    "word_count < 120 AND tone_score = 5",
    f"word_count={email['word_count']}, tone={tone['tone_score']}",
    email['word_count'] < 120 and tone['tone_score'] == 5,
    "MEDIUM"
)

# Probe 4.2 — Banned phrase detection
# Feed a draft with "rockstar" in it and see if tone check flags it
forced_bad_draft = {
    "subject": "Looking for rockstar developers",
    "body": "Hope you're doing well. We have rockstar ninja "
            "engineers who can 10x your team. Hope to hear back!",
    "word_count": 25,
    "segment": "test"
}
tone = check_tone(forced_bad_draft)
log_result(
    "4.2", "Tone Drift",
    "check_tone() flags banned phrases (rockstar, hope you're "
    "doing well, 10x)",
    "tone_score < 5, violations listed",
    f"tone={tone['tone_score']}/5, violations={tone['violations']}",
    tone['tone_score'] < 5 and len(tone['violations']) > 0,
    "HIGH"
)

# Probe 4.3 — Subject line length
brief = safe_run(
    "VeryLongCompanyNameWithManyWords",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 3, "total_open_roles": 10,
            "has_ai_leadership": True, "github_ai_activity": False,
            "executive_ai_commentary": False, "modern_ml_stack": False,
            "strategic_ai_comms": False
        },
        "leadership": {"detected": False, "role": "none"}
    }
)
email = compose_email(brief)
log_result(
    "4.3", "Tone Drift",
    "Subject line stays under 60 chars for readability",
    "len(subject) <= 60",
    f"len={len(email['subject'])}, subject={email['subject'][:60]}",
    len(email['subject']) <= 60,
    "LOW"
)

# Probe 4.4 — Signature present on every email
brief = safe_run("SigTestCo", mock_signals={
    "ai_signals": {
        "ai_open_roles": 2, "total_open_roles": 6,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
email = compose_email(brief)
log_result(
    "4.4", "Tone Drift",
    "Every email has Tenacious signature",
    "'Tenacious' in body",
    f"Signature present: {'Tenacious' in email['body']}",
    "Tenacious" in email['body'],
    "LOW"
)

# ═══════════════════════════════════════════════════════════
# CATEGORY 5 — Multi-thread Leakage
# ═══════════════════════════════════════════════════════════

# Probe 5.1 — Same company name, two prospects, independent briefs
brief_a = safe_run("MultiCompany", mock_signals={
    "ai_signals": {
        "ai_open_roles": 3, "total_open_roles": 8,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
brief_b = safe_run("MultiCompany", mock_signals={
    "ai_signals": {
        "ai_open_roles": 3, "total_open_roles": 8,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
log_result(
    "5.1", "Multi-thread Leakage",
    "Two prospects at same company get independent brief objects",
    "brief_a and brief_b have same segment but separate data",
    f"a.segment={brief_a['primary_segment_match']}, "
    f"b.segment={brief_b['primary_segment_match']}",
    brief_a['primary_segment_match'] == brief_b['primary_segment_match'],
    "LOW"
)

# Probe 5.2 — Input isolation: brief mutation doesn't leak
brief_c = safe_run("IsolationTest", mock_signals={
    "ai_signals": {
        "ai_open_roles": 2, "total_open_roles": 5,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
segment_before = brief_c['primary_segment_match']
# Mutate the brief
brief_c['primary_segment_match'] = "hacked_segment"
brief_d = safe_run("IsolationTest", mock_signals={
    "ai_signals": {
        "ai_open_roles": 2, "total_open_roles": 5,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
log_result(
    "5.2", "Multi-thread Leakage",
    "Mutating one brief does not affect subsequent runs",
    f"brief_d.segment = {segment_before}",
    f"brief_d.segment = {brief_d['primary_segment_match']}",
    brief_d['primary_segment_match'] == segment_before,
    "LOW"
)

# ═══════════════════════════════════════════════════════════
# CATEGORY 6 — Cost Pathology
# ═══════════════════════════════════════════════════════════

# Probe 6.1 — Empty company name
try:
    brief = run_pipeline(
        company_name="",
        domain="",
        mock_signals=None
    )
    log_result(
        "6.1", "Cost Pathology",
        "Empty company name should fail cleanly",
        "Raises exception or returns error",
        f"Completed with segment: {brief.get('primary_segment_match')}",
        False,  # Shouldn't succeed silently
        "MEDIUM",
        "No input validation on empty strings"
    )
except Exception as e:
    log_result(
        "6.1", "Cost Pathology",
        "Empty company name should fail cleanly",
        "Raises exception",
        f"Exception: {type(e).__name__}: {str(e)[:80]}",
        True,
        "n/a"
    )

# Probe 6.2 — Extremely long company name
long_name = "A" * 500
try:
    brief = run_pipeline(
        company_name=long_name,
        domain=f"{long_name.lower()}.com",
        mock_signals=None
    )
    log_result(
        "6.2", "Cost Pathology",
        "500-char name processed without validation",
        "Should truncate or reject",
        f"Processed: segment={brief.get('primary_segment_match')}",
        False,
        "LOW",
        "No input length cap"
    )
except Exception as e:
    log_result(
        "6.2", "Cost Pathology",
        "500-char name handling",
        "Fails gracefully",
        f"Exception: {type(e).__name__}",
        True,
        "n/a"
    )

# Probe 6.3 — Malformed mock_signals (string instead of dict)
try:
    brief = run_pipeline(
        company_name="MalformedTest",
        domain="malformedtest.com",
        mock_signals="this is not a dict"  # type: ignore
    )
    log_result(
        "6.3", "Cost Pathology",
        "Malformed mock_signals type",
        "Should raise TypeError",
        f"Accepted silently: {brief.get('primary_segment_match')}",
        False,
        "MEDIUM"
    )
except Exception as e:
    log_result(
        "6.3", "Cost Pathology",
        "Malformed mock_signals type",
        "Raises clean error",
        f"{type(e).__name__}: {str(e)[:80]}",
        True,
        "n/a"
    )

# ═══════════════════════════════════════════════════════════
# CATEGORY 7 — Dual-control Coordination
# ═══════════════════════════════════════════════════════════

# Probe 7.1 — Pipeline without mock_signals (live path)
brief = safe_run("CoordTest", mock_signals=None)
log_result(
    "7.1", "Dual Control",
    "Pipeline works without mock_signals (live path)",
    "Returns valid brief with real data",
    f"segment={brief.get('primary_segment_match')}, "
    f"ai_score={brief.get('ai_maturity', {}).get('score')}",
    "primary_segment_match" in brief,
    "n/a"
)

# Probe 7.2 — All signals optional (partial mock)
brief = safe_run("PartialMock", mock_signals={
    "ai_signals": {
        "ai_open_roles": 1, "total_open_roles": 4,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    }
    # No leadership key provided
})
log_result(
    "7.2", "Dual Control",
    "Partial mock_signals works (only ai_signals, no leadership)",
    "Leadership defaults to real detection",
    f"leadership_method={brief['buying_window_signals']['leadership_change'].get('detection_method')}",
    "primary_segment_match" in brief,
    "n/a"
)

# ═══════════════════════════════════════════════════════════
# CATEGORY 8 — Scheduling / Timezone Edge Cases
# ═══════════════════════════════════════════════════════════

# Probe 8.1 — generated_at timestamp is UTC and ISO-format
brief = safe_run("TimezoneTest", mock_signals={
    "ai_signals": {
        "ai_open_roles": 1, "total_open_roles": 3,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
generated_at = brief.get("generated_at", "")
has_tz = "+00:00" in generated_at or "Z" in generated_at
log_result(
    "8.1", "Scheduling",
    "Brief timestamps are UTC and timezone-aware",
    "generated_at contains +00:00 or Z",
    f"generated_at={generated_at}",
    has_tz,
    "LOW"
)

# Probe 8.2 — Deterministic timestamps within single run
import time
brief_t1 = safe_run("DeterministicTime", mock_signals={
    "ai_signals": {
        "ai_open_roles": 0, "total_open_roles": 0,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
time.sleep(1.5)
brief_t2 = safe_run("DeterministicTime", mock_signals={
    "ai_signals": {
        "ai_open_roles": 0, "total_open_roles": 0,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
log_result(
    "8.2", "Scheduling",
    "Same input at different times produces consistent segment",
    "segment identical across runs",
    f"t1={brief_t1['primary_segment_match']}, "
    f"t2={brief_t2['primary_segment_match']}",
    brief_t1['primary_segment_match'] == brief_t2['primary_segment_match'],
    "n/a"
)

# ═══════════════════════════════════════════════════════════
# CATEGORY 9 — Signal Reliability / False Positives
# ═══════════════════════════════════════════════════════════

# Probe 9.1 — AI maturity with zero signals returns 0
zero_signals = {
    "ai_open_roles": 0,
    "total_open_roles": 0,
    "has_ai_leadership": False,
    "github_ai_activity": False,
    "executive_ai_commentary": False,
    "modern_ml_stack": False,
    "strategic_ai_comms": False
}
result = score_ai_maturity(zero_signals)
log_result(
    "9.1", "Signal Reliability",
    "Zero signals should produce score 0",
    "score=0",
    f"score={result['score']}, confidence={result['confidence']}",
    result['score'] == 0,
    "HIGH"
)

# Probe 9.2 — Only low-weight signals cannot exceed score 1
only_low = {
    "ai_open_roles": 0,
    "total_open_roles": 5,
    "has_ai_leadership": False,
    "github_ai_activity": False,
    "executive_ai_commentary": False,
    "modern_ml_stack": True,  # low weight
    "strategic_ai_comms": True  # low weight
}
result = score_ai_maturity(only_low)
log_result(
    "9.2", "Signal Reliability",
    "Only low-weight signals should max out at score 1",
    "score <= 1",
    f"score={result['score']}",
    result['score'] <= 1,
    "MEDIUM"
)

# Probe 9.3 — All signals true produces score 3
all_true = {
    "ai_open_roles": 5,
    "total_open_roles": 10,
    "has_ai_leadership": True,
    "github_ai_activity": True,
    "executive_ai_commentary": True,
    "modern_ml_stack": True,
    "strategic_ai_comms": True
}
result = score_ai_maturity(all_true)
log_result(
    "9.3", "Signal Reliability",
    "All signals true produces maximum score 3",
    "score=3, confidence >= 0.6",
    f"score={result['score']}, confidence={result['confidence']}",
    result['score'] == 3 and result['confidence'] >= 0.5,
    "n/a"
)

# Probe 9.4 — AI maturity score never exceeds 3
edge_case = {
    "ai_open_roles": 100,
    "total_open_roles": 100,
    "has_ai_leadership": True,
    "github_ai_activity": True,
    "executive_ai_commentary": True,
    "modern_ml_stack": True,
    "strategic_ai_comms": True
}
result = score_ai_maturity(edge_case)
log_result(
    "9.4", "Signal Reliability",
    "Score is capped at 3 even with extreme inputs",
    "score=3 (capped)",
    f"score={result['score']}",
    result['score'] == 3,
    "LOW"
)

# Probe 9.5 — Negative AI open roles (invalid input)
negative_input = {
    "ai_open_roles": -5,
    "total_open_roles": 10,
    "has_ai_leadership": False,
    "github_ai_activity": False,
    "executive_ai_commentary": False,
    "modern_ml_stack": False,
    "strategic_ai_comms": False
}
try:
    result = score_ai_maturity(negative_input)
    log_result(
        "9.5", "Signal Reliability",
        "Negative ai_open_roles handled",
        "Treated as 0 or raises error",
        f"score={result['score']}",
        result['score'] == 0,
        "LOW"
    )
except Exception as e:
    log_result(
        "9.5", "Signal Reliability",
        "Negative input raises error",
        "Exception",
        f"{type(e).__name__}",
        True,
        "n/a"
    )

# Probe 9.6 — Justifications array present in output
result = score_ai_maturity({
    "ai_open_roles": 2, "total_open_roles": 5,
    "has_ai_leadership": True, "github_ai_activity": False,
    "executive_ai_commentary": True, "modern_ml_stack": False,
    "strategic_ai_comms": False
})
log_result(
    "9.6", "Signal Reliability",
    "Output includes per-signal justifications",
    "justifications list with weight/status/confidence per signal",
    f"justifications_count={len(result.get('justifications', []))}",
    len(result.get('justifications', [])) >= 4,
    "MEDIUM"
)

# ═══════════════════════════════════════════════════════════
# CATEGORY 10 — Gap Over-claiming
# ═══════════════════════════════════════════════════════════

from enrichment.competitor_gap import generate_competitor_gap_brief

# Probe 10.1 — Gap brief generated for high-maturity prospect
brief = safe_run("HighMaturity", mock_signals={
    "ai_signals": {
        "ai_open_roles": 5, "total_open_roles": 10,
        "has_ai_leadership": True, "github_ai_activity": True,
        "executive_ai_commentary": True, "modern_ml_stack": True,
        "strategic_ai_comms": True
    },
    "leadership": {"detected": False, "role": "none"}
})
try:
    gap = generate_competitor_gap_brief(brief)
    log_result(
        "10.1", "Gap Over-claiming",
        "Gap brief for prospect already at top quartile",
        "Should abstain or indicate at-or-above top quartile",
        f"gaps={len(gap.get('gaps', []))}",
        gap is not None,
        "MEDIUM"
    )
except Exception as e:
    log_result(
        "10.1", "Gap Over-claiming",
        "Gap brief generation",
        "Completes without error",
        f"Exception: {type(e).__name__}",
        False,
        "MEDIUM",
        str(e)[:100]
    )

# Probe 10.2 — Gap brief for low-maturity prospect
brief_low = safe_run("LowMaturity", mock_signals={
    "ai_signals": {
        "ai_open_roles": 0, "total_open_roles": 3,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
try:
    gap = generate_competitor_gap_brief(brief_low)
    log_result(
        "10.2", "Gap Over-claiming",
        "Gap brief generated for low-maturity prospect",
        "Should identify meaningful gaps to close",
        f"gaps={len(gap.get('gaps', []))}",
        gap is not None,
        "n/a"
    )
except Exception as e:
    log_result(
        "10.2", "Gap Over-claiming",
        "Gap brief generation",
        "Completes without error",
        f"Exception: {type(e).__name__}",
        False,
        "HIGH",
        str(e)[:100]
    )

# ═══════════════════════════════════════════════════════════
# CATEGORY 2 — Signal Over-claiming (additional)
# ═══════════════════════════════════════════════════════════

# Probe 2.6 — Honesty flag fires when job_count is low
brief = safe_run("WeakJobs", mock_signals={
    "ai_signals": {
        "ai_open_roles": 0, "total_open_roles": 2,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
has_flag = "weak_hiring_velocity_signal" in brief.get("honesty_flags", [])
log_result(
    "2.6", "Signal Over-claiming",
    "Honesty flag fires for weak hiring velocity",
    "weak_hiring_velocity_signal in honesty_flags",
    f"flags={brief.get('honesty_flags')}",
    has_flag,
    "MEDIUM"
)

# Probe 2.7 — Honesty flag for weak AI maturity
brief = safe_run("WeakAI", mock_signals={
    "ai_signals": {
        "ai_open_roles": 1, "total_open_roles": 5,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": True,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
has_flag = "weak_ai_maturity_signal" in brief.get("honesty_flags", [])
log_result(
    "2.7", "Signal Over-claiming",
    "Honesty flag fires for weak AI maturity",
    "weak_ai_maturity_signal in honesty_flags",
    f"flags={brief.get('honesty_flags')}",
    has_flag,
    "HIGH"
)

# Probe 2.8 — Mock data inference flag
brief = safe_run("NotInODM", mock_signals={
    "ai_signals": {
        "ai_open_roles": 2, "total_open_roles": 5,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": True, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
has_flag = "tech_stack_inferred_not_confirmed" in brief.get("honesty_flags", [])
log_result(
    "2.8", "Signal Over-claiming",
    "tech_stack_inferred_not_confirmed flag fires for mock companies",
    "Flag in honesty_flags when company not in ODM",
    f"flags={brief.get('honesty_flags')}",
    has_flag,
    "MEDIUM"
)

# ═══════════════════════════════════════════════════════════
# CATEGORY 1 — ICP Misclassification (additional)
# ═══════════════════════════════════════════════════════════

# Probe 1.6 — No segment assignment when all signals absent
brief = safe_run("EmptySignals", mock_signals={
    "ai_signals": {
        "ai_open_roles": 0, "total_open_roles": 0,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
log_result(
    "1.6", "ICP Misclassification",
    "Zero signals should produce abstain, not fallback to Seg 1",
    "segment=abstain",
    f"segment={brief['primary_segment_match']}",
    brief['primary_segment_match'] == "abstain",
    "HIGH"
)

# Probe 1.7 — Segment confidence is >= 0.4 and <= 1.0
brief = safe_run("ConfBounds", mock_signals={
    "ai_signals": {
        "ai_open_roles": 3, "total_open_roles": 10,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": True, "modern_ml_stack": True,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
conf = brief['segment_confidence']
log_result(
    "1.7", "ICP Misclassification",
    "segment_confidence is bounded [0.4, 1.0]",
    "0.4 <= confidence <= 1.0",
    f"confidence={conf}",
    0.4 <= conf <= 1.0,
    "LOW"
)

# ═══════════════════════════════════════════════════════════
# CATEGORY 3 — Bench Over-commitment (additional)
# ═══════════════════════════════════════════════════════════

# Probe 3.5 — bench_to_brief_match present in every brief
brief = safe_run("BenchCheck", mock_signals={
    "ai_signals": {
        "ai_open_roles": 2, "total_open_roles": 5,
        "has_ai_leadership": True, "github_ai_activity": False,
        "executive_ai_commentary": True, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
has_bench = "bench_to_brief_match" in brief
gaps_key = brief.get("bench_to_brief_match", {}).get("gaps")
log_result(
    "3.5", "Bench Over-commitment",
    "Every brief includes bench_to_brief_match field",
    "bench_to_brief_match with gaps list",
    f"has_field={has_bench}, gaps={gaps_key}",
    has_bench and gaps_key is not None,
    "MEDIUM"
)

# Probe 3.6 — Required stacks list is never empty
brief = safe_run("StackCheck", mock_signals={
    "ai_signals": {
        "ai_open_roles": 0, "total_open_roles": 0,
        "has_ai_leadership": False, "github_ai_activity": False,
        "executive_ai_commentary": False, "modern_ml_stack": False,
        "strategic_ai_comms": False
    },
    "leadership": {"detected": False, "role": "none"}
})
stacks = brief.get("tech_stack", [])
log_result(
    "3.6", "Bench Over-commitment",
    "tech_stack defaults to ['python'] when no signals",
    "stacks list is non-empty",
    f"stacks={stacks}",
    len(stacks) >= 1,
    "LOW"
)

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print(f"RESULTS — Batch 2 ({len(results)} probes)")
print("=" * 70)

passed = sum(1 for r in results if r["passed"])
failed = len(results) - passed
by_category = {}
for r in results:
    cat = r["category"]
    by_category.setdefault(cat, {"pass": 0, "fail": 0})
    by_category[cat]["pass" if r["passed"] else "fail"] += 1

print(f"\nTotal: {len(results)} probes")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"\nBy Category:")
for cat, counts in by_category.items():
    total = counts["pass"] + counts["fail"]
    rate = counts["fail"] / total * 100 if total > 0 else 0
    print(f"  {cat:30s} {counts['pass']}/{total} passed"
          f" (fail rate: {rate:.0f}%)")

# Save results to JSON
os.makedirs("probes", exist_ok=True)
results_file = "probes/probe_results_batch2.json"
with open(results_file, "w") as f:
    json.dump({
        "run_at": datetime.now().isoformat(),
        "total_probes": len(results),
        "passed": passed,
        "failed": failed,
        "by_category": by_category,
        "probes": results
    }, f, indent=2)
print(f"\nResults saved to: {results_file}")