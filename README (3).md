# Opportunity Navigator — v1.3

## Main fixes

### Language selector
- The selected language is now readable inside the sidebar dropdown.
- The active language remains visible below the selector.
- A direct web-translation fallback was added before the previous translation providers.
- Kazakh has a built-in core UI fallback so the main navigation and Home page do not remain English when a translation service is temporarily unavailable.
- Other supported languages continue through the cached translation pipeline.

### University Planner
- University-site discovery now rejects person/government entities that were previously able to masquerade as a university result.
- Wikidata results must look like an educational institution before their website is accepted.
- Search candidates are ranked for university/admissions signals and penalized for government/legal domains.
- Official-domain research now runs more targeted searches for programme requirements, entrance exams, English tests, SAT/ACT/IB/A-level routes, PDFs, deadlines and scholarships.
- Irrelevant news/legal pages are filtered out before extraction.

### Exam-score safety
- SAT values must now be valid current-scale increments (multiples of 10, 200–1600). Values such as 793 or 0778 are rejected.
- IELTS, TOEFL, ACT, PTE, Duolingo, Cambridge, YDS/YÖKDİL and IB have exam-specific validation.
- URLs, article IDs, years and unrelated numeric identifiers are removed before score extraction.
- A number is only surfaced when it appears close to the exam name in admissions/score context.
- Raw extracted snippets are no longer shown in grey under score cards.

### Cleaner learner UI
Technical API/configuration captions were removed from the learner-facing University Planner.

## Dependencies

```text
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
deep-translator>=1.11.4
openai>=2.0.0
```

No admissions engine can guarantee access to every protected/login-only site. When an exact requirement cannot be verified, the planner should leave it unverified and offer official admissions contacts rather than inventing a value.

