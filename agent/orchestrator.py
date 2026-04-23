import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

from enrichment.pipeline import run_pipeline
from agent.email_handler import compose_email, send_email, check_tone
from integrations.hubspot import (
    create_or_update_prospect,
    log_email_sent,
    _add_note,
    get_client
)
from integrations.cal_com import book_discovery_call

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ["LANGFUSE_HOST"]
)


def run_full_flow(
    company_name: str,
    prospect_email: str,
    prospect_name: str,
    domain: str = None,
    mock_signals: dict = None,
    dry_run: bool = True
) -> dict:
    """
    Run the full end-to-end flow for one prospect:
    1. Enrich prospect with hiring signal brief
    2. Compose personalized email
    3. Log to HubSpot
    4. Send email (or dry run)
    5. Book discovery call if high confidence
       → triggers second HubSpot write with booking ref

    Channel hierarchy enforced:
    - Email is primary outreach channel
    - SMS only after prospect replies to email (warm lead)
    - Voice is final channel: discovery call booked by agent,
      delivered by human Tenacious delivery lead

    Returns full trace of all actions taken.
    """
    # Start timing for latency tracking
    flow_start = time.time()

    trace = {
        "prospect": {
            "company": company_name,
            "email": prospect_email,
            "name": prospect_name,
            "domain": domain
        },
        "started_at": datetime.now().isoformat(),
        "steps": {},
        "status": "running",
        "latency": {},
        "channel_hierarchy": {
            "primary": "email",
            "secondary": "sms_after_email_reply",
            "final": "voice_discovery_call"
        }
    }

    print(f"\n{'='*50}")
    print(f"Starting flow for: {company_name}")
    print(f"{'='*50}")

    # Create Langfuse trace ID for this prospect
    lf_trace_id = langfuse.create_trace_id()

    # ── Step 1: Enrichment ──
    print("\n[Step 1] Running enrichment pipeline...")
    step_start = time.time()

    with langfuse.start_as_current_observation(
        name=f"enrichment-{company_name}",
        input={
            "company": company_name,
            "domain": domain
        }
    ):
        try:
            brief = run_pipeline(
                company_name=company_name,
                domain=domain,
                mock_signals=mock_signals
            )
            step_latency = time.time() - step_start
            trace["steps"]["enrichment"] = {
                "status": "success",
                "segment": brief["primary_segment_match"],
                "confidence": brief["segment_confidence"],
                "ai_maturity": brief["ai_maturity"]["score"],
                "honesty_flags": brief.get("honesty_flags", []),
                "latency_seconds": round(step_latency, 2),
                "completed_at": datetime.now().isoformat()
            }
            trace["latency"]["enrichment"] = round(
                step_latency, 2
            )
            langfuse.update_current_span(
                output={
                    "segment": brief["primary_segment_match"],
                    "confidence": brief["segment_confidence"],
                    "ai_maturity": brief["ai_maturity"]["score"]
                }
            )
            print(f"  ✅ Segment: {brief['primary_segment_match']}")
            print(f"  ✅ AI Maturity: {brief['ai_maturity']['score']}/3")
            print(f"  ✅ Latency: {step_latency:.2f}s")
        except Exception as e:
            trace["steps"]["enrichment"] = {
                "status": "error",
                "error": str(e)
            }
            trace["status"] = "failed"
            print(f"  ❌ Enrichment failed: {e}")
            langfuse.flush()
            return trace

    # ── Step 2: Compose Email ──
    print("\n[Step 2] Composing email...")
    step_start = time.time()

    with langfuse.start_as_current_observation(
        name=f"email-composition-{company_name}",
        input={
            "segment": brief["primary_segment_match"],
            "ai_maturity": brief["ai_maturity"]["score"]
        }
    ):
        try:
            email_draft = compose_email(brief)
            tone_check = check_tone(email_draft)
            step_latency = time.time() - step_start

            trace["steps"]["email_composition"] = {
                "status": "success",
                "subject": email_draft["subject"],
                "word_count": email_draft["word_count"],
                "tone_score": tone_check["tone_score"],
                "tone_violations": tone_check["violations"],
                "segment": email_draft["segment"],
                "latency_seconds": round(step_latency, 2),
                "completed_at": datetime.now().isoformat()
            }
            trace["latency"]["email_composition"] = round(
                step_latency, 2
            )
            langfuse.update_current_span(
                output={
                    "subject": email_draft["subject"],
                    "tone_score": tone_check["tone_score"],
                    "word_count": email_draft["word_count"],
                    "violations": tone_check["violations"]
                }
            )
            print(f"  ✅ Subject: {email_draft['subject']}")
            print(f"  ✅ Tone: {tone_check['tone_score']}/5")
            print(f"  ✅ Latency: {step_latency:.2f}s")

            if not tone_check["passed"]:
                print(
                    f"  ⚠️  Violations: {tone_check['violations']}"
                )

        except Exception as e:
            trace["steps"]["email_composition"] = {
                "status": "error",
                "error": str(e)
            }
            trace["status"] = "failed"
            print(f"  ❌ Email composition failed: {e}")
            langfuse.flush()
            return trace

    # ── Step 3: Log to HubSpot (first write) ──
    # Records ICP segment, signal enrichment data,
    # and enrichment timestamp
    print("\n[Step 3] Logging to HubSpot...")
    step_start = time.time()
    contact_id = None

    with langfuse.start_as_current_observation(
        name=f"hubspot-{company_name}",
        input={
            "email": prospect_email,
            "company": company_name,
            "segment": brief["primary_segment_match"],
            "enrichment_timestamp": brief["generated_at"]
        }
    ):
        try:
            hubspot_result = create_or_update_prospect(
                brief=brief,
                email=prospect_email,
                contact_name=prospect_name,
                email_draft=email_draft
            )
            step_latency = time.time() - step_start
            contact_id = hubspot_result.get("contact_id")

            trace["steps"]["hubspot_enrichment"] = {
                "status": hubspot_result["status"],
                "contact_id": contact_id,
                "icp_segment": brief["primary_segment_match"],
                "enrichment_timestamp": brief["generated_at"],
                "latency_seconds": round(step_latency, 2),
                "completed_at": datetime.now().isoformat()
            }
            trace["latency"]["hubspot"] = round(step_latency, 2)
            langfuse.update_current_span(
                output={
                    "contact_id": contact_id,
                    "status": hubspot_result["status"]
                }
            )
            print(f"  ✅ Contact ID: {contact_id}")
            print(
                f"  ✅ ICP segment logged: "
                f"{brief['primary_segment_match']}"
            )
            print(f"  ✅ Latency: {step_latency:.2f}s")
        except Exception as e:
            step_latency = time.time() - step_start
            trace["steps"]["hubspot_enrichment"] = {
                "status": "error",
                "error": str(e),
                "latency_seconds": round(step_latency, 2)
            }
            print(f"  ⚠️  HubSpot failed (non-critical): {e}")

    # ── Step 4: Send Email (primary channel) ──
    # Email is ALWAYS the first outreach channel.
    # SMS is only used after prospect replies to email.
    print("\n[Step 4] Sending email (primary channel)...")
    step_start = time.time()

    with langfuse.start_as_current_observation(
        name=f"email-send-{company_name}",
        input={
            "to": prospect_email,
            "subject": email_draft["subject"],
            "dry_run": dry_run,
            "channel": "email_primary"
        }
    ):
        try:
            email_result = send_email(
                to_email=prospect_email,
                email_draft=email_draft,
                prospect_name=prospect_name,
                dry_run=dry_run
            )
            step_latency = time.time() - step_start
            trace["steps"]["email_sent"] = {
                "status": email_result["status"],
                "to": prospect_email,
                "subject": email_draft["subject"],
                "dry_run": dry_run,
                "channel": "email_primary",
                "channel_note": (
                    "Email is primary channel. "
                    "SMS only sent after prospect replies."
                ),
                "latency_seconds": round(step_latency, 2),
                "completed_at": datetime.now().isoformat()
            }
            trace["latency"]["email_send"] = round(
                step_latency, 2
            )
            langfuse.update_current_span(
                output={
                    "status": email_result["status"],
                    "email_id": email_result.get("email_id"),
                    "channel": "email_primary"
                }
            )
            print(f"  ✅ Email status: {email_result['status']}")
            print(
                f"  ✅ Channel: email (primary) — "
                f"SMS gated on reply"
            )
            print(f"  ✅ Latency: {step_latency:.2f}s")
        except Exception as e:
            step_latency = time.time() - step_start
            trace["steps"]["email_sent"] = {
                "status": "error",
                "error": str(e),
                "latency_seconds": round(step_latency, 2)
            }
            print(f"  ❌ Email send failed: {e}")

    # ── Step 5: Book Discovery Call ──
    # Only books if segment confidence is high enough.
    # A completed booking triggers a second HubSpot write
    # referencing the same prospect (same contact_id).
    should_book = (
        brief["segment_confidence"] >= 0.75 and
        brief["primary_segment_match"] != "abstain"
    )

    if should_book:
        print("\n[Step 5] Booking discovery call...")
        step_start = time.time()

        with langfuse.start_as_current_observation(
            name=f"booking-{company_name}",
            input={
                "prospect_email": prospect_email,
                "company": company_name,
                "segment": brief["primary_segment_match"],
                "channel": "voice_final"
            }
        ):
            try:
                booking = book_discovery_call(
                    prospect_email=prospect_email,
                    prospect_name=prospect_name,
                    brief=brief
                )
                step_latency = time.time() - step_start

                # ── Booking triggers second HubSpot write ──
                # Links booking back to same contact
                # created in Step 3
                hubspot_booking_updated = False
                if (
                    booking["status"] in [
                        "success", "mock_success"
                    ]
                    and contact_id
                ):
                    try:
                        hs_client = get_client()
                        booking_note = (
                            f"=== Discovery Call Booked ===\n"
                            f"Booking ID: "
                            f"{booking.get('booking_id')}\n"
                            f"Booking UID: "
                            f"{booking.get('booking_uid')}\n"
                            f"Start Time: "
                            f"{booking.get('start_time')}\n"
                            f"Prospect: {prospect_name}\n"
                            f"Company: {company_name}\n"
                            f"Segment: "
                            f"{brief['primary_segment_match']}\n"
                            f"AI Maturity: "
                            f"{brief['ai_maturity']['score']}/3\n"
                            f"Booked at: "
                            f"{datetime.now().isoformat()}\n\n"
                            f"Context brief attached to "
                            f"Cal.com booking for delivery lead."
                        )
                        _add_note(
                            hs_client,
                            contact_id,
                            booking_note
                        )
                        hubspot_booking_updated = True
                        print(
                            f"  ✅ HubSpot updated with "
                            f"booking ref (contact: {contact_id})"
                        )
                    except Exception as he:
                        print(
                            f"  ⚠️  HubSpot booking "
                            f"write failed: {he}"
                        )

                trace["steps"]["booking"] = {
                    "status": booking["status"],
                    "booking_id": booking.get("booking_id"),
                    "booking_uid": booking.get("booking_uid"),
                    "start_time": booking.get("start_time"),
                    "channel": "voice_final",
                    "channel_note": (
                        "Discovery call is final channel — "
                        "booked by agent, "
                        "delivered by human delivery lead."
                    ),
                    "hubspot_booking_written": (
                        hubspot_booking_updated
                    ),
                    "hubspot_contact_id": contact_id,
                    "latency_seconds": round(step_latency, 2),
                    "completed_at": datetime.now().isoformat()
                }
                trace["latency"]["booking"] = round(
                    step_latency, 2
                )
                langfuse.update_current_span(
                    output={
                        "booking_id": booking.get("booking_id"),
                        "status": booking["status"],
                        "start_time": booking.get("start_time"),
                        "hubspot_updated": hubspot_booking_updated
                    }
                )
                print(
                    f"  ✅ Booking ID: {booking.get('booking_id')}"
                )
                print(f"  ✅ Latency: {step_latency:.2f}s")
            except Exception as e:
                step_latency = time.time() - step_start
                trace["steps"]["booking"] = {
                    "status": "error",
                    "error": str(e),
                    "latency_seconds": round(step_latency, 2)
                }
                print(f"  ⚠️  Booking failed (non-critical): {e}")
    else:
        print(
            f"\n[Step 5] Skipping booking "
            f"(confidence: {brief['segment_confidence']:.0%})"
        )
        trace["steps"]["booking"] = {
            "status": "skipped",
            "reason": (
                f"Segment confidence "
                f"{brief['segment_confidence']:.0%} "
                f"below 75% threshold"
            )
        }

    # ── Complete ──
    total_latency = time.time() - flow_start
    trace["status"] = "completed"
    trace["completed_at"] = datetime.now().isoformat()
    trace["latency"]["total"] = round(total_latency, 2)
    trace["langfuse_trace_id"] = lf_trace_id

    # Flush Langfuse
    langfuse.flush()

    # Save trace
    os.makedirs("outputs/traces", exist_ok=True)
    trace_file = (
        f"outputs/traces/trace_"
        f"{company_name.lower().replace(' ', '_')}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(trace_file, "w") as f:
        json.dump(trace, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Flow completed for: {company_name}")
    print(f"Total latency: {total_latency:.2f}s")
    print(f"Trace saved: {trace_file}")
    print(f"Langfuse trace ID: {lf_trace_id}")
    print(f"{'='*50}")

    return trace