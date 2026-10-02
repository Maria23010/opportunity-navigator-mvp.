# Opportunity Navigator — v1.2

Opportunity Navigator is a multilingual learning and admissions-navigation prototype.

## What changed in v1.2

### 1. Language selection now visibly works
The sidebar language selector was fixed so the selected value is readable on the dark sidebar.

A visible badge now shows the active interface language.

Country and interface language remain separate settings.

### 2. Broader interface translation
Most learner-facing Streamlit labels that previously stayed in English are now routed through the translation layer.

Translation order:
1. curated English/Russian text where available;
2. GoogleTranslator;
3. MyMemory fallback;
4. optional OpenAI translation fallback when `OPENAI_API_KEY` is configured.

Proper nouns, exam names, university names and official source URLs are preserved where appropriate.

### 3. Deeper University Planner research
For universities that do not have a curated record, v1.2 keeps the existing public-web fallback and adds an optional deeper research mode.

When `OPENAI_API_KEY` is configured, the planner uses the OpenAI Responses API with web search to research the target university and programme.

It asks for:
- programme-specific academic requirements;
- entrance exams;
- IELTS / TOEFL / PTE / Duolingo and other English tests;
- SAT / ACT / IB / A-level / national or programme-specific exams where relevant;
- exact published minimum scores;
- deadlines;
- application documents;
- scholarships / financial aid;
- official admissions contacts.

The research prompt explicitly requires official university sources and tells the model not to invent missing numeric scores.

Each returned requirement is expected to carry its official source URL.

### 4. Safer fallback
If deep research is unavailable or incomplete, the app falls back to the existing official-site/Jina research pipeline and then to official admissions contacts.

## Enabling deep web research on Streamlit

In Streamlit Community Cloud:

1. Open your app.
2. Go to **Manage app → Settings → Secrets**.
3. Add:

```toml
OPENAI_API_KEY = "YOUR_API_KEY_HERE"
OPENAI_MODEL = "gpt-5"
```

Do not commit a real API key to GitHub.

The app still runs without this secret, but University Planner uses the lighter public-web research fallback.

## Dependencies

```text
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
deep-translator>=1.11.4
openai>=2.0.0
```

## Important prototype limitation

No web-research system can guarantee access to every protected, login-only or CAPTCHA-gated page. The planner is designed to prefer verified official information, expose sources, and leave an item unverified rather than invent a requirement.

