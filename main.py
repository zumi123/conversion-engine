from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
import resend
import os
import json
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    Plug your qualification agent in here.
    """
    logger.info(f"Reply from {from_email}: {body[:100]}")
    # TODO Act III: route to qualification agent
    return {"from": from_email, "handled": True}


def handle_bounce(email_id: str, reason: str):
    """
    Handle bounced emails.
    Logs to HubSpot and marks contact as invalid.
    """
    logger.warning(f"Bounce for {email_id}: {reason}")
    # TODO: update HubSpot contact status to invalid
    return {"email_id": email_id, "handled": True}


def handle_spam_complaint(email_id: str):
    """Handle spam complaints — suppress contact."""
    logger.warning(f"Spam complaint for {email_id}")
    return {"email_id": email_id, "suppressed": True}


@app.post("/webhooks/resend")
async def handle_resend_webhook(request: Request):
    """
    Receive Resend webhook events.
    Handles: delivered, bounced, complained, replied.
    Explicit handling for malformed payloads.
    """
    # Handle malformed payload
    try:
        body = await request.body()
        if not body:
            logger.error("Empty webhook payload")
            return Response(
                content=json.dumps({
                    "status": "error",
                    "reason": "empty_payload"
                }),
                status_code=400,
                media_type="application/json"
            )
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Malformed JSON payload: {e}")
        return Response(
            content=json.dumps({
                "status": "error",
                "reason": "malformed_json"
            }),
            status_code=400,
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Payload parse error: {e}")
        return Response(
            content=json.dumps({
                "status": "error",
                "reason": "parse_error"
            }),
            status_code=400,
            media_type="application/json"
        )

    # Validate required fields
    event_type = payload.get("type")
    if not event_type:
        logger.error("Missing event type in payload")
        return Response(
            content=json.dumps({
                "status": "error",
                "reason": "missing_event_type"
            }),
            status_code=400,
            media_type="application/json"
        )

    data = payload.get("data", {})
    if not isinstance(data, dict):
        logger.error("Invalid data field in payload")
        return Response(
            content=json.dumps({
                "status": "error",
                "reason": "invalid_data_field"
            }),
            status_code=400,
            media_type="application/json"
        )

    # Route by event type
    try:
        if event_type == "email.delivered":
            email_id = data.get("email_id", "unknown")
            logger.info(f"Email delivered: {email_id}")

        elif event_type == "email.bounced":
            email_id = data.get("email_id", "unknown")
            bounce_info = data.get("bounce", {})
            reason = bounce_info.get(
                "message", "unknown bounce reason"
            )
            handle_bounce(email_id, reason)

        elif event_type == "email.complained":
            email_id = data.get("email_id", "unknown")
            handle_spam_complaint(email_id)

        elif event_type == "email.replied":
            reply = data.get("reply", {})
            if not reply:
                logger.warning("Reply event with no reply data")
                return {"status": "ok", "note": "empty_reply"}

            from_email = reply.get("from", "")
            subject = reply.get("subject", "")
            body_text = reply.get("text", "")
            email_id = data.get("email_id", "")

            if not from_email:
                logger.warning("Reply missing from address")
                return {
                    "status": "ok",
                    "note": "missing_from"
                }

            # Mark as warm lead for SMS channel
            from agent.sms_handler import mark_as_warm_lead
            mark_as_warm_lead(from_email)

            handle_email_reply(
                from_email=from_email,
                subject=subject,
                body=body_text,
                email_id=email_id
            )

        elif event_type == "email.opened":
            logger.info(
                f"Email opened: {data.get('email_id')}"
            )

        else:
            logger.info(f"Unhandled event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing event {event_type}: {e}")
        return Response(
            content=json.dumps({
                "status": "error",
                "reason": "processing_error",
                "event_type": event_type
            }),
            status_code=500,
            media_type="application/json"
        )

    return {"status": "ok", "event_type": event_type}


@app.post("/webhooks/sms")
async def handle_sms(request: Request):
    """
    Receive Africa's Talking inbound SMS.
    Routes to downstream SMS handler.
    """
    try:
        form = await request.form()
    except Exception as e:
        logger.error(f"Malformed SMS payload: {e}")
        return Response(
            content=json.dumps({
                "status": "error",
                "reason": "malformed_payload"
            }),
            status_code=400,
            media_type="application/json"
        )

    sender = form.get("from", "")
    message = form.get("text", "")

    if not sender or not message:
        logger.warning(
            f"SMS missing fields — from: {sender}, "
            f"text: {message}"
        )
        return {"status": "ok", "note": "missing_fields"}

    logger.info(f"SMS from {sender}: {message}")

    from agent.sms_handler import handle_inbound_sms
    result = handle_inbound_sms(sender, message)

    return {"status": "ok", "result": result}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}