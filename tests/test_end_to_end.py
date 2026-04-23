import json
from agent.orchestrator import run_full_flow

print("=== End-to-End Flow Test ===\n")

# Test with synthetic prospect
result = run_full_flow(
    company_name="Acme AI",
    prospect_email="alex.chen@acme-ai.com",
    prospect_name="Alex Chen",
    domain="acme-ai.com",
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
            "role": "none",
            "new_leader_name": None,
            "started_at": None,
            "source_url": None
        }
    },
    dry_run=True  # Change to False to actually send email
)

print("\n=== Flow Summary ===")
for step, data in result["steps"].items():
    status = data.get("status", "unknown")
    icon = "✅" if status in [
        "success", "mock_success", "dry_run", "skipped"
    ] else "❌"
    print(f"{icon} {step}: {status}")

print(f"\nOverall: {result['status']}")