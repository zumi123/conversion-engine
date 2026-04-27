import json
from enrichment.pipeline import run_pipeline


def run_probe(name, company_name, mock_signals,
              expected_segment, expected_to_pass=True):
    """Run one adversarial probe."""
    print(f"\n── Probe: {name} ──")

    brief = run_pipeline(
        company_name=company_name,
        domain=f"{company_name.lower().replace(' ', '')}.com",
        mock_signals=mock_signals
    )

    actual = brief["primary_segment_match"]
    confidence = brief["segment_confidence"]
    ai_score = brief["ai_maturity"]["score"]
    ai_conf = brief["ai_maturity"]["confidence"]

    match = actual == expected_segment
    if expected_to_pass:
        passed = match
    else:
        passed = not match  # we WANT it to not match

    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  Expected segment: {expected_segment}")
    print(f"  Actual: {actual} (confidence: {confidence})")
    print(f"  AI maturity: {ai_score}/3 (conf: {ai_conf})")
    print(f"  Honesty flags: {brief.get('honesty_flags')}")
    print(f"  Status: {status}")
    return brief, passed


print("=" * 60)
print("Advanced Adversarial Probes — Designed to Break System")
print("=" * 60)

# ── Probe A: ALL signals flipped to true (maximum over-claim) ──
probe_a, _ = run_probe(
    "A. All AI signals true — should score 3 but bypass filters",
    "FakeAICorp",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 10,
            "total_open_roles": 10,
            "has_ai_leadership": True,
            "github_ai_activity": True,
            "executive_ai_commentary": True,
            "modern_ml_stack": True,
            "strategic_ai_comms": True
        },
        "leadership": {
            "detected": False,
            "role": "none"
        }
    },
    expected_segment="segment_4_specialized_capability"
)
# Question: does the system accept 3/3 AI maturity
# from PURELY mocked data without verification?

# ── Probe B: Recent CTO + tiny company (should fail filter) ──
probe_b, _ = run_probe(
    "B. New CTO at 10-person startup — should fail 50-500 headcount rule",
    "NewCTOTiny",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 0,
            "total_open_roles": 2,
            "has_ai_leadership": False,
            "github_ai_activity": False,
            "executive_ai_commentary": False,
            "modern_ml_stack": False,
            "strategic_ai_comms": False
        },
        "leadership": {
            "detected": True,
            "role": "cto",
            "new_leader_name": "Jane Test",
            "started_at": "2026-03-01",
            "source_url": "https://example.com",
            "signal_confidence": "high"
        }
    },
    expected_segment="abstain"
    # Should abstain because mock crunchbase has 45 employees
    # which is below 50 threshold — but does it check?
)

# ── Probe C: New CTO with medium-sized company (should fire Segment 3) ──
probe_c, _ = run_probe(
    "C. New CTO with 45-person company (mock default)",
    "CTOMidCo",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 2,
            "total_open_roles": 10,
            "has_ai_leadership": False,
            "github_ai_activity": False,
            "executive_ai_commentary": False,
            "modern_ml_stack": False,
            "strategic_ai_comms": False
        },
        "leadership": {
            "detected": True,
            "role": "cto",
            "new_leader_name": "John Smith",
            "started_at": "2026-02-15",
            "source_url": "https://example.com",
            "signal_confidence": "high"
        }
    },
    expected_segment="segment_3_leadership_transition"
)

# ── Probe D: Low AI confidence but high score — HONESTY probe ──
probe_d, _ = run_probe(
    "D. AI score 3 with ONLY low-confidence inputs (mock abuse)",
    "WeakEvidenceAI",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 3,
            "total_open_roles": 5,
            "has_ai_leadership": True,
            "github_ai_activity": False,
            "executive_ai_commentary": False,
            "modern_ml_stack": True,
            "strategic_ai_comms": False
        },
        "leadership": {
            "detected": False,
            "role": "none"
        }
    },
    expected_segment="segment_4_specialized_capability"
    # This SHOULD succeed (score >=2 routes to seg 4)
    # But the brief should flag the LOW confidence somewhere
)

# ── Probe E: Exact boundary AI score = 2 ──
probe_e, _ = run_probe(
    "E. AI score exactly 2 — classifies Seg 4 even if weak?",
    "BoundaryCo",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 1,
            "total_open_roles": 5,
            "has_ai_leadership": True,
            "github_ai_activity": False,
            "executive_ai_commentary": False,
            "modern_ml_stack": False,
            "strategic_ai_comms": False
        },
        "leadership": {
            "detected": False,
            "role": "none"
        }
    },
    expected_segment="segment_4_specialized_capability"
)

# ── Probe F: Zero AI signals but high hiring — Segment 1 test ──
probe_f, _ = run_probe(
    "F. No AI but 8 open roles — should classify Segment 1",
    "ScalingStartup",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 0,
            "total_open_roles": 8,
            "has_ai_leadership": False,
            "github_ai_activity": False,
            "executive_ai_commentary": False,
            "modern_ml_stack": False,
            "strategic_ai_comms": False
        },
        "leadership": {
            "detected": False,
            "role": "none"
        }
    },
    expected_segment="segment_1_series_a_b"
    # Should trigger Seg 1 because mock has fresh funding
    # BUT job_count from RemoteOK will be 0 — so it abstains?
)

# ── Probe G: Repeat company — dedup test ──
probe_g1, _ = run_probe(
    "G1. First run — Acme AI",
    "AcmeRepeatTest",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 3,
            "total_open_roles": 10,
            "has_ai_leadership": True,
            "github_ai_activity": False,
            "executive_ai_commentary": True,
            "modern_ml_stack": True,
            "strategic_ai_comms": False
        },
        "leadership": {
            "detected": False,
            "role": "none"
        }
    },
    expected_segment="segment_4_specialized_capability"
)

probe_g2, _ = run_probe(
    "G2. Second run — same company — should produce same classification",
    "AcmeRepeatTest",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 3,
            "total_open_roles": 10,
            "has_ai_leadership": True,
            "github_ai_activity": False,
            "executive_ai_commentary": True,
            "modern_ml_stack": True,
            "strategic_ai_comms": False
        },
        "leadership": {
            "detected": False,
            "role": "none"
        }
    },
    expected_segment="segment_4_specialized_capability"
)

# Check determinism
g1_seg = probe_g1["primary_segment_match"]
g2_seg = probe_g2["primary_segment_match"]
print(f"\n\n── Determinism Check ──")
print(f"  Run 1: {g1_seg}")
print(f"  Run 2: {g2_seg}")
print(f"  Deterministic: {g1_seg == g2_seg}")


print("\n" + "=" * 60)
print("SUMMARY — Findings")
print("=" * 60)
print(f"Probe A (all signals mocked): {probe_a['primary_segment_match']}"
      f" — AI score {probe_a['ai_maturity']['score']}/3")
print(f"Probe B (tiny startup new CTO): {probe_b['primary_segment_match']}"
      f" — tests 50-500 gate")
print(f"Probe C (45-emp new CTO): {probe_c['primary_segment_match']}")
print(f"Probe D (weak evidence AI): {probe_d['primary_segment_match']}"
      f" — AI conf {probe_d['ai_maturity']['confidence']}")
print(f"Probe E (boundary score 2): {probe_e['primary_segment_match']}"
      f" — AI conf {probe_e['ai_maturity']['confidence']}")
print(f"Probe F (hiring no AI): {probe_f['primary_segment_match']}")
print(f"Probe G (determinism): {g1_seg == g2_seg}")