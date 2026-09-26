# Changelog — v1.1

## University Planner
- Removed the learner-facing “official links remain evidence” product-explanation sentence.
- Added official admissions-contact extraction from official university-domain pages.
- Added email ranking with preference for admissions / international / registrar addresses.
- Added public official phone extraction.
- Added official Contact / Admissions / International Office page discovery.
- Added contact-only fallback when admissions pages cannot be fully read.
- Added a ready-to-send English admissions question.
- Added a translated version of the question for the learner's selected interface language.
- When exact scores are not verified, the UI now directs the learner to official contacts instead of ending with a dead-end warning.

## Safety / data quality
- Contact details are surfaced only from official-domain pages or official-domain search results.
- The planner does not invent missing scores, emails or phone numbers.
