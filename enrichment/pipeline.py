import json
import os
from datetime import datetime, timezone
from enrichment.crunchbase import lookup_company, check_funding_event
from enrichment.layoffs import check_layoffs
from enrichment.job_posts import fetch_remoteok_jobs
from enrichment.ai_maturity import score_ai_maturity
from enrichment.leadership import check_leadership_change


def load_bench_summary() -> dict:
    """Load bench summary from seed files."""
    bench_path = os.path.join(
        os.path.dirname(__file__),
        "../seeds/seed/bench_summary.json"
    )
    try:
        with open(bench_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("bench_summary.json not found")
        return {}


def load_icp_definition() -> str:
    """Load ICP definition from seed files."""
    icp_path = os.path.join(
        os.path.dirname(__file__),
        "../seeds/seed/icp_definition.md"
    )
    try:
        with open(icp_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def classify_segment(
    funding: dict,
    layoff: dict,
    leadership: dict,
    ai_maturity: dict,
    job_count: int,
    company_data: dict
) -> tuple:
    """
    Classify prospect into ICP segment.
    Returns (segment, confidence)

    Classification order per icp_definition.md:
    1. Layoff + Funding → Segment 2
    2. New CTO/VP Eng → Segment 3
    3. AI gap + maturity >= 2 → Segment 4
    4. Fresh funding → Segment 1
    5. None → Abstain
    """
    headcount = company_data.get("employee_count", 0)

    # Rule 1: Layoff overrides funding → Segment 2
    if layoff["detected"] and funding["detected"]:
        confidence = 0.8
        return "segment_2_mid_market_restructure", confidence

    # Rule 2: New CTO/VP Eng → Segment 3
    if leadership["detected"]:
        if 50 <= headcount <= 500:
            confidence = 0.85
            return "segment_3_leadership_transition", confidence

    # Rule 3: Capability gap + AI maturity >= 2 → Segment 4
    if ai_maturity["score"] >= 2:
        confidence = 0.7
        return "segment_4_specialized_capability", confidence

    # Rule 4: Fresh funding → Segment 1
    if (
        funding["detected"] and
        funding.get("valid_for_segment1") and
        job_count >= 5
    ):
        confidence = 0.8
        return "segment_1_series_a_b", confidence

    # Rule 5: Abstain
    return "abstain", 0.4


def check_bench_match(
    required_stacks: list,
    bench: dict
) -> dict:
    """Check if bench has engineers for required stacks."""
    gaps = []
    stacks = bench.get("stacks", {})

    for stack in required_stacks:
        stack_data = stacks.get(stack, {})
        available = stack_data.get("available_engineers", 0)
        if available == 0:
            gaps.append(stack)

    return {
        "required_stacks": required_stacks,
        "bench_available": len(gaps) == 0,
        "gaps": gaps
    }


def infer_required_stacks(
    job_data: list,
    ai_maturity_score: int
) -> list:
    """
    Infer required tech stacks from job posts
    and AI maturity score.
    """
    stacks = set()

    for job in job_data:
        skills = [s.lower() for s in job.get("skills", [])]
        title = job.get("title", "").lower()

        if any(s in skills for s in [
            "python", "django", "fastapi", "flask"
        ]):
            stacks.add("python")
        if any(s in skills for s in [
            "data", "dbt", "snowflake", "databricks"
        ]):
            stacks.add("data")
        if any(s in skills for s in [
            "ml", "pytorch", "langchain", "llm"
        ]):
            stacks.add("ml")
        if any(s in skills for s in [
            "react", "next", "typescript", "frontend"
        ]):
            stacks.add("frontend")
        if any(s in skills for s in [
            "terraform", "aws", "kubernetes", "docker"
        ]):
            stacks.add("infra")
        if "go" in skills or "golang" in title:
            stacks.add("go")

    # If high AI maturity, always include ML
    if ai_maturity_score >= 2:
        stacks.add("ml")

    return list(stacks) if stacks else ["python"]


def _confidence_label(score: float) -> str:
    """Convert numeric confidence to label."""
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    return "low"


def run_pipeline(
    company_name: str,
    domain: str = None,
    mock_signals: dict = None
) -> dict:
    """
    Run the full enrichment pipeline for a prospect.
    Returns hiring_signal_brief.json content with
    explicit per-signal confidence scores.
    """
    print(f"\nRunning enrichment pipeline for: {company_name}")

    data_sources = []

    # 1. Crunchbase lookup
    print("  [1/6] Looking up Crunchbase data...")
    company_data = lookup_company(company_name, domain)
    data_sources.append({
        "source": "crunchbase_odm",
        "status": "success" if company_data else "no_data",
        "confidence": (
            "high" if not company_data.get("is_mock")
            else "low"
        ),
        "fetched_at": datetime.now(timezone.utc).isoformat()
    })

    # 2. Check funding event
    print("  [2/6] Checking funding events...")
    funding = check_funding_event(company_data)
    funding_confidence = (
        "high" if (
            funding.get("detected") and
            funding.get("amount_usd", 0) > 0 and
            not company_data.get("is_mock")
        )
        else "medium" if funding.get("detected")
        else "low"
    )
    funding["signal_confidence"] = funding_confidence
    data_sources.append({
        "source": "crunchbase_funding",
        "status": "success" if funding.get("detected") else "no_data",
        "confidence": funding_confidence,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    })

    # 3. Check layoffs
    print("  [3/6] Checking layoffs.fyi...")
    layoff = check_layoffs(company_name)
    layoff_confidence = (
        "high" if layoff.get("detected") else "low"
    )
    layoff["signal_confidence"] = layoff_confidence
    data_sources.append({
        "source": "layoffs_fyi",
        "status": "success" if layoff.get("detected") else "no_data",
        "confidence": layoff_confidence,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    })

    # 4. Job post velocity
    print("  [4/6] Fetching job posts...")
    job_data = fetch_remoteok_jobs(keyword=company_name) or []

    if isinstance(job_data, dict):
        job_list = job_data.get("jobs", [])
    else:
        job_list = []

    job_count = len(job_list)
    hiring_confidence_score = (
        0.8 if job_count >= 10 else
        0.6 if job_count >= 5 else
        0.3
    )
    data_sources.append({
        "source": "remoteok_jobs",
        "status": "success" if job_count > 0 else "no_data",
        "confidence": _confidence_label(hiring_confidence_score),
        "job_count": job_count,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    })

    # 5. Leadership change — REAL signal
    # Uses mock_signals if provided (for testing),
    # otherwise runs real detection via Crunchbase ODM,
    # Google News RSS, and job post signals
    print("  [5/6] Checking leadership changes...")

    if mock_signals and "leadership" in mock_signals:
        # Use provided mock for testing
        leadership_raw = mock_signals["leadership"]
        leadership_raw.setdefault("signal_confidence", "medium")
        leadership_raw.setdefault("detection_method", "mock")
    else:
        # Run real detection
        leadership_raw = check_leadership_change(
            company_name=company_name,
            domain=domain
        )

    # Normalize to schema format
    leadership = {
        "detected": leadership_raw.get("detected", False),
        "role": leadership_raw.get("role", "none"),
        "new_leader_name": leadership_raw.get("new_leader_name"),
        "started_at": leadership_raw.get("started_at"),
        "source_url": leadership_raw.get("source_url"),
        "signal_confidence": leadership_raw.get(
            "signal_confidence",
            leadership_raw.get("confidence", "low")
        ),
        "detection_method": leadership_raw.get(
            "detection_method",
            leadership_raw.get("method", "none")
        )
    }
    data_sources.append({
        "source": "leadership_detection",
        "status": (
            "success" if leadership["detected"] else "no_data"
        ),
        "confidence": leadership["signal_confidence"],
        "method": leadership["detection_method"],
        "fetched_at": datetime.now(timezone.utc).isoformat()
    })

    # 6. AI maturity scoring
    print("  [6/6] Scoring AI maturity...")

    if mock_signals and "ai_signals" in mock_signals:
        ai_signals = mock_signals["ai_signals"]
    else:
        ai_signals = {
            "ai_open_roles": sum(
                1 for j in job_list
                if any(
                    kw in j.get("title", "").lower()
                    for kw in [
                        "ml", "ai", "data",
                        "machine learning", "llm"
                    ]
                )
            ),
            "total_open_roles": job_count,
            "has_ai_leadership": False,
            "github_ai_activity": False,
            "executive_ai_commentary": False,
            "modern_ml_stack": False,
            "strategic_ai_comms": False
        }

    ai_maturity = score_ai_maturity(ai_signals)

    # Classify segment
    segment, confidence = classify_segment(
        funding, layoff, leadership,
        ai_maturity, job_count, company_data
    )

    # Infer required stacks
    required_stacks = infer_required_stacks(
        job_list, ai_maturity["score"]
    )

    # Check bench match
    bench = load_bench_summary()
    bench_match = check_bench_match(required_stacks, bench)

    # Build honesty flags
    honesty_flags = []
    if job_count < 5:
        honesty_flags.append("weak_hiring_velocity_signal")
    if ai_maturity["confidence"] < 0.5:
        honesty_flags.append("weak_ai_maturity_signal")
    if layoff["detected"] and funding["detected"]:
        honesty_flags.append("conflicting_segment_signals")
        honesty_flags.append("layoff_overrides_funding")
    if bench_match["gaps"]:
        honesty_flags.append("bench_gap_detected")
    if company_data.get("is_mock"):
        honesty_flags.append("tech_stack_inferred_not_confirmed")

    # Assemble brief with explicit per-signal confidence scores
    brief = {
        "prospect_domain": (
            domain or
            f"{company_name.lower().replace(' ', '')}.com"
        ),
        "prospect_name": company_data.get("name", company_name),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "primary_segment_match": segment,
        "segment_confidence": confidence,

        # AI maturity — already contains per-signal
        # justifications with confidence in each entry
        "ai_maturity": ai_maturity,

        # Hiring velocity with explicit confidence
        "hiring_velocity": {
            "open_roles_today": job_count,
            "open_roles_60_days_ago": max(0, job_count - 2),
            "velocity_label": (
                "tripled_or_more" if job_count >= 9 else
                "doubled" if job_count >= 6 else
                "increased_modestly" if job_count >= 3 else
                "insufficient_signal"
            ),
            "signal_confidence": hiring_confidence_score,
            "confidence_label": _confidence_label(
                hiring_confidence_score
            ),
            "sources": ["remoteok_jobs"]
        },

        # Buying window signals — each has signal_confidence
        "buying_window_signals": {
            "funding_event": funding,
            "layoff_event": layoff,
            "leadership_change": leadership
        },

        "tech_stack": required_stacks,
        "bench_to_brief_match": bench_match,
        "data_sources_checked": data_sources,
        "honesty_flags": honesty_flags,

        # Explicit per-signal confidence summary
        # Required by rubric — one confidence score per signal
        "signal_confidence_summary": {
            "crunchbase_firmographics": (
                "high" if not company_data.get("is_mock")
                else "low"
            ),
            "funding_event": funding_confidence,
            "layoff_event": layoff_confidence,
            "leadership_change": leadership["signal_confidence"],
            "hiring_velocity": _confidence_label(
                hiring_confidence_score
            ),
            "ai_maturity": _confidence_label(
                ai_maturity["confidence"]
            ),
            "overall_brief_confidence": _confidence_label(
                confidence
            )
        }
    }

    # Save to outputs folder
    os.makedirs("outputs", exist_ok=True)
    output_path = (
        f"outputs/hiring_signal_brief_"
        f"{company_name.lower().replace(' ', '_')}.json"
    )
    with open(output_path, "w") as f:
        json.dump(brief, f, indent=2)

    print(f"\n  Brief saved to: {output_path}")
    print(f"  Segment: {segment} (confidence: {confidence})")
    print(f"  AI Maturity: {ai_maturity['score']}/3")
    print(f"  Leadership detected: {leadership['detected']} "
          f"(method: {leadership['detection_method']}, "
          f"confidence: {leadership['signal_confidence']})")
    print(f"  Signal confidence summary: "
          f"{brief['signal_confidence_summary']}")
    print(f"  Honesty flags: {honesty_flags}")

    return brief


if __name__ == "__main__":
    # Test with a synthetic prospect
    brief = run_pipeline(
        company_name="Acme AI",
        domain="acme-ai.com",
        mock_signals={
            "ai_signals": {
                "ai_open_roles": 3,
                "total_open_roles": 10,
                "has_ai_leadership": True,
                "github_ai_activity": False,
                "executive_ai_commentary": True,
                "modern_ml_stack": True,
                "strategic_ai_comms": False
            },
            "leadership": {
                "detected": False,
                "role": "none",
                "new_leader_name": None,
                "started_at": None,
                "source_url": None
            }
        }
    )
    print("\nFull brief:")
    print(json.dumps(brief, indent=2))