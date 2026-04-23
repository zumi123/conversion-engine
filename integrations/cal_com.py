import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CAL_API_KEY = os.environ.get("CALCOM_API_KEY", "")
EVENT_TYPE_ID = os.environ.get("CALCOM_EVENT_TYPE_ID", "")
CAL_BASE_URL = "https://api.cal.com/v2"


def get_headers() -> dict:
    """Get Cal.com v2 API headers."""
    return {
        "Authorization": f"Bearer {CAL_API_KEY}",
        "cal-api-version": "2024-08-13",
        "Content-Type": "application/json"
    }


def get_available_slots(days_ahead: int = 7) -> list:
    """
    Get available booking slots from Cal.com v2.
    """
    try:
        start_time = datetime.now()
        end_time = start_time + timedelta(days=days_ahead)

        response = requests.get(
            f"{CAL_BASE_URL}/slots/available",
            headers=get_headers(),
            params={
                "eventTypeId": EVENT_TYPE_ID,
                "startTime": start_time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "endTime": end_time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "timeZone": "UTC"
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            slots = []
            slot_data = data.get("data", {}).get("slots", {})
            for date, times in slot_data.items():
                for slot in times:
                    slots.append({
                        "date": date,
                        "time": slot.get("time"),
                        "available": True
                    })
            print(f"  Found {len(slots)} real slots")
            return slots
        else:
            print(f"  Cal.com slots error: {response.text}")
            return _mock_slots()

    except Exception as e:
        print(f"  Cal.com error: {e}")
        return _mock_slots()


def _mock_slots() -> list:
    """Return mock slots for testing."""
    slots = []
    base = datetime.now() + timedelta(days=1)
    for i in range(3):
        slot_time = base + timedelta(days=i, hours=10)
        slots.append({
            "date": slot_time.strftime("%Y-%m-%d"),
            "time": slot_time.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "available": True
        })
    return slots


def book_discovery_call(
    prospect_email: str,
    prospect_name: str,
    brief: dict,
    slot_time: str = None
) -> dict:
    """
    Book a discovery call on Cal.com v2.
    """
    # Get available slot if none provided
    if not slot_time:
        slots = get_available_slots()
        if not slots:
            return {
                "status": "error",
                "error": "No available slots found"
            }
        slot_time = slots[0]["time"]

    # Build context brief
    company = brief["prospect_name"]
    segment = brief["primary_segment_match"]
    ai_score = brief["ai_maturity"]["score"]
    funding = brief["buying_window_signals"]["funding_event"]
    bench = brief["bench_to_brief_match"]

    funding_str = "None detected"
    if funding.get("detected"):
        amount = funding.get("amount_usd", 0)
        stage = funding.get(
            "stage", ""
        ).replace("_", " ").title()
        funding_str = f"{stage} ${amount/1_000_000:.1f}M"

    context_notes = f"""=== Discovery Call Context Brief ===
Company: {company}
Segment: {segment.replace('_', ' ').upper()}
AI Maturity: {ai_score}/3
Funding: {funding_str}
Bench Match: {'Available' if bench['bench_available'] else 'Gap: ' + ', '.join(bench['gaps'])}
Required Stacks: {', '.join(bench['required_stacks'])}

Key Talking Points:
- Prospect responded to {segment.replace('_', ' ')} pitch
- AI maturity score: {ai_score}/3
- Bench is {'ready' if bench['bench_available'] else 'has gaps for: ' + ', '.join(bench['gaps'])}

Do NOT quote pricing outside the public tier bands.
Route scope questions to this call.
"""

    try:
        # Split name
        name_parts = prospect_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        response = requests.post(
            f"{CAL_BASE_URL}/bookings",
            headers=get_headers(),
            json={
                "eventTypeId": int(EVENT_TYPE_ID),
                "start": slot_time,
                "attendee": {
                    "name": prospect_name,
                    "email": prospect_email,
                    "timeZone": "UTC",
                    "language": "en"
                },
                "metadata": {
                    "company": company,
                    "segment": segment,
                    "ai_maturity": str(ai_score),
                    "source": "conversion-engine",
                    "context_brief": context_notes
                }
            },
            timeout=15
        )

        if response.status_code in [200, 201]:
            booking = response.json()
            data = booking.get("data", booking)
            print(f"  Booking created: {data.get('id')}")
            return {
                "status": "success",
                "booking_id": data.get("id"),
                "booking_uid": data.get("uid"),
                "start_time": slot_time,
                "prospect_email": prospect_email,
                "prospect_name": prospect_name,
                "company": company,
                "context_brief": context_notes
            }
        else:
            print(f"  Booking error: {response.text}")
            return _mock_booking(
                prospect_email, prospect_name,
                company, slot_time, context_notes
            )

    except Exception as e:
        print(f"  Cal.com booking error: {e}")
        return _mock_booking(
            prospect_email, prospect_name,
            company, slot_time, context_notes
        )


def _mock_booking(
    email, name, company,
    slot_time, context_notes
) -> dict:
    """Return mock booking for testing."""
    return {
        "status": "mock_success",
        "booking_id": "mock_12345",
        "booking_uid": "mock-uid-abc123",
        "start_time": slot_time,
        "prospect_email": email,
        "prospect_name": name,
        "company": company,
        "context_brief": context_notes,
        "note": "Mock booking - Cal.com API unavailable"
    }