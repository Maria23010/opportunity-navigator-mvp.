# Opportunity Navigator — MVP

## Why include motivation?
Because the differentiator is not only finding a resource. The pattern is:
**specific barrier → real story → one concrete next action.**

## Why no live peer chat in MVP?
The users are minors. Open chat adds safeguarding risks (bullying, grooming, sharing personal data, self-harm content, moderation load).
A future community should be moderated and pseudonymous.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 20-second admissions demo
1. Build profile: age 15, Russia, Russian, Math, Free only.
2. Open Recommendations.
3. Show top result + “Why this matches”.
4. Open Motivation → Action.
5. Say: “Version 1 is intentionally simple and explainable. I want to test whether personalization reduces the time it takes a student to find a useful next step before moving to a more complex model.”

## MVP hypothesis
Can personalization reduce the effort required for a teenager with limited resources to find a useful next step?

## Technical honesty
This version is a rule-based recommender, not machine learning.
That is deliberate: it creates an auditable baseline for later comparison with embeddings or other ranking models.
