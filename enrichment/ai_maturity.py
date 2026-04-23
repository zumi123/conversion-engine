from typing import List, Dict


def score_ai_maturity(signals: Dict) -> Dict:
    """
    Score AI maturity 0-3 based on public signals.
    
    Signals dict expects:
    - ai_open_roles: int (count of AI/ML open roles)
    - total_open_roles: int
    - has_ai_leadership: bool
    - github_ai_activity: bool
    - executive_ai_commentary: bool
    - modern_ml_stack: bool (dbt, Snowflake, Databricks etc)
    - strategic_ai_comms: bool
    """
    score = 0
    justifications = []
    
    # HIGH WEIGHT signals (can contribute 1 point each)
    
    # AI-adjacent open roles
    ai_roles = signals.get("ai_open_roles", 0)
    total_roles = signals.get("total_open_roles", 0)
    ai_role_ratio = ai_roles / total_roles if total_roles > 0 else 0
    
    if ai_roles >= 3 or ai_role_ratio >= 0.25:
        score += 1
        justifications.append({
            "signal": "ai_adjacent_open_roles",
            "status": f"Found {ai_roles} AI/ML open roles "
                     f"({ai_role_ratio:.0%} of total openings)",
            "weight": "high",
            "confidence": "high" if ai_roles >= 3 else "medium"
        })
    elif ai_roles > 0:
        justifications.append({
            "signal": "ai_adjacent_open_roles",
            "status": f"Found {ai_roles} AI/ML role — "
                     f"weak signal",
            "weight": "high",
            "confidence": "low"
        })
    else:
        justifications.append({
            "signal": "ai_adjacent_open_roles",
            "status": "No AI/ML open roles detected",
            "weight": "high",
            "confidence": "high"
        })
    
    # Named AI/ML leadership
    if signals.get("has_ai_leadership"):
        score += 1
        justifications.append({
            "signal": "named_ai_ml_leadership",
            "status": "AI/ML leadership role detected "
                     "(Head of AI, VP Data, or equivalent)",
            "weight": "high",
            "confidence": "high"
        })
    else:
        justifications.append({
            "signal": "named_ai_ml_leadership",
            "status": "No named AI/ML leadership found publicly",
            "weight": "high",
            "confidence": "medium"
        })
    
    # MEDIUM WEIGHT signals (contribute 0.5 points, 
    # rounded at end)
    medium_score = 0
    
    # GitHub activity
    if signals.get("github_ai_activity"):
        medium_score += 0.5
        justifications.append({
            "signal": "github_org_activity",
            "status": "Recent AI/ML commits detected "
                     "in public GitHub org",
            "weight": "medium",
            "confidence": "medium"
        })
    else:
        justifications.append({
            "signal": "github_org_activity",
            "status": "No public GitHub AI activity — "
                     "may be private",
            "weight": "medium",
            "confidence": "low"
        })
    
    # Executive commentary
    if signals.get("executive_ai_commentary"):
        medium_score += 0.5
        justifications.append({
            "signal": "executive_commentary",
            "status": "CEO/CTO has publicly named AI "
                     "as strategic priority in last 12 months",
            "weight": "medium",
            "confidence": "high"
        })
    else:
        justifications.append({
            "signal": "executive_commentary",
            "status": "No recent executive AI commentary found",
            "weight": "medium",
            "confidence": "medium"
        })
    
    # LOW WEIGHT signals (contribute 0.25 points each)
    low_score = 0
    
    # Modern ML stack
    if signals.get("modern_ml_stack"):
        low_score += 0.25
        justifications.append({
            "signal": "modern_data_ml_stack",
            "status": "Modern ML/data stack detected "
                     "(dbt, Snowflake, Databricks, etc.)",
            "weight": "low",
            "confidence": "medium"
        })
    
    # Strategic communications
    if signals.get("strategic_ai_comms"):
        low_score += 0.25
        justifications.append({
            "signal": "strategic_communications",
            "status": "AI positioned as company priority "
                     "in investor/press communications",
            "weight": "low",
            "confidence": "medium"
        })
    
    # Add medium and low scores and round
    total_score = score + medium_score + low_score
    final_score = min(3, round(total_score))
    
    # Calculate overall confidence
    high_signals = sum(
        1 for j in justifications 
        if j["confidence"] == "high"
    )
    total_signals = len(justifications)
    confidence = round(high_signals / total_signals, 2)
    
    return {
        "score": final_score,
        "confidence": confidence,
        "justifications": justifications
    }