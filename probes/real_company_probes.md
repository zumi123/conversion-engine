# Real Company Probes — Run Against Crunchbase ODM Companies

Executed 2026-04-24 against 5 real companies from the ODM sample.

## Critical Finding: Google News RSS False Positive Rate

Leadership detected via google_news_rss for ALL 5 companies tested.
This is a 100% false positive rate on this sample.

Wickr (51-100 employees, US, messaging company) was classified
as Segment 3 (leadership transition) at 0.85 confidence based
entirely on a false RSS match. If this were a real prospect,
Tenacious would send a pitch referencing "your new CTO" to
a company that does not have a new CTO.

### False positive rate: 5/5 = 100%

| Company | Leadership detected | Method | Likely real? |
|---|---|---|---|
| Wit.ai | True | google_news_rss | NO — owned by Meta |
| Semantica | True | google_news_rss | NO — no evidence |
| Wickr | True | google_news_rss | NO — acquired by AWS |
| SnapTrade | True | google_news_rss | NO — 1-10 person startup |
| Whitehill Technologies | True | google_news_rss | NO — enterprise software |

### Impact on classification
- Wickr: incorrectly classified Segment 3 at 0.85 confidence
- Whitehill Technologies: incorrectly classified Segment 3 at 0.85 confidence
- Other 3: correctly abstained despite false leadership signal
  (saved by headcount gate or low AI maturity)

### Root cause
The RSS scraper checks if company_name.lower() appears
anywhere in the RSS response body. Common words like "wit"
and "snap" match unrelated articles. The proximity check
between company name and leadership keywords is too loose.

### Severity: CRITICAL (honesty category)

This is the highest-severity bug found during Act III.
It would cause Tenacious to send wrong-segment pitches
to real prospects.