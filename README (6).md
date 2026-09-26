# Opportunity Navigator — v1.0

Opportunity Navigator is a research-driven prototype for adolescents who need learning, admissions and opportunity navigation in one place.

## What v1.0 adds

### Global university research
The University Planner now uses a multi-source pipeline:
1. a verified structured university record when one exists;
2. a user-provided official URL if available;
3. Wikidata official-site discovery;
4. global web search through Jina Search;
5. direct official-site reading;
6. Jina Reader fallback for sites that block Streamlit or need browser-style rendering.

The app keeps source URLs attached to extracted requirements and does not invent a score when it cannot verify one.

No free prototype can guarantee access to literally every website: some sites block automation, require login, or expose data only after interactive JavaScript. v1.0 is designed to fail safely and use multiple fallbacks instead of sending the learner to a generic search engine.

### Multilingual interface
Country and interface language are separate settings.
- Countries come from `pycountry`.
- Interface-language choices come from the translation engine's supported-language list.
- English and Russian keep hand-edited UI strings where available.
- Other supported languages use cached automatic translation.
- Extracted university information is translated for the learner while the official source link remains available.

## Dependencies

```text
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
deep-translator>=1.11.4
```

## Main file
`app.py`

## Important prototype limitations
- Automatic translation depends on an external translation service and may occasionally fall back to English.
- Global university research is best-effort; no scraper can guarantee access to every protected/login-only website.
- Extracted facts should remain source-linked and rechecked before a real application.
