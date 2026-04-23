import json
from integrations.hubspot import create_or_update_prospect
from agent.email_handler import compose_email

# Load brief
with open("outputs/hiring_signal_brief_acme_ai.json") as f:
    brief = json.load(f)

# Compose email
email_draft = compose_email(brief)

print("=== Testing HubSpot Integration ===\n")

# Create contact with enrichment
result = create_or_update_prospect(
    brief=brief,
    email="test.prospect@acme-ai.com",
    contact_name="Alex Chen",
    email_draft=email_draft
)

print("\nResult:")
print(json.dumps(result, indent=2))