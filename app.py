import streamlit as st
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
R = pd.read_csv(BASE/"resources.csv")
S = pd.read_csv(BASE/"stories.csv")
st.set_page_config(page_title="Opportunity Navigator", page_icon="🧭", layout="wide")

def toks(x): return {i.strip().lower() for i in str(x).split("|") if i.strip()}

def score(row,p):
    s=0; why=[]
    if row.min_age <= p["age"] <= row.max_age: s+=3; why.append("fits your age")
    else: s-=5
    if p["free"] and row.cost=="Free": s+=3; why.append("free")
    if p["goal"].lower() in toks(row.goals): s+=5; why.append("matches your goal")
    if p["lang"].lower() in toks(row.languages) or "multilingual" in toks(row.languages): s+=3; why.append("language match")
    if "global" in toks(row.regions) or p["country"].lower() in toks(row.regions): s+=3; why.append("available in your region")
    want_h = p["support"]!="AI/self-study"
    want_s = p["support"]!="Human mentor/tutor"
    if want_h and int(row.human_support)==1: s+=4; why.append("includes human support")
    if want_s and int(row.self_study)==1: s+=2; why.append("works for self-study")
    if p["lowbw"] and int(row.low_bandwidth_friendly)==1: s+=2; why.append("bandwidth-friendly")
    return s, why

st.title("🧭 Opportunity Navigator")
st.caption("MVP: personalized next steps for adolescents with limited resources")

tabs=st.tabs(["Profile","Recommendations","Motivation → Action","Human Support","Community Preview","About"])

if "profile" not in st.session_state: st.session_state.profile=None

with tabs[0]:
    st.subheader("Build a learner & access profile")
    c1,c2=st.columns(2)
    with c1:
        age=st.slider("Age",13,17,15)
        country=st.selectbox("Country / region",["Global","Russia","UAE","United States","United Kingdom","Other"])
        lang=st.selectbox("Preferred language",["English","Russian","Multilingual"])
        goal=st.selectbox("Main goal",["math","sat","english","coding","general_learning","college_guidance"])
    with c2:
        support=st.selectbox("Support preference",["AI/self-study","Human mentor/tutor","Both AI/self-study and human support"])
        free=st.checkbox("Free resources only",True)
        lowbw=st.checkbox("Prefer low-bandwidth options",False)
        barrier=st.selectbox("What feels hardest right now?",["financial limits","low confidence","lack of guidance","school disengagement"])
    if st.button("Create my pathway",type="primary"):
        st.session_state.profile=dict(age=age,country=country,lang=lang,goal=goal,support=support,free=free,lowbw=lowbw,barrier=barrier)
        st.success("Profile created.")

with tabs[1]:
    st.subheader("Personalized recommendations")
    p=st.session_state.profile
    if not p: st.info("Create a profile first.")
    else:
        ranked=[]
        for _,row in R.iterrows():
            sc,why=score(row,p); ranked.append((sc,why,row))
        ranked.sort(key=lambda x:x[0],reverse=True)
        for i,(sc,why,row) in enumerate(ranked[:5],1):
            with st.container(border=True):
                st.markdown(f"### {i}. {row['name']}")
                st.write(row["description"])
                st.write("**Why this matches:** "+" · ".join(why))
                st.write("**Next step:** "+row["next_step"])
                st.markdown(f"[Open resource]({row['url']})")
                st.caption(f"Explainable demo score: {sc}")
        st.info("Version 1 deliberately uses a transparent weighted baseline before ML.")

with tabs[2]:
    st.subheader("Motivation → concrete action")
    p=st.session_state.profile
    if not p: st.info("Create a profile first.")
    else:
        x=S[S.barrier==p["barrier"]].iloc[0]
        with st.container(border=True):
            st.markdown(f"### {x['person']}")
            st.write(x["story"])
            st.write("**Why selected:** "+x["match_reason"])
            st.write("**Do one thing now:** "+x["action"])
        st.caption("Production version: every story should be sourced, age-reviewed, and tested for unintended pressure or comparison.")

with tabs[3]:
    st.subheader("Human support, not AI replacement")
    st.write("AI can navigate; it should not diagnose mental-health conditions or replace a qualified professional.")
    need=st.selectbox("Human support needed",["Academic mentor","Subject tutor","College / opportunity guidance","Wellbeing support"])
    if st.button("Show safe handoff"):
        if need=="Wellbeing support":
            st.warning("Demo: route to verified local professional support; urgent danger requires trusted-adult / local emergency escalation.")
        else:
            st.success(f"Demo: request a vetted {need.lower()} through a partner organization.")

with tabs[4]:
    st.subheader("Community Preview")
    st.write("**Live child-to-child chat is intentionally excluded from MVP 0.1.**")
    st.markdown("""
Future safe layer:
- moderated topic rooms;
- pseudonyms;
- read-only peer success posts;
- no public contact details;
- no adult-to-child private messaging;
- reporting, blocking, and human moderation.
""")
    with st.container(border=True):
        st.write("**Example moderated post:** “I keep getting stuck on algebra. What free resource helped you understand functions?”")

with tabs[5]:
    st.subheader("What this prototype tests")
    st.markdown("""
> **Can personalization reduce the effort required for a teenager with limited resources to find a useful next step?**

**Current design**
- Python + Streamlit
- structured CSV data
- transparent weighted recommender
- explanation layer
- barrier-matched motivation module
- human-support handoff
- no live peer chat in MVP

**Next technical steps**
1. collect user feedback;
2. measure time-to-useful-resource;
3. expand and verify the dataset;
4. add learning-state tracking;
5. compare rule-based ranking with an embedding/ML recommender.
""")
