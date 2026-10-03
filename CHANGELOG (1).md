# Changelog — v2.1

## Global Admissions Engine
- Moved global university research into `global_admissions_engine.py`.
- Added country normalization and local-language field aliases.
- Added sitemap and internal-link discovery on official university domains.
- Added HTML-table preservation and PDF text extraction.
- Added Jina Reader fallback for difficult university pages.
- Added Serper and Tavily as optional search providers.
- Kept Jina, DuckDuckGo and Bing as no-key fallbacks.
- Added Wikidata country-wide university registry fallback.

## University finder
- Rejects obvious non-university websites and search engines.
- Requires a matching undergraduate programme on the university's own domain.
- Keeps official university and programme names.
- Separately researches scholarship / financial-aid availability.

## Admissions requirements
- Searches testing, admissions, international, deadline, document and funding pages.
- Separates mandatory conditions from alternative ways to satisfy them.
- Distinguishes minimum, competitive guidance, no-minimum, no-cutoff and pathway-specific values.
- Reads current official-source bundles with OpenAI / Gemini / Claude when configured.
- Falls back to deterministic official-page extraction when AI providers are unavailable.

## Deployment
- `app.py` and `global_admissions_engine.py` must now stay together in the repository root.
- Added `pypdf>=5.0`.
- Added optional `SERPER_API_KEY` and `TAVILY_API_KEY` secrets.

