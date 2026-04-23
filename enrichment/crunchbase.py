import json
import os
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
    e.g. '11-50' -> 30, '1-10' -> 5
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


def parse_funding_rounds(funding_str: str) -> dict:
    """
    Parse funding_rounds JSON string.
    Returns funding info dict.
    """
    if not funding_str or funding_str == "{}":
        return {}
    try:
        if isinstance(funding_str, str):
            return json.loads(funding_str)
        return funding_str
    except Exception:
        return {}


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
                domain in website or
                domain in url
            )
        )

        if name_match or domain_match:
            return _normalize_company(company)

    # Not found - use mock
    print(f"  Company '{company_name}' not in ODM sample "
          f"- using mock data")
    return _mock_company(company_name, domain)


def _normalize_company(raw: dict) -> dict:
    """
    Normalize raw Crunchbase CSV row to 
    standard format.
    """
    # Parse funding rounds
    funding_rounds = parse_funding_rounds(
        raw.get("funding_rounds", "{}")
    )

    # Get funding info
    last_funding_at = None
    last_funding_usd = 0
    last_funding_type = "none"

    funding_list = raw.get("funding_rounds_list", "[]")
    if isinstance(funding_list, str):
        try:
            funding_list = json.loads(funding_list)
        except Exception:
            funding_list = []

    if funding_list:
        # Get most recent funding round
        latest = funding_list[-1] if funding_list else {}
        last_funding_at = latest.get(
            "announced_on", None
        )
        last_funding_usd = latest.get(
            "money_raised_usd", 0
        ) or 0
        last_funding_type = latest.get(
            "series", "other"
        ).lower().replace(" ", "_")

    return {
        "crunchbase_id": raw.get("id", ""),
        "name": raw.get("name", ""),
        "homepage_url": raw.get("website", ""),
        "short_description": raw.get("about", ""),
        "employee_count": parse_employee_count(
            raw.get("num_employees", "0")
        ),
        "funding_total_usd": last_funding_usd,
        "last_funding_type": last_funding_type,
        "last_funding_at": last_funding_at,
        "last_funding_usd": last_funding_usd,
        "country_code": raw.get("country_code", ""),
        "city": raw.get("address", "").split(",")[0],
        "categories": raw.get("industries", ""),
        "ipo_status": raw.get("ipo_status", "private"),
        "operating_status": raw.get(
            "operating_status", "active"
        ),
        "builtwith_tech": raw.get("builtwith_tech", "[]"),
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
        "funding_total_usd": 14000000,
        "last_funding_type": "series_a",
        "last_funding_at": (
            datetime.now() - timedelta(days=90)
        ).strftime("%Y-%m-%d"),
        "last_funding_usd": 14000000,
        "country_code": "USA",
        "city": "San Francisco",
        "categories": ["artificial-intelligence", "saas"],
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
        # Try multiple date formats
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
            try:
                funding_date = datetime.strptime(
                    last_funding_at[:10], "%Y-%m-%d"
                )
                break
            except Exception:
                continue
        else:
            return {
                "detected": False,
                "stage": "none",
                "amount_usd": 0,
                "closed_at": None
            }

        is_recent = funding_date >= cutoff

        # Map funding type to stage
        stage_map = {
            "series_a": "series_a",
            "series_b": "series_b",
            "series_c": "series_c",
            "series_d": "series_d_plus",
            "seed": "seed",
            "debt_financing": "debt",
            "debt": "debt"
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
    builtwith = company_data.get("builtwith_tech", "[]")

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