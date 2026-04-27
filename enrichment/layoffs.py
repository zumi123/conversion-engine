import csv
import os
import requests
from datetime import datetime, timedelta


def check_layoffs(company_name: str, days: int = 120) -> dict:
    """
    Check layoffs.fyi for layoff events for a company
    in the last N days.
    """
    layoffs_path = os.path.join(
        os.path.dirname(__file__),
        "../data/layoffs.csv"
    )

    # Try loading local CSV first
    if os.path.exists(layoffs_path):
        return _check_local_csv(company_name, layoffs_path, days)

    # Fall back to mock
    print("layoffs.csv not found - returning no layoff signal")
    return {
        "detected": False,
        "date": None,
        "headcount_reduction": 0,
        "percentage_cut": 0.0,
        "source_url": "https://layoffs.fyi",
        "signal_confidence": "low"
    }


def _check_local_csv(
    company_name: str,
    csv_path: str,
    days: int
) -> dict:
    """Check local layoffs.csv for company events."""
    cutoff = datetime.now() - timedelta(days=days)

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Match company name (fuzzy)
                csv_company = row.get("company", "")
                if company_name.lower() not in \
                        csv_company.lower():
                    continue

                try:
                    date_str = row.get("date", "")
                    if not date_str:
                        continue

                    # Handle both date formats
                    # "2024-01-15" or "1/15/2024"
                    try:
                        layoff_date = datetime.strptime(
                            date_str, "%Y-%m-%d"
                        )
                    except ValueError:
                        try:
                            layoff_date = datetime.strptime(
                                date_str, "%m/%d/%Y"
                            )
                        except ValueError:
                            continue

                    if layoff_date >= cutoff:
                        pct_str = row.get(
                            "percentage_laid_off", ""
                        ) or "0"
                        try:
                            pct = float(pct_str)
                        except ValueError:
                            pct = 0.0

                        count_str = row.get(
                            "total_laid_off", ""
                        ) or "0"
                        try:
                            count = int(float(count_str))
                        except ValueError:
                            count = 0

                        return {
                            "detected": True,
                            "date": date_str,
                            "headcount_reduction": count,
                            "percentage_cut": pct,
                            "source_url": row.get(
                                "source",
                                "https://layoffs.fyi"
                            ),
                            "days_ago": (
                                datetime.now() - layoff_date
                            ).days,
                            "signal_confidence": "high"
                        }
                except Exception:
                    continue
    except Exception as e:
        print(f"Error reading layoffs CSV: {e}")

    return {
        "detected": False,
        "date": None,
        "headcount_reduction": 0,
        "percentage_cut": 0.0,
        "source_url": "https://layoffs.fyi",
        "signal_confidence": "low"
    }


def download_layoffs_csv():
    """Download latest layoffs.fyi data."""
    url = "https://layoffs.fyi/export"
    os.makedirs("data", exist_ok=True)

    try:
        response = requests.get(url, timeout=30)
        with open("data/layoffs.csv", "w") as f:
            f.write(response.text)
        print("layoffs.csv downloaded successfully")
    except Exception as e:
        print(f"Could not download layoffs.csv: {e}")