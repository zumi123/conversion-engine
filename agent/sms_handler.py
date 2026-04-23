import africastalking
import os
from dotenv import load_dotenv

load_dotenv()

africastalking.initialize(
    username=os.environ["AFRICASTALKING_USERNAME"],
    api_key=os.environ["AFRICASTALKING_API_KEY"]
)

sms = africastalking.SMS

# In-memory store of warm leads
# (prospects who have replied by email)
# In production this would be HubSpot CRM lookup
warm_leads = set()


def mark_as_warm_lead(phone_number: str):
    """
    Mark a prospect as warm lead after email reply.
    SMS is only sent to warm leads per channel hierarchy:
    Email first → SMS only after email reply.
    """
    warm_leads.add(phone_number)
    print(f"  Marked {phone_number} as warm lead")


def is_warm_lead(phone_number: str) -> bool:
    """
    Check if prospect has replied by email.
    SMS channel is gated on prior email reply.
    """
    return phone_number in warm_leads


def send_sms(phone_number: str, message: str) -> dict:
    """
    Send SMS to prospect.
    CHANNEL HIERARCHY: SMS is secondary channel.
    Only sends to warm leads who have replied by email.
    Cold outreach goes via email only.
    """
    # Enforce channel hierarchy
    if not is_warm_lead(phone_number):
        print(
            f"  ⚠️  SMS blocked for {phone_number} — "
            f"not a warm lead. "
            f"Channel hierarchy: email first, "
            f"SMS only after email reply."
        )
        return {
            "status": "blocked",
            "reason": "channel_hierarchy",
            "message": (
                "SMS requires prior email reply. "
                "Send email first."
            )
        }

    try:
        response = sms.send(message, [phone_number])
        print(f"SMS sent to {phone_number}: {response}")
        return {
            "status": "sent",
            "response": response
        }
    except Exception as e:
        print(f"SMS send error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def handle_inbound_sms(
    phone_number: str,
    message: str
) -> dict:
    """
    Handle inbound SMS from prospect.
    Routes to scheduling flow for warm leads.
    """
    print(f"  Inbound SMS from {phone_number}: {message}")

    # Handle STOP command (TCPA compliance)
    if message.strip().upper() in ["STOP", "UNSUB", "UNSUBSCRIBE"]:
        warm_leads.discard(phone_number)
        print(f"  Unsubscribed: {phone_number}")
        return {
            "status": "unsubscribed",
            "phone": phone_number
        }

    # Handle HELP command
    if message.strip().upper() == "HELP":
        send_sms(
            phone_number,
            "Tenacious Intelligence. "
            "Reply STOP to unsubscribe."
        )
        return {"status": "help_sent"}

    # Route warm leads to scheduling
    if is_warm_lead(phone_number):
        print(
            f"  Routing warm lead {phone_number} "
            f"to scheduling flow"
        )
        return {
            "status": "routed_to_scheduling",
            "phone": phone_number,
            "message": message
        }

    return {
        "status": "received",
        "phone": phone_number,
        "message": message
    }