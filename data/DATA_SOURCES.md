# Data Sources — Substitutions and Known Gaps

## Crunchbase ODM (1,001 companies)
- Status: ✅ Using as specified
- Location: data/crunchbase_sample.json, data/crunchbase_sample.csv
- License: Apache 2.0

## Job Post Velocity
- Required: BuiltIn, Wellfound, LinkedIn via Playwright
- Actual: RemoteOK public API
- Reason: Wellfound and LinkedIn blocked by Cloudflare
  on the Ethiopia-based server (197.156.71.65). Attempted
  Playwright scraping on Day 0 — both returned 403/captcha.
  RemoteOK is an open API with no auth required.
- Impact: Lower coverage. RemoteOK has ~100 listings vs
  thousands on LinkedIn. Company-specific job counts are
  often 0 for companies not posting on RemoteOK.
- Mitigation: The frozen job post dataset provided in the
  seed repo could supplement this. Playwright scraping of
  individual company careers pages (e.g., careers.stripe.com)
  is implemented in job_posts.py as a secondary source.

## layoffs.fyi
- Required: Downloadable CSV (CC-BY)
- Actual: Not yet downloaded — export URL is login-gated
- Impact: All prospects show layoff_event.detected: false.
  Segment 2 classification cannot fire.
- Fix: Download from HuggingFace mirror and place at
  data/layoffs.csv

## Leadership Change
- Required: Crunchbase + press releases
- Actual: ✅ Crunchbase ODM leadership_hire field +
  Google News RSS + job post keyword signals
- Note: Google News RSS has known false positive rate
  for companies with common names (see Probe 7.2 results)

## Tech Stack (BuiltWith / Wappalyzer)
- Required: BuiltWith or Wappalyzer public data
- Actual: Not implemented as standalone signal
- Current: Tech stack inferred from job post keywords
  and Crunchbase builtwith_tech field
- Impact: tech_stack_inferred_not_confirmed honesty flag
  fires for all prospects not in ODM sample