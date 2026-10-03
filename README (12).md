# Opportunity Navigator — v1.6

Opportunity Navigator is a multilingual learning and university-navigation prototype for teenagers.

## University Planner in v1.6

The University Planner now has two entry points:

1. **I know the university** — enter the institution, discover its current Bachelor's programmes from official university sources, select a programme, then build a structured admissions plan.
2. **Help me find a university** — enter a country preference, field, interests, preferred teaching language and scholarship need. The planner searches current official university sources and produces a research shortlist of matching Bachelor's programmes.

The system is dynamic rather than a fixed preloaded list, so it can research universities beyond a small curated database. Coverage still depends on the university publishing accessible official information online.

## Requirement logic

v1.6 separates a **mandatory condition** from the **ways to satisfy it**.

For example:

- English proficiency can be a mandatory condition.
- IELTS, TOEFL, PTE or another accepted test can be alternative ways to satisfy that condition.
- If one qualifying result is enough, the UI says that clearly.
- A learner may take or submit several accepted alternatives by choice; extra alternatives are not shown as separately mandatory.

The same logic is used for entry routes such as SAT, ACT, university entrance tests, IB, A-levels, national exams, Olympiad routes and other official qualifications.

Supported selection rules include:

- **all required**;
- **one or more accepted options, minimum one**;
- **choose one official route**;
- **optional, choose any number**;
- **conditional only if applicable**.

## GPA / academic record

The app does **not** assume that every university publishes a universal numeric GPA cutoff.

It separates:

- school completion / diploma / transcript requirements;
- a published minimum GPA when one actually exists;
- GPA as one possible admission route where applicable;
- cases where no verified numeric GPA minimum is published.

## Official-source research

With `OPENAI_API_KEY` configured, the planner uses the OpenAI Responses API with web search forced on for admissions research. It searches current official university webpages and PDFs and asks for structured output containing:

- programme and language of instruction;
- academic requirements;
- English-proficiency alternatives and exact published scores;
- entrance routes and alternatives;
- programme-specific requirements;
- application documents;
- deadlines;
- financial-aid conditions;
- official optional/recommended items;
- official admissions contacts.

Returned URLs are filtered to the university's official domain before they are shown.

Without an API key, the app keeps a lighter official-site/Jina fallback. This fallback is useful but less capable of interpreting complex tables and route logic than the AI web-research mode.

## Undergraduate programme discovery

After a university is entered, the app can search its official programme catalog and show the Bachelor's programmes it finds. When available, each programme includes the official programme page, degree, school/faculty and teaching language.

## University recommendation

The finder does not present a prestige ranking. It produces a research shortlist based on the learner's chosen:

- country or global search;
- field/direction;
- interests and goals;
- preferred teaching language;
- scholarship/financial-aid need;
- target entry year.

The learner can select a suggested programme and continue directly into the admissions-requirements workflow.

## Language

The selected interface language controls the learner-facing UI. Research is normalized into canonical English internally and then translated to the selected interface language.

## Dependencies

```text
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
deep-translator>=1.11.4
openai>=2.0.0
```

## Streamlit secrets

```toml
OPENAI_API_KEY = "YOUR_API_KEY_HERE"
OPENAI_MODEL = "gpt-5"
```

Do not commit a real API key to GitHub.

## Important limitation

No system can guarantee access to literally every university website. Some institutions use login-only portals, CAPTCHAs, inaccessible JavaScript pages, or publish incomplete admissions information. Opportunity Navigator should leave a value unverified rather than inventing it.
