# Changelog — v1.2

## Language / interface
- Fixed invisible selected-language text in the sidebar select box.
- Added a visible “Selected language” badge.
- Routed many previously English-only Streamlit labels through the multilingual translation layer.
- Added MyMemory as a translation fallback.
- Added optional OpenAI translation fallback when an API key is configured.
- Updated Motivation and Community content so non-Russian interface languages can also translate learner-facing text.

## University Planner
- Added optional deep admissions research through OpenAI Responses API web search.
- Deep mode can search official university pages and PDFs for programme-specific admissions information.
- Added structured sections for academic requirements, entrance exams, English tests, deadlines, documents, scholarships and contacts.
- Deep research is instructed to return `null` rather than invent missing numeric scores.
- Each factual admissions item is expected to include an official source URL.
- Deep mode can still discover an official university site if the lightweight discovery layer misses it.
- Existing Jina/direct-reading/contact fallback remains available when deep mode is unavailable.

## UX
- Technical API configuration details are kept out of the core learner flow.
- Selected language is now immediately visible after selection.

