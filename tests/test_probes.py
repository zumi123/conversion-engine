import json
import sys
from enrichment.pipeline import run_pipeline


def run_probe(name, company_name, mock_signals, expected_segment):
    """Run one adversarial probe."""
    print(f"\n── Probe: {name} ──")

    brief = run_pipeline(
        company_name=company_name,
        domain=f"{company_name.lower().replace(' ', '')}.com",
        mock_signals=mock_signals
    )

    actual = brief["primary_segment_match"]
    confidence = brief["segment_confidence"]

    passed = actual == expected_segment
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  Expected: {expected_segment}")
    print(f"  Actual:   {actual} (confidence: {confidence})")
    print(f"  Status:   {status}")

    return passed


# Probe 1.3 — High score, low confidence
print("=" * 60)
print("Running Adversarial Probes")
print("=" * 60)

probe_1_3 = run_probe(
    "1.3 High AI score, low confidence",
    "WeakSignalCo",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 2,
            "total_open_roles": 5,
            "has_ai_leadership": False,
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
    expected_segment="abstain"
)

# Probe 2.4 — AI roles are marketing, not engineering
probe_2_4 = run_probe(
    "2.4 AI role false positives",
    "MarketingAICo",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 5,
            "total_open_roles": 10,
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
    expected_segment="abstain"
)

# Probe 1.5 — Too-small Series A startup
probe_1_5 = run_probe(
    "1.5 Small Series A (10 employees)",
    "TinyStartup",
    mock_signals={
        "ai_signals": {
            "ai_open_roles": 0,
            "total_open_roles": 5,
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
    expected_segment="abstain"
)

print("\n" + "=" * 60)
print("Probe Results Summary")
print("=" * 60)
passed = sum([probe_1_3, probe_2_4, probe_1_5])
total = 3
print(f"Passed: {passed}/{total}")