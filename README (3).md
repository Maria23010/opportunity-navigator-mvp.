# Opportunity Navigator — MVP v0.6

A research-driven Streamlit prototype for adolescents who may have limited access to tutoring, guidance, admissions information, or opportunity networks.

The product is designed as **one pathway**, not a directory of external links. It combines:

- a learner profile with global country and language selection;
- a personalized pathway and persistent progress counters;
- an in-platform AI Tutor workflow with subject/topic selection and follow-up questions;
- adaptive Learning Hub practice that adds questions after mistakes;
- barrier-matched motivation stories with saveable next actions;
- a safe human-support request workflow;
- a moderated community concept with contact-detail blocking;
- personalized opportunity cards with direct official links;
- a University Planner for admissions research, exam/score tracking, motivation-letter drafting, and portfolio evidence.

## What v0.6 fixes after testing

1. **Tutor topic choice and follow-up questions**
   - Subject and topic are selected explicitly.
   - The learner can ask repeated follow-up questions without restarting the session.
   - Simpler explanation, hint and another-example controls stay available.

2. **Adaptive practice instead of a fixed four-question lesson**
   - Lessons start with three core questions.
   - One mistake adds extra practice.
   - Repeated mistakes add more remedial questions, up to the available question bank.
   - Wrong answers always show an explanation.
   - Lesson completion is tracked.

3. **Community contact-detail blocking**
   - Email addresses, phone numbers and common social handles are blocked before submission.

4. **Opportunity links and counters**
   - Official provider pages use direct link buttons.
   - Saved opportunities update the pathway counter.

5. **Refresh persistence**
   - A compressed state token in the URL preserves non-sensitive profile choices, current page, lesson progress, saved opportunities, support-request count, saved actions, admissions target, requirement checklist and exam tracker.
   - Export/import remains available in the sidebar.
   - Free-text support/community/essay content is intentionally not stored in the URL token.

6. **University Planner expanded**
   - A learner can specify a target country, university and/or program.
   - The app can search the public web for candidate official admissions, exam-score, scholarship and essay pages.
   - An official page URL can be opened and scanned for requirement mentions.
   - Verified exam/score requirements can be recorded with a source URL.
   - Motivation-letter drafting now uses motivation → evidence → reflection → fit.
   - Portfolio evidence is organized around role, result and proof rather than a fixed number of achievements.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

Use `app.py` as the main file and install from `requirements.txt`.

## Important prototype limitations

This version is deliberately honest about what is and is not production-ready:

- the AI Tutor uses deterministic teaching logic, not a live generative model;
- mentor matching is simulated;
- community moderation is a prototype flow rather than a production moderation system;
- university web search/page extraction is a research aid and every requirement must be verified on an official source;
- authenticated accounts and a production database are not implemented.

