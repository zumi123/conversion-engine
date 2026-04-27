import json
import os
import re
from datetime import datetime, timedelta


def load_crunchbase_data() -> list:
    """Load the Crunchbase ODM sample."""
    data_path = os.path.join(
        os.path.dirname(__file__),
        "../data/crunchbase_sample.json"
    )
    try:
        with open(data_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Crunchbase sample not found")
        return []


def parse_employee_count(num_employees: str) -> int:
    """
    Convert employee range string to integer.
    e.g. '51-100' -> 75, '1-10' -> 5,
    '1001-5000' -> 3000
    """
    if not num_employees:
        return 0
    try:
        if "-" in str(num_employees):
            parts = str(num_employees).split("-")
            return (int(parts[0]) + int(parts[1])) // 2
        return int(num_employees)
    except Exception:
        return 0


def _safe_parse_json(val):
    """
    Safely parse a field that might be:
    - already a list/dict (parsed)
    - a JSON string (needs json.loads)
    - empty/null
    """
    if isinstance(val, (list, dict)):
        return val
    if isinstance(val, str) and val.strip():
        try:
            parsed = json.loads(val)
            if isinstance(parsed, (list, dict)):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
    return [] if not isinstance(val, dict) else {}


def _extract_funding_type(title: str) -> str:
    """
    Extract funding type from round title.
    e.g. 'Series A - Company' -> 'series_a'
    e.g. 'Pre Seed Round - Company' -> 'pre_seed'
    e.g. 'Venture Round - Company' -> 'venture'
    """
    if not title:
        return "other"
    title_lower = title.lower()

    if "series a" in title_lower:
        return "series_a"
    elif "series b" in title_lower:
        return "series_b"
    elif "series c" in title_lower:
        return "series_c"
    elif "series d" in title_lower:
        return "series_d"
    elif "pre-seed" in title_lower or "pre seed" in title_lower:
        return "pre_seed"
    elif "seed" in title_lower:
        return "seed"
    elif "angel" in title_lower:
        return "angel"
    elif "convertible" in title_lower:
        return "convertible_note"
    elif "debt" in title_lower:
        return "debt"
    elif "venture" in title_lower:
        return "venture"
    elif "ipo" in title_lower:
        return "ipo"
    elif "grant" in title_lower:
        return "grant"
    else:
        return "other"


def lookup_company(
    company_name: str,
    domain: str = None
) -> dict:
    """
    Look up a company in the Crunchbase ODM sample.
    Returns normalized company data.
    """
    companies = load_crunchbase_data()

    # Search by name or domain
    for company in companies:
        name = company.get("name", "")
        website = company.get("website", "")
        url = company.get("url", "")

        name_match = (
            company_name.lower() in name.lower() or
            name.lower() in company_name.lower()
        )
        domain_match = (
            domain and (
                domain in (website or "") or
                domain in (url or "")
            )
        )

        if name_match or domain_match:
            print(f"  Found '{name}' in Crunchbase ODM")
            return _normalize_company(company)

    # Not found - use mock
    print(f"  Company '{company_name}' not in ODM sample "
          f"- using mock data")
    return _mock_company(company_name, domain)


def _normalize_company(raw: dict) -> dict:
    """
    Normalize raw Crunchbase ODM row to standard format.
    Handles fields stored as JSON strings.
    """
    # Parse funding rounds list (may be JSON string)
    funding_list = _safe_parse_json(
        raw.get("funding_rounds_list", "[]")
    )

    # Extract latest funding info
    last_funding_at = None
    last_funding_usd = 0
    last_funding_type = "none"

    if isinstance(funding_list, list) and len(funding_list) > 0:
        # Sort by announced_on date to get latest
        valid_rounds = [
            r for r in funding_list
            if isinstance(r, dict) and r.get("announced_on")
        ]
        if valid_rounds:
            valid_rounds.sort(
                key=lambda x: x.get("announced_on", ""),
                reverse=True
            )
            latest = valid_rounds[0]

            last_funding_at = latest.get("announced_on")

            # Extract amount — nested in money_raised dict
            money = latest.get("money_raised", {})
            if isinstance(money, dict):
                last_funding_usd = (
                    money.get("value_usd", 0) or
                    money.get("value", 0) or 0
                )
            else:
                last_funding_usd = 0

            # Extract type from title
            title = latest.get("title", "")
            last_funding_type = _extract_funding_type(title)

    # Parse leadership hires (may be JSON string)
    leadership_hire = _safe_parse_json(
        raw.get("leadership_hire", "[]")
    )

    # Parse layoffs (may be JSON string)
    layoff = _safe_parse_json(
        raw.get("layoff", "[]")
    )

    # Parse industries (may be JSON string)
    industries = _safe_parse_json(
        raw.get("industries", "[]")
    )
    industry_names = [
        i.get("value", "") for i in industries
        if isinstance(i, dict)
    ]

    # Parse builtwith tech (may be JSON string)
    builtwith = _safe_parse_json(
        raw.get("builtwith_tech", "[]")
    )

    # Parse current employees
    employees = _safe_parse_json(
        raw.get("current_employees", "[]")
    )

    return {
        "crunchbase_id": raw.get("id", ""),
        "name": raw.get("name", ""),
        "homepage_url": raw.get("website", ""),
        "short_description": raw.get("about", ""),
        "employee_count": parse_employee_count(
            raw.get("num_employees", "0")
        ),
        "num_employees_raw": raw.get("num_employees", ""),
        "funding_total_usd": last_funding_usd,
        "last_funding_type": last_funding_type,
        "last_funding_at": last_funding_at,
        "last_funding_usd": last_funding_usd,
        "funding_rounds_count": len(
            [r for r in funding_list if isinstance(r, dict)]
        ) if isinstance(funding_list, list) else 0,
        "country_code": raw.get("country_code", ""),
        "city": (raw.get("address", "") or "").split(",")[0],
        "categories": industry_names,
        "ipo_status": raw.get("ipo_status", "private"),
        "operating_status": raw.get(
            "operating_status", "active"
        ),
        "builtwith_tech": builtwith,
        "leadership_hire": leadership_hire,
        "layoff_data": layoff,
        "current_employees": employees,
        "is_mock": False
    }


def _mock_company(
    company_name: str,
    domain: str = None
) -> dict:
    """
    Returns a synthetic company record for testing.
    """
    return {
        "crunchbase_id": (
            f"mock_{company_name.lower().replace(' ', '_')}"
        ),
        "name": company_name,
        "homepage_url": (
            f"https://{domain or company_name.lower().replace(' ', '') + '.com'}"
        ),
        "short_description": "Technology company",
        "employee_count": 45,
        "num_employees_raw": "11-50",
        "funding_total_usd": 14000000,
        "last_funding_type": "series_a",
        "last_funding_at": (
            datetime.now() - timedelta(days=90)
        ).strftime("%Y-%m-%d"),
        "last_funding_usd": 14000000,
        "funding_rounds_count": 1,
        "country_code": "USA",
        "city": "San Francisco",
        "categories": ["artificial-intelligence", "saas"],
        "builtwith_tech": [],
        "leadership_hire": [],
        "layoff_data": [],
        "current_employees": [],
        "is_mock": True
    }


def check_funding_event(
    company_data: dict,
    days: int = 180
) -> dict:
    """
    Check if company had a funding event
    in the last N days.
    """
    cutoff = datetime.now() - timedelta(days=days)

    last_funding_at = company_data.get("last_funding_at")
    if not last_funding_at:
        return {
            "detected": False,
            "stage": "none",
            "amount_usd": 0,
            "closed_at": None,
            "source_url": company_data.get("homepage_url")
        }

    try:
        funding_date = datetime.strptime(
            last_funding_at[:10], "%Y-%m-%d"
        )

        is_recent = funding_date >= cutoff

        # Map funding type to stage
        stage_map = {
            "series_a": "series_a",
            "series_b": "series_b",
            "series_c": "series_c",
            "series_d": "series_d_plus",
            "seed": "seed",
            "pre_seed": "pre_seed",
            "angel": "angel",
            "convertible_note": "convertible_note",
            "venture": "venture",
            "debt": "debt",
            "grant": "grant",
        }

        funding_type = company_data.get(
            "last_funding_type", "other"
        )
        stage = stage_map.get(funding_type, "other")
        amount = company_data.get("last_funding_usd", 0) or 0

        # Valid for Segment 1 if $5M-$30M Series A/B
        valid_for_segment1 = (
            is_recent and
            stage in ["series_a", "series_b"] and
            5_000_000 <= amount <= 30_000_000
        )

        return {
            "detected": is_recent,
            "stage": stage,
            "amount_usd": amount,
            "closed_at": last_funding_at,
            "days_ago": (
                datetime.now() - funding_date
            ).days,
            "valid_for_segment1": valid_for_segment1,
            "source_url": company_data.get("homepage_url")
        }

    except Exception as e:
        return {
            "detected": False,
            "stage": "none",
            "amount_usd": 0,
            "closed_at": None,
            "error": str(e)
        }


def get_tech_stack(company_data: dict) -> list:
    """
    Extract tech stack from BuiltWith data.
    Maps to Tenacious bench stacks.
    """
    builtwith = company_data.get("builtwith_tech", [])

    if isinstance(builtwith, str):
        try:
            builtwith = json.loads(builtwith)
        except Exception:
            return []

    tech_names = [
        t.get("name", "").lower()
        for t in builtwith
        if isinstance(t, dict)
    ]

    # Map to Tenacious bench stacks
    stacks = set()

    python_tech = [
        "django", "flask", "fastapi",
        "python", "celery"
    ]
    data_tech = [
        "snowflake", "databricks", "dbt",
        "airflow", "fivetran", "powerbi"
    ]
    ml_tech = [
        "tensorflow", "pytorch", "hugging face",
        "langchain", "mlflow", "weights & biases"
    ]
    infra_tech = [
        "kubernetes", "terraform", "docker",
        "aws", "gcp", "datadog", "grafana"
    ]
    frontend_tech = [
        "react", "next.js", "typescript",
        "tailwind", "vue"
    ]

    for tech in tech_names:
        if any(p in tech for p in python_tech):
            stacks.add("python")
        if any(d in tech for d in data_tech):
            stacks.add("data")
        if any(m in tech for m in ml_tech):
            stacks.add("ml")
        if any(i in tech for i in infra_tech):
            stacks.add("infra")
        if any(f in tech for f in frontend_tech):
            stacks.add("frontend")

    return list(stacks)