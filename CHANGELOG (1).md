# Changelog — v1.0

## Global research
- Added Jina Search fallback for worldwide official-site discovery.
- Added Jina Reader fallback for sites that block direct server requests or rely on browser rendering.
- Added same-domain official admissions searches for requirements, exams, scholarships, deadlines and documents.
- Expanded exam extraction to IELTS, TOEFL, SAT, ACT, PTE, Duolingo, Cambridge, YDS, YÖKDİL and IB.
- Kept source URLs attached to extracted facts.
- Missing scores are shown as unverified rather than invented.

## Languages
- Interface-language choice is now independent from country.
- Language selector is populated from the translation engine's supported languages.
- English/Russian curated text is preserved.
- Other languages use cached automatic translation.
- Country/language names use pycountry localization where available.

## Reliability
- Research pipeline is now: curated record → official URL → Wikidata → global search → direct fetch → Reader fallback.
- Generic technical tracebacks stay hidden from learners.

