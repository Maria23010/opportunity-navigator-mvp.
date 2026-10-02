# Opportunity Navigator — v1.5

Opportunity Navigator is a multilingual learning and university-admissions navigation prototype for teenagers.

## v1.5 — clearer admissions logic

The University Planner is redesigned around a child-facing question: **what do I actually have to do?**

Instead of showing every discovered exam in one flat list, the planner now separates:

- **REQUIRED** — requirements that apply to every applicant in the selected route;
- **CHOOSE ONE** — alternative tests or qualification routes; the learner should not assume all of them are required;
- **ONLY IF APPLICABLE** — financial-aid, Olympiad, interview, waiver, visa or other conditional rules;
- **OPTIONAL** — genuine optional/recommended items;
- **NOT REQUIRED** — items such as a portfolio when the current official rules do not require one.

For English-language requirements, accepted tests are displayed as alternatives. For entry qualifications, SAT, ACT, NUET, IB, A-level and other pathways can be grouped as alternatives when the official rules say one route is sufficient.

## Multilingual output

The interface language now controls both static UI labels and dynamically researched admissions content. Deep research returns canonical English internally and the learner-facing layer translates it into the selected interface language.

This avoids mixed-language results when an official source is written in Russian, Kazakh, Turkish, Arabic or another language.

## Nazarbayev University verified profile

v1.5 includes a source-linked structured profile for Nazarbayev University undergraduate admission so the prototype demonstrates the intended UX even without an API key. It distinguishes:

- English proficiency: IELTS **or** TOEFL;
- one entry qualification route rather than every exam;
- NUET, Digital SAT, ACT, Olympiad, IB, A-level/NIS, GPA and UNT routes;
- fee-paying thresholds versus financial-support rules;
- official requirements versus optional profile-building suggestions.

The Computer Science programme is mapped to its Artificial Intelligence and Data Science tracks when the learner searches for those fields.

## General university research

For other universities the planner uses, in order:

1. a verified structured profile when available;
2. OpenAI Responses API web research when `OPENAI_API_KEY` is configured;
3. official-site discovery, direct reading, Jina Search/Reader and conservative extraction;
4. official admissions contacts when a requirement cannot be verified.

The deep-research prompt explicitly asks for official webpages/PDFs, table-aware interpretation, all accepted routes, exact minimums, and mandatory/alternative/conditional classification.

The no-API fallback no longer shows long unstructured scraped paragraphs to the learner. It only shows high-confidence published values and labels route logic as unverified rather than guessing.

## Streamlit Secrets for deep research

In Streamlit Community Cloud, add the API key under **Manage app → Settings → Secrets**:

```toml
OPENAI_API_KEY = "YOUR_API_KEY_HERE"
OPENAI_MODEL = "gpt-5"
```

Never commit a real API key to GitHub.

## Dependencies

```text
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
deep-translator>=1.11.4
openai>=2.0.0
```

## Important limitation

Admissions requirements change. The app keeps official source links attached to requirements and should never invent a missing score. A production version would expand the verified-profile database and continuously re-check source changes.

