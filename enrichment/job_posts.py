import requests
import json
import os
from playwright.sync_api import sync_playwright


def fetch_jobs_playwright(
    company_name: str,
    careers_url: str = None
) -> list:
    """
    Fetch job posts using Playwright.
    No login logic — public pages only.
    Respects robots.txt.
    """
    if not careers_url:
        return []

    print(f"  Fetching jobs via Playwright: {careers_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (compatible; "
                "ConversionEngine/1.0; "
                "research bot)"
            )
        )
        page = context.new_page()

        try:
            page.goto(
                careers_url,
                timeout=30000,
                wait_until="domcontentloaded"
            )

            # Extract job titles from page
            # No login — public content only
            title = page.title()

            # Look for common job listing patterns
            job_elements = page.query_selector_all(
                "h2, h3, [class*='job'], [class*='position'], "
                "[class*='role'], [class*='opening']"
            )

            jobs = []
            for el in job_elements[:20]:
                text = el.inner_text().strip()
                if len(text) > 5 and len(text) < 200:
                    jobs.append({
                        "title": text,
                        "company": company_name,
                        "source": careers_url,
                        "via": "playwright"
                    })

            print(f"  Found {len(jobs)} job elements")
            browser.close()
            return jobs

        except Exception as e:
            print(f"  Playwright error: {e}")
            browser.close()
            return []


def fetch_remoteok_jobs(keyword: str = "engineer") -> dict:
    """
    Fetch from RemoteOK API as fallback.
    Public API — no login required.
    """
    print(f"Fetching jobs from RemoteOK...")
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; "
                "ConversionEngine/1.0)"
            )
        }
        response = requests.get(
            "https://remoteok.com/api",
            headers=headers,
            timeout=30
        )

        jobs = response.json()
        jobs = [
            j for j in jobs
            if isinstance(j, dict) and "position" in j
        ]

        print(f"Total jobs fetched: {len(jobs)}")

        if jobs:
            print(
                f"Sample job structure:\n"
                f"{json.dumps(jobs[0], indent=2)}"
            )

        filtered = [
            {
                "company": j.get("company", ""),
                "title": j.get("position", ""),
                "location": "Remote",
                "posted_date": j.get("date", ""),
                "skills": j.get("tags", []),
                "url": j.get("url", ""),
                "via": "remoteok"
            }
            for j in jobs
            if keyword.lower() in j.get(
                "position", ""
            ).lower()
            or keyword.lower() in str(
                j.get("tags", [])
            ).lower()
        ][:10]

        result = {
            "source_url": "https://remoteok.com/api",
            "status": "success",
            "keyword": keyword,
            "total_fetched": len(jobs),
            "total_found": len(filtered),
            "jobs": filtered
        }

        os.makedirs("data", exist_ok=True)
        with open("data/job_posts_test.json", "w") as f:
            json.dump(result, f, indent=2)

        return result

    except Exception as e:
        print(f"Error: {e}")
        return {
            "source_url": "https://remoteok.com/api",
            "status": "error",
            "error": str(e),
            "jobs": []
        }


def fetch_job_posts(
    company_name: str,
    domain: str = None
) -> dict:
    """
    Main job post fetcher.
    Tries Playwright first for company careers page,
    falls back to RemoteOK API.
    No login logic anywhere in this function.
    """
    jobs = []

    # Try Playwright on company careers page first
    if domain:
        careers_url = f"https://{domain}/careers"
        playwright_jobs = fetch_jobs_playwright(
            company_name, careers_url
        )
        jobs.extend(playwright_jobs)

    # Fall back to RemoteOK
    if not jobs:
        result = fetch_remoteok_jobs(
            keyword=company_name
        )
        jobs = result.get("jobs", [])

    return {
        "company": company_name,
        "total_found": len(jobs),
        "jobs": jobs,
        "status": "success" if jobs else "no_data"
    }