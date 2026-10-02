# Opportunity Navigator — v1.4

## University Planner: AI-first official admissions research

v1.4 changes the research architecture rather than adding another regex patch.

### Research order
1. Curated verified profile, when available.
2. Official-site discovery.
3. If `OPENAI_API_KEY` is configured: AI-first web research across the official university domain, including admissions pages and PDFs.
4. A second targeted AI pass automatically runs when English-test or entrance-exam information is still missing.
5. Without an API key, the fallback now uses university sitemaps, targeted same-domain searches, table-aware HTML extraction, Jina Reader and conservative score validation.
6. If a requirement remains unverified, official admissions contacts are shown instead of a guessed value.

### Important improvements
- Keeps HTML tables instead of flattening them away.
- Searches official admissions-policy PDFs.
- Distinguishes first-year, transfer, mid-year, foundation and other admission pathways instead of mixing their scores.
- Keeps IELTS overall and section/subscore requirements together.
- Validates common exam scales before displaying a score.
- Rejects document IDs, years and URL numbers as exam scores.
- Uses strict structured JSON when the configured OpenAI model supports it.
- Filters AI results back to official university-domain URLs.

### OpenAI web research
Add your key in Streamlit Community Cloud → Manage app → Settings → Secrets:

```toml
OPENAI_API_KEY = "YOUR_API_KEY"
OPENAI_MODEL = "gpt-5"
```

Do not commit a real API key to GitHub.

## Dependencies
```text
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
deep-translator>=1.11.4
openai>=2.0.0
```

No automated system can guarantee access to every protected or login-only page. The planner therefore shows only verified official information and leaves missing values unverified rather than inventing them.

