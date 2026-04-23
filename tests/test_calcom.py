import json
from integrations.cal_com import (
    get_available_slots,
    book_discovery_call
)

# Load brief
with open(
    "outputs/hiring_signal_brief_acme_ai.json"
) as f:
    brief = json.load(f)

print("=== Testing Cal.com Integration ===\n")

# Step 1 - Get available slots
print("Step 1: Getting available slots...")
slots = get_available_slots(days_ahead=7)
print(f"  Found {len(slots)} available slots")
if slots:
    print(f"  First slot: {slots[0]['time']}")

# Step 2 - Book a discovery call
print("\nStep 2: Booking discovery call...")
booking = book_discovery_call(
    prospect_email="alex.chen@acme-ai.com",
    prospect_name="Alex Chen",
    brief=brief
)

print("\nBooking result:")
print(json.dumps(booking, indent=2))