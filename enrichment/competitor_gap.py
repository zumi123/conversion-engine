import json
import os
from datetime import datetime


def generate_competitor_gap_brief(
    brief: dict,
    sector: str = "AI/ML SaaS"
) -> dict:
    """
    Generate competitor gap brief for a prospect.
    Compares prospect AI maturity against sector top quartile.
    """
    prospect_score = brief["ai_maturity"]["score"]
    company = brief["prospect_name"]
    segment = brief["primary_segment_match"]

    # Top quartile benchmark (sector average top 25%)
    # Based on public signal from Crunchbase ODM sample
    sector_benchmarks = {
        "AI/ML SaaS": {
            "top_quartile_score": 3,
            "median_score": 2,
            "sample_companies": [
                "Hugging Face",
                "Scale AI",
                "Cohere"
            ]
        },
        "Data Platform": {
            "top_quartile_score": 3,
            "median_score": 2,
            "sample_companies": [
                "Databricks",
                "dbt Labs",
                "Fivetran"
            ]
        },
        "General SaaS": {
            "top_quartile_score": 2,
            "median_score": 1,
            "sample_companies": [
                "Salesforce",
                "HubSpot",
                "Zendesk"
            ]
        }
    }

    benchmark = sector_benchmarks.get(
        sector,
        sector_benchmarks["General SaaS"]
    )
    top_quartile_score = benchmark["top_quartile_score"]
    gap = top_quartile_score - prospect_score

    # Identify practices top quartile has
    # that prospect doesn't
    practices_not_observed = []

    if prospect_score < 3:
        if not any(
            j["signal"] == "named_ai_ml_leadership" and
            j["confidence"] == "high"
            for j in brief["ai_maturity"]["justifications"]
        ):
            practices_not_observed.append({
                "practice": "Dedicated AI/ML Leadership",
                "public_signal": (
                    f"Top quartile companies in {sector} "
                    f"have named Head of AI or VP Data — "
                    f"no equivalent found for {company}"
                )
            })

    if prospect_score < 2:
        practices_not_observed.append({
            "practice": "MLOps Infrastructure",
            "public_signal": (
                f"Competitors in {sector} show public "
                f"signal of MLOps tooling (MLflow, W&B) — "
                f"not detected for {company}"
            )
        })

    if prospect_score < 1:
        practices_not_observed.append({
            "practice": "AI-Adjacent Engineering Roles",
            "public_signal": (
                f"Top quartile companies post ML Engineer "
                f"and Data Platform Engineer roles — "
                f"none found for {company}"
            )
        })

    # Suggested pitch shift
    if gap == 0:
        pitch_shift = (
            "Prospect is at top-quartile level. "
            "Focus on scaling what they already have."
        )
    elif gap == 1:
        pitch_shift = (
            f"Shift pitch to: 'Scale your existing "
            f"AI function faster than in-house hiring "
            f"can support'"
        )
    else:
        pitch_shift = (
            f"Shift pitch to: 'Stand up your first "
            f"dedicated AI function with a squad that "
            f"deploys in 10 days'"
        )

    gap_brief = {
        "prospect_name": company,
        "prospect_sector": sector,
        "prospect_ai_maturity": prospect_score,
        "top_quartile_benchmark": top_quartile_score,
        "sector_median": benchmark["median_score"],
        "gap_score": gap,
        "computed_gap_finding": (
            f"{company} AI maturity score is {prospect_score}/3 "
            f"vs sector top-quartile benchmark of "
            f"{top_quartile_score}/3 — "
            f"a gap of {gap} point(s)"
        ) if gap > 0 else (
            f"{company} is at or above the sector "
            f"top-quartile benchmark"
        ),
        "top_quartile_practices_not_observed": (
            practices_not_observed
        ),
        "suggested_pitch_shift": pitch_shift,
        "generated_at": datetime.now().isoformat(),
        "honesty_note": (
            "Gap analysis based on public signal only. "
            "Absence of signal does not confirm absence "
            "of capability — prospect may have private "
            "AI work not publicly visible."
        )
    }

    # Save to outputs
    os.makedirs("outputs", exist_ok=True)
    company_slug = company.lower().replace(" ", "_")
    output_path = (
        f"outputs/competitor_gap_brief_{company_slug}.json"
    )
    with open(output_path, "w") as f:
        json.dump(gap_brief, f, indent=2)

    print(f"  Gap brief saved: {output_path}")
    return gap_brief