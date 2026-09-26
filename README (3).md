# Opportunity Navigator — v1.1

Opportunity Navigator is a multilingual learning and admissions-navigation prototype.

## v1.1: admissions-contact fallback

The University Planner now follows a more useful rule:

**verified requirement → show it**
**missing requirement → do not invent it → find official admissions contacts → prepare the question**

For non-curated universities the planner can:
- discover and read official university pages;
- extract public admissions/international-office email addresses;
- extract public official phone numbers;
- surface official contact pages;
- prepare a ready-to-send admissions question in English;
- show a translated version in the learner's selected interface language.

Only contact details discovered on the official university domain are surfaced.

## Cleaner learner-facing copy

The conceptual sentence about “official links as evidence” was removed from the main University Planner screen. Sources remain available next to facts without making the learner read product-design explanations.

## Multilingual behavior

Country and interface language remain separate settings. English and Russian have curated UI text; other supported interface languages use cached automatic translation.

## Research limitations

No scraper can guarantee access to every protected, login-only or CAPTCHA-gated website. When a requirement cannot be verified, v1.1 fails safely and tries to surface official admissions contacts instead of guessing.

## Dependencies

```text
pycountry>=24.6.1
requests>=2.32
beautifulsoup4>=4.12
deep-translator>=1.11.4
```

