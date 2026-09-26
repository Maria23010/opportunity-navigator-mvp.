# Opportunity Navigator — v0.9

A bilingual (English / Russian) Streamlit prototype for adolescents who need learning, admissions and opportunity navigation in one place.

## What changed in v0.9

- Added an always-visible interface-language selector: English / Русский.
- Country and language names are localized with pycountry's ISO translation catalogues.
- Russian UI now covers navigation, profile, pathway, AI Tutor, Learning Hub, Motivation, Human Support, Community, Opportunities and the University Planner.
- Added a curated admissions record for Istanbul Aydın University — Industrial Engineering, including current official pages plus clearly labelled historical score evidence where current minimums are not published.
- University Planner now uses one generic curated-record renderer instead of MBZUAI-specific labels for every supported university.
- Added separate gap analysis for MBZUAI and Istanbul Aydın University.
- Unknown universities still use official-site discovery as a fallback, but user-facing failures are shown as plain language rather than technical tracebacks.
- Preserved adaptive learning, follow-up tutoring, privacy filtering, saved opportunities and refresh persistence.

## Deployment

Use Python 3.11 on Streamlit Community Cloud.

`requirements.txt`:

```text
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
```

Main file: `app.py`

## Admissions-data honesty

The planner distinguishes:
- current published requirements;
- historical official values that must be re-verified for a future intake;
- information that is not currently published and therefore must not be invented.

For unknown universities, automated extraction is a research aid, not a guaranteed complete admissions database.
