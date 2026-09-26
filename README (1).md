# Opportunity Navigator — MVP v0.3

A research-driven social mobility platform prototype for adolescents with limited access to educational guidance.

## Product shift after testing
The first MVP behaved too much like an aggregator: it ranked external websites. v0.3 changes the core product so that the learner can study, practise, build a pathway, read motivation stories, request human support and use a moderated community **inside the platform**. External links are now secondary and mainly used when an application or provider action must happen elsewhere.

## Included in v0.3
- searchable ISO country list;
- broad searchable ISO language list;
- personal learner/access profile;
- explainable personalized pathway;
- in-platform Tutor workflow prototype;
- in-platform learning lessons and practice;
- expanded sourced motivation stories with turning points and actions;
- human-support request workflow;
- moderated community workflow with no private DMs;
- opportunity cards with internal checklists and saved items;
- site-style navigation and visual redesign.

## Technical honesty
The current tutor is a deterministic interface prototype, not a live generative AI model. Mentor matching and community moderation are simulated. Recommendation logic remains an explainable baseline. The next phase should validate user value and safety before adding a more complex ML recommender or generative model.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
