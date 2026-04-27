import requests
import os
import json
import re
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
    2. Press release scraping via Google News RSS
    3. Job post language hints
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

    # Skip if company name is too short (high false positive risk)
    if len(company_name.strip()) < 4:
        return result

    # Source 1: Check Crunchbase ODM leadership_hire field
    crunchbase_result = _check_crunchbase_leadership(
        company_name
    )
    if crunchbase_result.get("detected"):
        return crunchbase_result

    # Source 2: Check Google News RSS for press releases
    news_result = _check_news_rss(company_name, days)
    if news_result.get("detected"):
        return news_result

    # Source 3: Check job posts for "new CTO" language
    jobpost_result = _check_job_signals(company_name)
    if jobpost_result.get("detected"):
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

            if not isinstance(leadership_hire, list) or \
                    not leadership_hire:
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

    STRICT matching rules:
    1. Only check article titles inside <item> blocks
       (skip the feed-level title which contains our query)
    2. Company name must appear in the article title
    3. A leadership keyword must appear in same title
    4. An appointment verb must appear in same title
    5. Company must appear before the verb (subject check)
       to avoid "OtherCo hires ex-CompanyName person"
    """
    # Skip short names — too many false positives
    if len(company_name.strip()) < 4:
        return {"detected": False}

    try:
        query = (
            f'"{company_name}" '
            f"(CTO OR \"VP Engineering\" OR "
            f"\"Chief Technology\") "
            f"(appointed OR joins OR named OR hires)"
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

        # Extract only article titles inside <item> blocks
        # Skip feed-level <title> which contains our query
        items = re.findall(
            r'<item>(.*?)</item>',
            response.text,
            re.DOTALL
        )

        titles = []
        for item in items:
            # Try CDATA first
            match = re.search(
                r'<title><!\[CDATA\[(.*?)\]\]></title>',
                item
            )
            if not match:
                match = re.search(
                    r'<title>(.*?)</title>',
                    item
                )
            if match:
                titles.append(match.group(1))

        # Leadership keywords to look for
        leadership_keywords = [
            "cto",
            "chief technology officer",
            "vp of engineering",
            "vp engineering",
            "head of engineering"
        ]

        # Appointment verbs — must also be present
        appointment_verbs = [
            "appoints", "appointed", "names",
            "named", "hires", "hired",
            "joins as", "announces"
        ]

        company_lower = company_name.lower()

        # Check each article title individually
        for title in titles:
            title_lower = title.lower()

            # Rule 1: Company name must be in this title
            if company_lower not in title_lower:
                continue

            # Rule 2: An appointment verb must be present
            has_verb = any(
                v in title_lower for v in appointment_verbs
            )
            if not has_verb:
                continue

            # Rule 3: Company must be the SUBJECT
            # (appear before or near the verb, not after)
            # "Snap appoints new CTO" = good
            # "Nubank hires ex-Snap exec" = bad
            company_pos = title_lower.find(company_lower)
            verb_positions = [
                title_lower.find(v)
                for v in appointment_verbs
                if v in title_lower
            ]
            if verb_positions:
                earliest_verb = min(
                    p for p in verb_positions if p >= 0
                )
                # If company appears well after the verb,
                # it's likely the source, not the subject
                if company_pos > earliest_verb + 15:
                    continue

            # Rule 4: A leadership keyword in same title
            for kw in leadership_keywords:
                if kw in title_lower:
                    # Extract article URLs from RSS
                    urls = re.findall(
                        r'<link>(https?://[^<]+)</link>',
                        response.text
                    )
                    source_url = (
                        urls[1] if len(urls) > 1 else None
                    )

                    role = "cto"
                    if "vp" in kw or \
                            "head of engineering" in kw:
                        role = "vp_engineering"

                    return {
                        "detected": True,
                        "role": role,
                        "new_leader_name": None,
                        "started_at": None,
                        "source_url": source_url,
                        "confidence": "medium",
                        "method": "google_news_rss",
                        "keyword_found": kw,
                        "matched_title": title[:100]
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
    # Skip short names
    if len(company_name.strip()) < 4:
        return {"detected": False}

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

            # Strict match: company name must match
            # the job's company field exactly
            if company_name.lower() != company:
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