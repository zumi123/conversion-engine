import json
from agent.email_handler import compose_email, check_tone, send_email

# Load the brief we generated earlier
with open("outputs/hiring_signal_brief_acme_ai.json", "r") as f:
    brief = json.load(f)

print("=== Testing Email Agent ===\n")

# Step 1 - Compose email
print("Step 1: Composing email from brief...")
email = compose_email(brief)
print(f"  Segment: {email['segment']}")
print(f"  Subject: {email['subject']}")
print(f"  Word count: {email['word_count']}")

# Step 2 - Tone check
print("\nStep 2: Checking tone...")
tone = check_tone(email)
print(f"  Tone score: {tone['tone_score']}/5")
if tone['violations']:
    print(f"  Violations: {tone['violations']}")
else:
    print("  No violations!")

# Step 3 - Send (dry run)
print("\nStep 3: Sending email (dry run)...")
result = send_email(
    to_email="test@example.com",
    email_draft=email,
    prospect_name="Acme AI",
    dry_run=True  # Change to False to actually send
)

print("\n=== Done ===")
print(f"Status: {result['status']}")