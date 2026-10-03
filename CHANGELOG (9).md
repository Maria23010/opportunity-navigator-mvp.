# Changelog — v1.6

## University discovery
- Added two University Planner modes: **I know the university** and **Help me find a university**.
- Added dynamic university recommendation by country, field, interests, teaching language, financial-aid need and entry year.
- Recommendations are a research shortlist rather than a prestige ranking.
- Added direct handoff from a recommended programme into the admissions plan.

## Bachelor's programme catalog
- Added dynamic discovery of current undergraduate/Bachelor's programmes from official university sources.
- Added programme selector with official programme links and metadata when available.
- Added a fallback programme search for deployments without OpenAI web research.

## Admissions requirement model
- Rebuilt the data model around **mandatory conditions** and **accepted ways to satisfy them**.
- Added requirement groups with selection rules:
  - all required;
  - one or more accepted options (minimum one);
  - choose one route;
  - optional any number;
  - informational.
- English proficiency is now represented as a mandatory condition with alternative accepted tests rather than every test appearing mandatory.
- Entry qualifications are represented as alternative routes where the university publishes them that way.
- The UI explicitly explains that a learner may take multiple alternative exams by choice while only the published minimum number is required.

## GPA / academic record
- Removed any assumption that every university has a universal required numeric GPA.
- School completion/transcript requirements are separated from a published GPA cutoff.
- Numeric GPA is shown only when supported by an official source for the selected applicant category.

## Research quality
- OpenAI web search is now forced for deep-research calls instead of being optional.
- Deep research is instructed to search official webpages, tables and PDFs and to preserve route logic.
- Added a second focused research pass when English, entry-route or academic structure is missing.
- Added official-domain validation for requirement-group source URLs.

## UX
- Removed the old generic “take one English test and one entry route” summary box.
- Replaced it with requirement-by-requirement explanations that state exactly what is mandatory and how many alternatives are needed.
- Optional profile-strengthening remains clearly separated from official admission requirements.
- The selected interface language continues to control the entire learner-facing block.
