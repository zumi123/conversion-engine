import requests
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def check_leadership_change(
    company_name: str,
    domain: str = None,
    days: int = 90
) -> dict:
    """
    Check for new CTO or VP Engineering appointments
    in the last N days using public sources.

    Sources:
    1. Crunchbase ODM people data (leadership_hire field)
    2. LinkedIn public profile hints via job post language
    3. Press release scraping via Google News RSS
    """
    result = {
        "detected": False,
        "role": "none",
        "new_leader_name": None,
        "started_at": None,
        "source_url": None,
        "confidence": "low",
        "method": None
    }

    # Source 1: Check Crunchbase ODM leadership_hire field
    crunchbase_result = _check_crunchbase_leadership(
        company_name
    )
    if crunchbase_result["detected"]:
        return crunchbase_result

    # Source 2: Check Google News RSS for press releases
    news_result = _check_news_rss(company_name, days)
    if news_result["detected"]:
        return news_result

    # Source 3: Check job posts for "new CTO" language
    jobpost_result = _check_job_signals(company_name)
    if jobpost_result["detected"]:
        return jobpost_result

    return result


def _check_crunchbase_leadership(
    company_name: str
) -> dict:
    """
    Check Crunchbase ODM sample for leadership_hire data.
    """
    data_path = os.path.join(
        os.path.dirname(__file__),
        "../data/crunchbase_sample.json"
    )

    try:
        with open(data_path, "r") as f:
            companies = json.load(f)

        for company in companies:
            if company_name.lower() not in \
                    company.get("name", "").lower():
                continue

            leadership_hire = company.get(
                "leadership_hire", "[]"
            )
            if isinstance(leadership_hire, str):
                try:
                    leadership_hire = json.loads(
                        leadership_hire
                    )
                except Exception:
                    continue

            if not leadership_hire:
                continue

            cutoff = datetime.now() - timedelta(days=90)

            for hire in leadership_hire:
                if not isinstance(hire, dict):
                    continue

                title = hire.get("title", "").lower()
                is_leadership = any(
                    role in title for role in [
                        "cto", "vp engineering",
                        "vp of engineering",
                        "chief technology",
                        "head of engineering",
                        "engineering director"
                    ]
                )

                if not is_leadership:
                    continue

                started = hire.get("started_on", "")
                if started:
                    try:
                        start_date = datetime.strptime(
                            started[:10], "%Y-%m-%d"
                        )
                        if start_date >= cutoff:
                            role_map = {
                                "cto": "cto",
                                "chief technology": "cto",
                                "vp engineering": "vp_engineering",
                                "vp of engineering": "vp_engineering",
                                "head of engineering": "vp_engineering"
                            }
                            role = "other"
                            for k, v in role_map.items():
                                if k in title:
                                    role = v
                                    break

                            return {
                                "detected": True,
                                "role": role,
                                "new_leader_name": hire.get(
                                    "name", ""
                                ),
                                "started_at": started[:10],
                                "source_url": (
                                    f"https://crunchbase.com/"
                                    f"organization/"
                                    f"{company.get('id', '')}"
                                ),
                                "confidence": "high",
                                "method": "crunchbase_odm"
                            }
                    except Exception:
                        continue

    except Exception as e:
        print(f"  Crunchbase leadership check error: {e}")

    return {"detected": False}


def _check_news_rss(
    company_name: str,
    days: int = 90
) -> dict:
    """
    Check Google News RSS for CTO/VP Engineering
    appointment press releases.
    No login required — public RSS feed.
    """
    try:
        query = (
            f"{company_name} "
            f"(CTO OR 'VP Engineering' OR 'Chief Technology') "
            f"appointed OR joins OR named OR hires"
        )
        rss_url = (
            f"https://news.google.com/rss/search?"
            f"q={requests.utils.quote(query)}"
            f"&hl=en-US&gl=US&ceid=US:en"
        )

        response = requests.get(
            rss_url,
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; "
                    "ConversionEngine/1.0)"
                )
            }
        )

        if response.status_code != 200:
            return {"detected": False}

        content = response.text.lower()
        cutoff_str = (
            datetime.now() - timedelta(days=days)
        ).strftime("%Y")

        # Look for leadership keywords in recent news
        leadership_keywords = [
            "appointed cto",
            "new cto",
            "joins as cto",
            "named cto",
            "vp of engineering",
            "vp engineering",
            "chief technology officer"
        ]

        company_lower = company_name.lower()
        found_keyword = None

        for kw in leadership_keywords:
            if kw in content and company_lower in content:
                found_keyword = kw
                break

        if found_keyword:
            # Extract article URL from RSS
            import re
            urls = re.findall(
                r'<link>(https?://[^<]+)</link>',
                response.text
            )
            source_url = urls[1] if len(urls) > 1 else None

            role = "cto"
            if "vp" in found_keyword or "engineering" in found_keyword:
                role = "vp_engineering"

            return {
                "detected": True,
                "role": role,
                "new_leader_name": None,
                "started_at": None,
                "source_url": source_url,
                "confidence": "medium",
                "method": "google_news_rss",
                "keyword_found": found_keyword
            }

    except Exception as e:
        print(f"  News RSS check error: {e}")

    return {"detected": False}


def _check_job_signals(company_name: str) -> dict:
    """
    Check if company has job posts suggesting
    a leadership transition (e.g. 'reporting to new CTO').
    Weak signal — low confidence only.
    """
    try:
        response = requests.get(
            "https://remoteok.com/api",
            headers={
                "User-Agent": "ConversionEngine/1.0"
            },
            timeout=10
        )
        jobs = response.json()

        transition_keywords = [
            "new cto", "new vp", "newly appointed",
            "leadership transition", "join our leadership"
        ]

        for job in jobs:
            if not isinstance(job, dict):
                continue
            company = job.get("company", "").lower()
            desc = job.get("description", "").lower()

            if company_name.lower() not in company:
                continue

            for kw in transition_keywords:
                if kw in desc:
                    return {
                        "detected": True,
                        "role": "other",
                        "new_leader_name": None,
                        "started_at": None,
                        "source_url": job.get("url"),
                        "confidence": "low",
                        "method": "job_post_signal",
                        "keyword_found": kw
                    }

    except Exception as e:
        print(f"  Job signal check error: {e}")

    return {"detected": False}