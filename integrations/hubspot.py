import os
import json
from datetime import datetime
from dotenv import load_dotenv
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate
from hubspot.crm.contacts.exceptions import ApiException

load_dotenv()


def get_client():
    """Get HubSpot client."""
    return HubSpot(
        access_token=os.environ["HUBSPOT_API_KEY"]
    )


def create_or_update_prospect(
    brief: dict,
    email: str,
    contact_name: str = None,
    email_draft: dict = None
) -> dict:
    """
    Create or update a prospect contact in HubSpot
    with enrichment data from the hiring signal brief.
    """
    client = get_client()
    company = brief["prospect_name"]
    segment = brief["primary_segment_match"]
    ai_score = brief["ai_maturity"]["score"]
    confidence = brief["segment_confidence"]
    funding = brief["buying_window_signals"]["funding_event"]
    honesty_flags = brief.get("honesty_flags", [])

    # Build contact properties
    properties = {
        "email": email,
        "company": company,
        "website": brief.get("prospect_domain", ""),

        # ICP Classification
        "hs_lead_status": "NEW",
        "lifecyclestage": "lead",

    }

    # Add name if provided
    if contact_name:
        parts = contact_name.split(" ", 1)
        properties["firstname"] = parts[0]
        if len(parts) > 1:
            properties["lastname"] = parts[1]

    # Build enrichment note
    funding_str = "None detected"
    if funding.get("detected"):
        amount = funding.get("amount_usd", 0)
        stage = funding.get("stage", "").replace("_", " ").title()
        days = funding.get("days_ago", 0)
        funding_str = f"{stage} ${amount/1_000_000:.1f}M ({days} days ago)"

    note_content = f"""=== Tenacious Enrichment Brief ===
Generated: {brief['generated_at']}

SEGMENT: {segment.replace('_', ' ').upper()}
Confidence: {confidence:.0%}

AI MATURITY: {ai_score}/3
Honesty Flags: {', '.join(honesty_flags) or 'None'}

FUNDING: {funding_str}

HIRING VELOCITY: {brief['hiring_velocity']['velocity_label']}
Open Roles Today: {brief['hiring_velocity']['open_roles_today']}

BENCH MATCH: {'✓ Available' if brief['bench_to_brief_match']['bench_available'] else '✗ Gap detected'}
Required Stacks: {', '.join(brief['bench_to_brief_match']['required_stacks'])}

EMAIL SENT:
Subject: {email_draft['subject'] if email_draft else 'N/A'}
Tone Score: {email_draft.get('tone_score', 'N/A') if email_draft else 'N/A'}
"""

    try:
        # Try to find existing contact
        existing = _find_contact_by_email(client, email)

        if existing:
            # Update existing contact
            contact_id = existing.id
            client.crm.contacts.basic_api.update(
                contact_id=contact_id,
                simple_public_object_input=
                    SimplePublicObjectInputForCreate(
                        properties=properties
                    )
            )
            print(f"  Updated existing contact: {contact_id}")
        else:
            # Create new contact
            response = client.crm.contacts.basic_api.create(
                simple_public_object_input_for_create=
                    SimplePublicObjectInputForCreate(
                        properties=properties
                    )
            )
            contact_id = response.id
            print(f"  Created new contact: {contact_id}")

        # Add enrichment note
        _add_note(client, contact_id, note_content)

        return {
            "status": "success",
            "contact_id": contact_id,
            "company": company,
            "segment": segment,
            "enrichment_timestamp": datetime.now().isoformat()
        }

    except ApiException as e:
        print(f"  HubSpot API error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def _find_contact_by_email(
    client: HubSpot,
    email: str
) -> object:
    """Find existing contact by email."""
    try:
        from hubspot.crm.contacts import PublicObjectSearchRequest
        search = PublicObjectSearchRequest(
            filter_groups=[{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }]
        )
        results = client.crm.contacts.search_api.do_search(
            public_object_search_request=search
        )
        if results.total > 0:
            return results.results[0]
        return None
    except Exception:
        return None


def _add_note(
    client: HubSpot,
    contact_id: str,
    note_content: str
) -> None:
    """Add a note to a HubSpot contact."""
    try:
        from hubspot.crm.objects.notes import (
            SimplePublicObjectInputForCreate as NoteInput
        )
        from hubspot.crm.associations.v4 import (
            BatchInputPublicDefaultAssociationMultiPost,
            PublicDefaultAssociationMultiPost
        )

        # Create the note
        note = NoteInput(
            properties={
                "hs_note_body": note_content,
                "hs_timestamp": str(
                    int(datetime.now().timestamp() * 1000)
                )
            }
        )
        note_response = (
            client.crm.objects.notes.basic_api.create(
                simple_public_object_input_for_create=note
            )
        )

        # Associate note with contact using v4 API
        client.crm.associations.v4.basic_api.create(
            object_type="notes",
            object_id=note_response.id,
            to_object_type="contacts",
            to_object_id=contact_id,
            association_spec=[{
                "associationCategory": "HUBSPOT_DEFINED",
                "associationTypeId": 202
            }]
        )
        print(f"  Note added to contact {contact_id}")
    except Exception as e:
        print(f"  Note creation failed (non-critical): {e}")

def log_email_sent(
    contact_id: str,
    subject: str,
    body: str
) -> None:
    """Log outbound email activity in HubSpot."""
    try:
        client = get_client()
        from hubspot.crm.objects.emails import (
            SimplePublicObjectInputForCreate as EmailInput
        )
        email_obj = EmailInput(
            properties={
                "hs_email_subject": subject,
                "hs_email_text": body,
                "hs_email_direction": "EMAIL",
                "hs_timestamp": str(
                    int(datetime.now().timestamp() * 1000)
                )
            }
        )
        email_response = (
            client.crm.objects.emails.basic_api.create(
                simple_public_object_input_for_create=email_obj
            )
        )
        print(f"  Email logged: {email_response.id}")
    except Exception as e:
        print(f"  Email logging failed (non-critical): {e}")