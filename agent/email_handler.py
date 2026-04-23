import resend
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.environ["RESEND_API_KEY"]


def load_style_guide() -> str:
    """Load Tenacious style guide."""
    path = "seeds/seed/style_guide.md"
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def load_bench_summary() -> dict:
    """Load bench summary."""
    path = "seeds/seed/bench_summary.json"
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def compose_email(brief: dict) -> dict:
    """
    Compose a personalized outreach email based on
    the hiring signal brief.
    Uses rules-based composition — no LLM needed.
    """
    company = brief["prospect_name"]
    segment = brief["primary_segment_match"]
    confidence = brief["segment_confidence"]
    ai_score = brief["ai_maturity"]["score"]
    honesty_flags = brief.get("honesty_flags", [])
    funding = brief["buying_window_signals"]["funding_event"]
    layoff = brief["buying_window_signals"]["layoff_event"]
    leadership = brief["buying_window_signals"]["leadership_change"]
    hiring = brief["hiring_velocity"]
    bench_match = brief["bench_to_brief_match"]

    # If low confidence — send generic exploratory email
    if confidence < 0.6 or segment == "abstain":
        return _compose_generic_email(company, brief)

    # Route to segment-specific composer
    if segment == "segment_1_series_a_b":
        return _compose_segment1_email(
            company, brief, funding, 
            ai_score, hiring, honesty_flags
        )
    elif segment == "segment_2_mid_market_restructure":
        return _compose_segment2_email(
            company, brief, layoff,
            ai_score, honesty_flags
        )
    elif segment == "segment_3_leadership_transition":
        return _compose_segment3_email(
            company, brief, leadership, honesty_flags
        )
    elif segment == "segment_4_specialized_capability":
        return _compose_segment4_email(
            company, brief, ai_score,
            bench_match, honesty_flags
        )
    else:
        return _compose_generic_email(company, brief)


def _compose_segment1_email(
    company, brief, funding, 
    ai_score, hiring, honesty_flags
) -> dict:
    """Segment 1: Recently-funded Series A/B startup."""
    
    amount = funding.get("amount_usd", 0)
    amount_str = f"${amount/1_000_000:.0f}M" if amount else "recent"
    stage = funding.get("stage", "").replace("_", " ").title()
    days_ago = funding.get("days_ago", 0)
    
    # Hiring velocity — only assert if signal is strong
    if "weak_hiring_velocity_signal" in honesty_flags:
        hiring_line = (
            "Is recruiting velocity keeping up with "
            "the growth you're planning post-raise?"
        )
    else:
        open_roles = hiring.get("open_roles_today", 0)
        hiring_line = (
            f"Your {open_roles} open engineering roles "
            f"suggest hiring is moving fast — "
            f"is recruiting velocity matching the runway?"
        )

    # AI pitch language based on maturity score
    if ai_score >= 2:
        value_prop = (
            "scale your AI engineering team faster "
            "than in-house hiring can support"
        )
    else:
        value_prop = (
            "stand up your first AI function "
            "with a dedicated squad"
        )

    subject = f"Request: Engineering capacity post-{stage}"
    if len(subject) > 60:
        subject = f"Request: Engineering capacity post-raise"

    body = f"""Congratulations on the {amount_str} {stage} — {days_ago} days in is typically when hiring velocity starts to strain recruiting capacity.

{hiring_line}

Tenacious provides dedicated engineering teams that deploy in 7 days. We work with {stage} companies specifically to {value_prop}.

Worth a 15-minute conversation?

"""

    return {
        "subject": subject,
        "body": body,
        "segment": "segment_1_series_a_b",
        "ai_maturity_score": ai_score,
        "word_count": len(body.split())
    }


def _compose_segment2_email(
    company, brief, layoff,
    ai_score, honesty_flags
) -> dict:
    """Segment 2: Mid-market restructuring."""

    pct = layoff.get("percentage_cut", 0)
    date = layoff.get("date", "recently")

    if ai_score >= 2:
        value_prop = (
            "preserve your AI delivery capacity "
            "while reshaping cost structure"
        )
    else:
        value_prop = (
            "maintain platform delivery velocity "
            "through the restructure"
        )

    subject = "Context: Engineering capacity during restructure"

    body = f"""Following the recent restructure, many engineering teams face the same challenge: maintain delivery velocity while reducing fixed headcount cost.

Tenacious provides offshore engineering teams at 20% below comparable India rates, with guaranteed 3-hour synchronous overlap and a 1-month minimum commitment.

The goal: {value_prop} — without a long-term headcount commitment.

Open to a 15-minute conversation?

"""

    return {
        "subject": subject,
        "body": body,
        "segment": "segment_2_mid_market_restructure",
        "ai_maturity_score": ai_score,
        "word_count": len(body.split())
    }


def _compose_segment3_email(
    company, brief, leadership, honesty_flags
) -> dict:
    """Segment 3: New CTO/VP Engineering."""

    role = leadership.get("role", "CTO").replace("_", " ").upper()
    name = leadership.get("new_leader_name", "")
    days = leadership.get("days_ago", 60)

    greeting = f"Congratulations on the {role} appointment"
    if name:
        greeting = f"Congratulations {name} on the {role} role"

    subject = f"Request: 15 minutes on engineering vendor mix"

    body = f"""{greeting} — the first 90 days are typically when vendor contracts and offshore mix get reassessed.

Tenacious works with engineering leaders at this stage to provide dedicated offshore squads that deploy in 7 days with no long-term commitment required.

Not pitching a specific engagement — just offering 15 minutes if the timing is right.

"""

    return {
        "subject": subject,
        "body": body,
        "segment": "segment_3_leadership_transition",
        "ai_maturity_score": brief["ai_maturity"]["score"],
        "word_count": len(body.split())
    }


def _compose_segment4_email(
    company, brief, ai_score,
    bench_match, honesty_flags
) -> dict:
    """Segment 4: Specialized capability gap."""

    stacks = bench_match.get("required_stacks", ["ML"])
    stack_str = " and ".join(
        [s.upper() for s in stacks[:2]]
    )

    subject = f"Question: {stack_str} capability gap"
    if len(subject) > 60:
        subject = "Question: AI/ML capability gap"

    body = f"""Based on public signal — open roles and recent communications — it looks like {company} is building toward a specific {stack_str} capability.

Three companies in your sector at your stage have stood up dedicated {stack_str} functions in the last 90 days. Curious whether you've made a deliberate choice not to, or whether it's still being scoped.

Tenacious has {stack_str} engineers ready to deploy in 10 days for a fixed-scope engagement or ongoing capacity.

Worth a 15-minute conversation?

"""

    return {
        "subject": subject,
        "body": body,
        "segment": "segment_4_specialized_capability",
        "ai_maturity_score": ai_score,
        "word_count": len(body.split())
    }


def _compose_generic_email(company, brief) -> dict:
    """Generic exploratory email for low-confidence segments."""

    subject = "Question: Engineering capacity at your stage"

    body = f"""Two questions relevant to companies at {company}'s stage:

1. Where is your team currently most constrained — recruiting velocity, specialized skill gaps, or overall cost?
2. What is the single biggest bottleneck in your engineering operations right now?

No prep required — just a quick 15-minute window for a discussion.

"""

    return {
        "subject": subject,
        "body": body,
        "segment": "abstain",
        "ai_maturity_score": brief["ai_maturity"]["score"],
        "word_count": len(body.split())
    }


def add_signature(body: str) -> str:
    """Add Tenacious signature per style guide."""
    signature = """Arun
Research Partner
Tenacious Intelligence Corporation
gettenacious.com"""
    return body + signature


def check_tone(email: dict) -> dict:
    """
    Basic tone check against style guide rules.
    Returns score and any violations.
    """
    body = email["body"].lower()
    violations = []

    # Check word count
    if email["word_count"] > 120:
        violations.append(
            f"Too long: {email['word_count']} words (max 120)"
        )

    # Check for banned phrases
    banned = [
        "hope you're doing well",
        "just wanted to reach out",
        "top talent",
        "world-class",
        "rockstar",
        "ninja",
        "a-players",
        "following up",
        "circling back",
        "quick question"
    ]
    for phrase in banned:
        if phrase in body:
            violations.append(f"Banned phrase: '{phrase}'")

    # Check subject line length
    if len(email["subject"]) > 60:
        violations.append(
            f"Subject too long: {len(email['subject'])} chars"
        )

    # Check subject starts correctly
    valid_starts = [
        "request:", "follow-up:", "context:", 
        "question:", "follow up:"
    ]
    subject_lower = email["subject"].lower()
    if not any(
        subject_lower.startswith(s) for s in valid_starts
    ):
        violations.append(
            "Subject should start with Request/Follow-up/"
            "Context/Question"
        )

    tone_score = max(0, 5 - len(violations))

    return {
        "tone_score": tone_score,
        "violations": violations,
        "passed": len(violations) == 0
    }


def send_email(
    to_email: str,
    email_draft: dict,
    prospect_name: str = None,
    dry_run: bool = True
) -> dict:
    """
    Send outreach email via Resend.
    dry_run=True means compose but don't send.
    """
    body_with_sig = add_signature(email_draft["body"])

    # Tone check before sending
    tone_check = check_tone(email_draft)
    if not tone_check["passed"]:
        print(f"  ⚠️  Tone violations: {tone_check['violations']}")

    if dry_run:
        print("\n  [DRY RUN] Email would be sent:")
        print(f"  To: {to_email}")
        print(f"  Subject: {email_draft['subject']}")
        print(f"  Body:\n{body_with_sig}")
        print(f"  Tone score: {tone_check['tone_score']}/5")
        return {
            "status": "dry_run",
            "to": to_email,
            "subject": email_draft["subject"],
            "tone_check": tone_check
        }

    # Actually send
    try:
        response = resend.Emails.send({
            "from": "outreach@resend.dev",
            "to": [to_email],
            "subject": email_draft["subject"],
            "text": body_with_sig,
            "reply_to": "outreach@resend.dev"
        })
        print(f"  ✅ Email sent: {response}")
        return {
            "status": "sent",
            "email_id": response.get("id"),
            "to": to_email,
            "subject": email_draft["subject"],
            "tone_check": tone_check
        }
    except Exception as e:
        print(f"  ❌ Send failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }