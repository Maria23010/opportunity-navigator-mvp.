# Opportunity Navigator — v2.1

## Global Admissions Engine

v2.1 replaces the old university-search logic with a separate global admissions engine.

### What it now does

**University discovery**
- normalizes country names such as `Turkey` / `Türkiye`, `USA` / `United States`;
- expands fields into synonyms and local-language names;
- searches through Serper and Tavily when API keys are connected;
- falls back to Jina, DuckDuckGo and Bing;
- verifies institutions and rejects search engines, course platforms and obvious non-university providers;
- uses Wikidata as an independent country-wide university registry fallback when web search is sparse.

**Programme discovery**
- searches the official university domain;
- reads sitemaps and internal navigation;
- supports local-language programme names;
- keeps official university/programme names instead of translating proper names;
- filters out graduate-only pages when the learner asked for Bachelor's study.

**Admissions research**
- reads official HTML pages, tables and PDFs;
- checks admissions, international applicants, testing, programme, deadlines, documents and funding pages;
- can cross-check the same official source bundle with OpenAI, Gemini and Claude when their API keys are connected;
- keeps deterministic extraction as a fallback when AI providers are unavailable.

**Requirement semantics**
The engine distinguishes:
- official minimum;
- competitive / typical guidance;
- no numeric minimum;
- required test with no cutoff;
- pathway-specific score;
- mandatory requirement;
- conditional requirement;
- choose-one alternative;
- optional item.

It does **not** invent a SAT / ACT / IELTS / TOEFL / GPA cutoff when the university does not publish one.

**Funding**
The engine separately looks for:
- scholarships;
- need-based aid;
- tuition waivers;
- full tuition;
- fully funded / tuition-free routes.

Funding rules are never mixed into the base admissions requirements.

## Important deployment change

`app.py` now imports:

```python
global_admissions_engine.py
```

So **both files must be uploaded to the root of the GitHub repository**.

The root of the repository should contain at least:

```text
app.py
global_admissions_engine.py
requirements.txt
README.md
CHANGELOG.md
```

Do not upload only `app.py`.

## Recommended Streamlit Secrets

The engine works without paid keys, but global reliability improves when search/API providers are connected.

```toml
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-5.6-sol"

GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-3.8-flash"

ANTHROPIC_API_KEY = ""
ANTHROPIC_MODEL = ""

SERPER_API_KEY = ""
TAVILY_API_KEY = ""
```

You do not need every key. Leave unused values empty.

For university **discovery**, a dedicated web-search provider such as Serper or Tavily is especially useful because Streamlit Cloud can sometimes be blocked by public search engines.

## Dependencies

```text
streamlit>=1.40,<2
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
deep-translator>=1.11.4
pypdf>=5.0
openai>=2.0.0
google-genai>=1.0.0
anthropic>=0.70.0
```

## Honest limitation

No automated system can guarantee access to literally every admissions page worldwide. Some universities use CAPTCHA, login-only portals, JavaScript-only pages or scanned documents. v2.1 is designed to maximize coverage through several independent discovery routes while leaving unverified values blank instead of fabricating them.
