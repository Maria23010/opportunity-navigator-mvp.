# Changelog — v1.5

## University Planner UX
- Rebuilt the admissions-results block around **Required / Choose one / Conditional / Optional / Not required**.
- Added a clear instruction that learners do **not** need to take every exam displayed.
- English exams are shown as accepted alternatives where appropriate.
- Entry qualifications are grouped as alternative routes rather than a flat checklist.
- Financial-aid rules are separated from base admission requirements.
- Optional profile-building suggestions are explicitly marked as not replacing official requirements.
- Removed the blue technical research-information box from the learner-facing screen.
- Removed long, noisy unstructured scraped paragraphs from the no-API fallback.

## Language behavior
- Fixed dynamic admissions content so it is translated into the currently selected interface language.
- English UI can now translate source text that arrives in Cyrillic/Arabic/CJK rather than assuming all dynamic content is already English.

## Research structure
- Extended the deep-research schema with `requirement_class`, `choice_group`, `applies_to` and `score_type`.
- Deep research now explicitly searches for all entry routes and distinguishes mandatory, alternative, conditional and optional requirements.
- Improved official-domain matching for sibling university subdomains such as admissions and school/program subdomains.

## Nazarbayev University
- Added a source-linked undergraduate profile for the 2027 cycle.
- Added IELTS/TOEFL logic, NUET, Digital SAT, ACT, Olympiad, IB, A-level/NIS, GPA and UNT routes.
- Separated fee-paying thresholds from financial-support rules.
- Added the Computer Science programme mapping to Artificial Intelligence and Data Science tracks.

