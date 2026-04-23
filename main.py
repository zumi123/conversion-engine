from fastapi import FastAPI, Request
from dotenv import load_dotenv
import resend
import os
import json

load_dotenv()

app = FastAPI()
resend.api_key = os.environ["RESEND_API_KEY"]


def handle_email_reply(
    from_email: str,
    subject: str,
    body: str,
    email_id: str
):
    """
    Downstream handler for inbound email replies.
    Called by webhook when prospect replies.
    """
    print(f"Reply from {from_email}: {body[:100]}")
    # Route to qualification agent
    # This is where Act II conversation continues


def handle_bounce(email_id: str, reason: str):
    """Handle bounced emails."""
    print(f"Bounce for {email_id}: {reason}")
    # Log to HubSpot, mark contact as invalid


@app.post("/webhooks/resend")
async def handle_resend_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "reason": "malformed_payload"}

    event_type = payload.get("type", "")

    try:
        if event_type == "email.delivered":
            print(f"Delivered: {payload.get('data', {}).get('email_id')}")

        elif event_type == "email.bounced":
            data = payload.get("data", {})
            handle_bounce(
                email_id=data.get("email_id", ""),
                reason=data.get("bounce", {}).get("message", "unknown")
            )

        elif event_type == "email.replied":
            data = payload.get("data", {})
            reply = data.get("reply", {})
            handle_email_reply(
                from_email=reply.get("from", ""),
                subject=reply.get("subject", ""),
                body=reply.get("text", ""),
                email_id=data.get("email_id", "")
            )

        else:
            print(f"Unhandled event: {event_type}")

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"status": "error", "reason": str(e)}

    return {"status": "ok"}


@app.post("/webhooks/sms")
async def handle_sms(request: Request):
    try:
        form = await request.form()
    except Exception:
        return {"status": "error", "reason": "malformed_payload"}

    sender = form.get("from", "")
    message = form.get("text", "")

    print(f"SMS from {sender}: {message}")

    # Route to downstream SMS handler
    from agent.sms_handler import handle_inbound_sms
    handle_inbound_sms(sender, message)

    return {"status": "ok"}