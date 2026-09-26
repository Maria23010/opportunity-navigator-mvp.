import streamlit as st
import pandas as pd
import pycountry
from pathlib import Path
from datetime import datetime
import random

BASE = Path(__file__).parent

st.set_page_config(
    page_title="Opportunity Navigator",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual system ----------
st.markdown(
    """
    <style>
    :root {
      --ink:#172033;
      --muted:#697386;
      --brand:#6C63FF;
      --brand2:#4F46E5;
      --aqua:#24B6A8;
      --warm:#FFB35C;
      --surface:#FFFFFF;
      --line:#E7EAF1;
      --soft:#F5F7FB;
    }
    [data-testid="stAppViewContainer"] {background: linear-gradient(180deg,#F8FAFF 0%,#F5F7FB 100%);}
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    [data-testid="stSidebar"] {background: linear-gradient(180deg,#10172A 0%,#18213A 100%);}
    [data-testid="stSidebar"] * {color:#F7F8FC;}
    [data-testid="stSidebar"] .stRadio label {padding: 0.36rem 0.5rem; border-radius: 10px;}
    .block-container {padding-top: 1.8rem; padding-bottom: 4rem; max-width: 1240px;}
    h1,h2,h3 {color:var(--ink); letter-spacing:-0.02em;}
    p, li {color:#3F4A5F;}
    .hero {
      padding: 2.2rem 2.2rem 2rem 2.2rem;
      border-radius: 26px;
      background: radial-gradient(circle at 90% 10%, rgba(255,255,255,.24), transparent 26%),
                  linear-gradient(120deg,#5B54E8 0%,#6C63FF 48%,#24B6A8 130%);
      color:white;
      box-shadow: 0 18px 50px rgba(66,63,160,.18);
      margin-bottom: 1.25rem;
    }
    .hero h1 {color:white; font-size:3rem; margin:0 0 .5rem 0;}
    .hero p {color:rgba(255,255,255,.92); font-size:1.13rem; max-width:760px;}
    .eyebrow {font-size:.77rem; text-transform:uppercase; letter-spacing:.12em; font-weight:800; color:#8A92A5;}
    .card {
      background:white; border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.2rem;
      box-shadow: 0 7px 22px rgba(31,45,74,.05); height:100%;
    }
    .card h3 {font-size:1.08rem; margin:.25rem 0 .35rem 0;}
    .card p {font-size:.93rem; margin:.25rem 0;}
    .mini {
      display:inline-block; padding:.25rem .55rem; border-radius:999px; background:#F0F1FF;
      color:#5148D8; font-size:.75rem; font-weight:700; margin-right:.25rem;
    }
    .step {
      background:white; border:1px solid var(--line); border-left:5px solid var(--brand);
      border-radius:16px; padding:1rem 1.15rem; margin:.65rem 0;
    }
    .story {
      background:linear-gradient(180deg,#FFFDF9,#FFFFFF); border:1px solid #F0E8DC;
      border-radius:20px; padding:1.3rem 1.4rem;
    }
    .notice {background:#F0FBF8; border:1px solid #CFEFE8; border-radius:14px; padding:.8rem 1rem;}
    .prototype {background:#FFF7E8; border:1px solid #F6DDAF; border-radius:14px; padding:.8rem 1rem;}
    .site-title {font-size:1.15rem; font-weight:800; color:white; margin:.45rem 0 0 0;}
    .site-sub {font-size:.78rem; color:#B8C0D8 !important; margin-bottom:1rem;}
    .stButton>button {border-radius:12px; font-weight:700; border:0;}
    .stButton>button[kind="primary"] {background:linear-gradient(90deg,#655DEB,#4F46E5);}
    .stTextInput input,.stSelectbox div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div {border-radius:12px;}
    div[data-testid="stMetric"] {background:white;border:1px solid var(--line);padding:.8rem;border-radius:14px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Data ----------
def read_csv(name):
    path = BASE / name
    if path.exists():
        return pd.read_csv(path).fillna("")
    return pd.DataFrame()

STORIES = read_csv("stories.csv")
LESSONS = read_csv("learning_modules.csv")
OPPS = read_csv("opportunities.csv")

# All ISO countries and a broad ISO language list. Search works by typing inside Streamlit selectboxes.
COUNTRIES = ["Global / not specified"] + sorted({c.name for c in pycountry.countries})
COMMON_LANGS = [
    "English", "Russian", "Arabic", "Chinese", "Spanish", "French", "German", "Turkish",
    "Hindi", "Portuguese", "Korean", "Japanese", "Italian", "Kazakh", "Uzbek", "Ukrainian"
]
ALL_LANGUAGE_NAMES = sorted({
    getattr(lang, "name", "") for lang in pycountry.languages if getattr(lang, "name", "")
})
LANGUAGES = COMMON_LANGS + [x for x in ALL_LANGUAGE_NAMES if x not in COMMON_LANGS]

GOALS = [
    "Improve school grades", "Understand mathematics", "Learn English", "Learn coding",
    "Prepare for SAT / international exams", "Prepare for university applications",
    "Find scholarships and opportunities", "Build confidence and study habits"
]
BARRIERS = [
    "Financial limits", "Low confidence", "Lack of guidance", "School disengagement",
    "Bullying / uncomfortable school environment", "Language barrier", "Limited internet / device access"
]

# ---------- Session state ----------
def init_state():
    defaults = {
        "page": "Home",
        "profile": None,
        "completed_lessons": set(),
        "saved_opps": set(),
        "support_requests": [],
        "community_queue": [],
        "community_posts": [
            {"name":"Nova15", "tag":"Math", "text":"I used to freeze when I saw functions. Drawing the graph first made the formula less scary.", "status":"Verified peer tip"},
            {"name":"Orbit16", "tag":"Study skills", "text":"I study in 20-minute blocks because long sessions made me give up. Short sessions finally became a habit.", "status":"Verified peer tip"},
            {"name":"Mira14", "tag":"English", "text":"Reading one short article aloud each day helped me stop being afraid of making pronunciation mistakes.", "status":"Verified peer tip"},
        ],
        "last_tutor_output": None,
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

# ---------- Helpers ----------
def nav_to(page):
    st.session_state.page = page


def first_goal(profile):
    if profile and profile.get("goals"):
        return profile["goals"][0]
    return "Improve school grades"


def goal_to_subject(goal):
    g = goal.lower()
    if "math" in g or "sat" in g: return "Math"
    if "english" in g: return "English"
    if "coding" in g: return "Coding"
    if "university" in g or "scholar" in g: return "Applications"
    return "Study skills"


def barrier_key(profile):
    if not profile or not profile.get("barriers"):
        return "lack of guidance"
    b = profile["barriers"][0].lower()
    if "financial" in b: return "financial limits"
    if "confidence" in b: return "low confidence"
    if "school" in b or "bullying" in b: return "school disengagement"
    return "lack of guidance"


def tutor_content(subject, topic, mode):
    topic = topic.strip() or {
        "Math":"linear equations", "English":"articles", "Coding":"loops", "Study skills":"focus"
    }.get(subject, "planning")
    t = topic.lower()

    if subject == "Math":
        if "linear" in t or "equation" in t:
            lesson = (
                "A linear equation is like a balance: whatever you do to one side, do to the other. "
                "Example: 2x + 5 = 17. First subtract 5 from both sides → 2x = 12. Then divide by 2 → x = 6."
            )
            q, a = "Try: 3x + 4 = 19. What is x?", "5"
        elif "percent" in t:
            lesson = "Percent means ‘out of 100’. To find 20% of 60, convert 20% to 0.20 and multiply: 0.20 × 60 = 12."
            q, a = "What is 15% of 80?", "12"
        else:
            lesson = "Start by naming what you know, what you need to find, and one rule that connects them. Then solve one small step at a time."
            q, a = "Write the first step you would take for your current problem.", ""
    elif subject == "English":
        if "article" in t or "a/an/the" in t:
            lesson = "Use ‘a/an’ when you mention one non-specific thing for the first time. Use ‘the’ when the listener knows which specific thing you mean."
            q, a = "Choose: I saw ___ dog. ___ dog was sleeping. (a/the)", "a, the"
        else:
            lesson = "A useful language habit is retrieval: read a short phrase, hide it, then say it from memory. This is stronger than rereading it many times."
            q, a = "Write one sentence using the new word you are learning.", ""
    elif subject == "Coding":
        if "loop" in t:
            lesson = "A loop repeats an instruction. In Python, `for i in range(3):` runs the indented code three times, with i taking the values 0, 1, and 2."
            q, a = "How many times does `for i in range(5)` repeat?", "5"
        else:
            lesson = "Break code into input → process → output. Before writing syntax, describe those three pieces in plain language."
            q, a = "For a calculator, what is one input and one output?", ""
    else:
        lesson = "Make the next step small enough to start. A 15-minute task with a clear finish line is usually better than a vague plan to ‘study more’."
        q, a = "What is one task you can finish in 15 minutes?", ""

    if mode == "Explain it simply":
        return f"### Simple explanation\n{lesson}\n\n**Check yourself:** {q}"
    if mode == "Give me a hint":
        return f"### Hint\nDon’t solve everything at once. Identify the first move.\n\n{lesson.split('.')[0]}."
    if mode == "Quiz me":
        return f"### Quick quiz\n{q}\n\n*Try answering before opening the explanation below.*\n\n<details><summary>Show explanation</summary><p>{lesson}</p></details>"
    return f"### 20-minute study plan\n1. **3 min:** recall what you already know about {topic}.\n2. **7 min:** read this: {lesson}\n3. **7 min:** answer: {q}\n4. **3 min:** write one thing you can now explain without notes."


def pathway(profile):
    goal = first_goal(profile)
    subject = goal_to_subject(goal)
    barrier = barrier_key(profile)
    story = STORIES[STORIES["barrier"].str.lower() == barrier].head(1)
    story_person = story.iloc[0]["person"] if not story.empty else "a relevant role model"
    steps = [
        ("AI Tutor", f"Do one 15-minute {subject.lower()} session inside the platform.", "AI Tutor"),
        ("Learning Hub", f"Complete one short {subject.lower()} lesson and mark it done.", "Learning Hub"),
        ("Motivation", f"Read the story of {story_person} and choose one action for today.", "Motivation"),
    ]
    if profile and "Lack of guidance" in profile.get("barriers", []):
        steps.append(("Human Support", "Create a request for an academic mentor; no private adult-child chat is used in the MVP.", "Human Support"))
    return steps

# ---------- Sidebar site navigation ----------
st.sidebar.markdown("<div class='site-title'>🧭 Opportunity Navigator</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='site-sub'>One place to learn, plan, connect and move forward.</div>", unsafe_allow_html=True)
NAV = ["Home","My Pathway","AI Tutor","Learning Hub","Motivation","Human Support","Community","Opportunities","Profile","About the Project"]
icons = {"Home":"🏠","My Pathway":"🧭","AI Tutor":"🤖","Learning Hub":"📚","Motivation":"🌱","Human Support":"🤝","Community":"💬","Opportunities":"🎓","Profile":"👤","About the Project":"ℹ️"}
current_index = NAV.index(st.session_state.page) if st.session_state.page in NAV else 0
selected = st.sidebar.radio("Navigate", NAV, index=current_index, format_func=lambda x: f"{icons[x]}  {x}", label_visibility="collapsed")
st.session_state.page = selected
st.sidebar.markdown("---")
if st.session_state.profile:
    p = st.session_state.profile
    st.sidebar.caption(f"Profile: age {p['age']} · {p['country']} · {p['language']}")
else:
    st.sidebar.caption("Create a profile to personalize the platform.")

page = st.session_state.page

# ---------- HOME ----------
if page == "Home":
    st.markdown(
        """
        <div class="hero">
          <div style="font-weight:800; opacity:.9; letter-spacing:.08em; text-transform:uppercase; font-size:.78rem;">Research-driven social mobility platform</div>
          <h1>Your next step should not depend on knowing where to look.</h1>
          <p>Opportunity Navigator combines learning, tutoring, motivation, safe human support, community and opportunity discovery in one place — so a teenager does not have to assemble a support system alone.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("<div class='card'><div class='eyebrow'>Learn</div><h3>AI Tutor + Learning Hub</h3><p>Get an explanation, practise a concept and continue learning without leaving the platform.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'><div class='eyebrow'>Navigate</div><h3>Personal pathway</h3><p>Turn goals, barriers, language and access constraints into a small set of useful next actions.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='card'><div class='eyebrow'>Connect safely</div><h3>Human support + community</h3><p>Ask for a verified mentor or join moderated topic spaces without open child-to-child DMs.</p></div>", unsafe_allow_html=True)
    st.write("")
    a,b = st.columns([1,1])
    with a:
        if st.button("Build my profile", type="primary", use_container_width=True):
            nav_to("Profile"); st.rerun()
    with b:
        if st.button("Explore the learning hub", use_container_width=True):
            nav_to("Learning Hub"); st.rerun()
    st.markdown("### One platform, not another directory")
    st.write("The first MVP mainly recommended outside resources. This version deliberately changes the product: external links become a secondary layer, while the core experience — learning, pathway planning, motivation, safe support and community — happens inside Opportunity Navigator.")

# ---------- PROFILE ----------
elif page == "Profile":
    st.markdown("## Build your learner & access profile")
    st.caption("Country and language fields are searchable. Start typing to jump to a value.")
    old = st.session_state.profile or {}
    with st.form("profile_form"):
        c1,c2 = st.columns(2)
        with c1:
            age = st.slider("Age", 12, 19, int(old.get("age",15)))
            country_default = old.get("country", "Global / not specified")
            country = st.selectbox("Country / region", COUNTRIES, index=COUNTRIES.index(country_default) if country_default in COUNTRIES else 0)
            lang_default = old.get("language", "English")
            language = st.selectbox("Preferred language", LANGUAGES, index=LANGUAGES.index(lang_default) if lang_default in LANGUAGES else 0)
            other_langs = st.multiselect("Other languages you can use", LANGUAGES, default=old.get("other_languages",[]))
        with c2:
            goals = st.multiselect("What do you want to work on?", GOALS, default=old.get("goals", ["Understand mathematics"]))
            barriers = st.multiselect("What makes progress harder right now?", BARRIERS, default=old.get("barriers", ["Lack of guidance"]))
            support = st.selectbox("Preferred support", ["Mostly self-study", "Mostly human support", "A mix of both"], index=2)
            access = st.multiselect("Access needs", ["Free only", "Low-bandwidth friendly", "Works on a phone", "Downloadable/offline material"], default=old.get("access", ["Free only"]))
        current_need = st.text_input("What do you need help with today?", value=old.get("current_need", ""), placeholder="Example: I do not understand linear equations and I do not know where to start.")
        submitted = st.form_submit_button("Save profile and build my pathway", type="primary", use_container_width=True)
    if submitted:
        st.session_state.profile = {
            "age":age,"country":country,"language":language,"other_languages":other_langs,
            "goals":goals or ["Improve school grades"],"barriers":barriers or ["Lack of guidance"],
            "support":support,"access":access,"current_need":current_need,
        }
        st.success("Profile saved. Your pathway has been rebuilt.")
        if st.button("Open my pathway"):
            nav_to("My Pathway"); st.rerun()

# ---------- PATHWAY ----------
elif page == "My Pathway":
    st.markdown("## My pathway")
    p = st.session_state.profile
    if not p:
        st.info("Create your profile first so the pathway can use your goals, language and access constraints.")
        if st.button("Create profile", type="primary"):
            nav_to("Profile"); st.rerun()
    else:
        st.markdown(f"<div class='notice'><b>Today:</b> focus on one useful next step, not a long list. Your main goal is <b>{first_goal(p)}</b>.</div>", unsafe_allow_html=True)
        st.write("")
        completed = len(st.session_state.completed_lessons)
        m1,m2,m3 = st.columns(3)
        m1.metric("Learning modules completed", completed)
        m2.metric("Saved opportunities", len(st.session_state.saved_opps))
        m3.metric("Support requests", len(st.session_state.support_requests))
        st.markdown("### Today’s path")
        for i,(label,desc,target) in enumerate(pathway(p),1):
            st.markdown(f"<div class='step'><b>{i}. {label}</b><br>{desc}</div>", unsafe_allow_html=True)
            if st.button(f"Go to {label}", key=f"goto_{i}"):
                nav_to(target); st.rerun()
        st.markdown("### Why these steps?")
        st.write("The pathway uses your selected goal, barriers and support preference. The product intentionally starts with an explainable baseline; user testing should determine where more complex recommendation models add value.")

# ---------- AI TUTOR ----------
elif page == "AI Tutor":
    st.markdown("## AI Tutor — learning interface prototype")
    st.markdown("<div class='prototype'><b>Technical honesty:</b> this portfolio version demonstrates the tutoring workflow with deterministic lesson logic. It is not yet connected to a generative model. The next technical phase is to connect a safeguarded LLM and evaluate answer quality, hallucinations and age-appropriate explanations.</div>", unsafe_allow_html=True)
    st.write("")
    c1,c2,c3 = st.columns([1,1.4,1])
    with c1:
        subject = st.selectbox("Subject", ["Math","English","Coding","Study skills"])
    with c2:
        topic = st.text_input("Topic", placeholder="Example: linear equations")
    with c3:
        mode = st.selectbox("How should the tutor help?", ["Explain it simply","Give me a hint","Quiz me","Make a study plan"])
    if st.button("Start tutoring session", type="primary"):
        st.session_state.last_tutor_output = tutor_content(subject, topic, mode)
    if st.session_state.last_tutor_output:
        with st.container(border=True):
            st.markdown(st.session_state.last_tutor_output, unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        c1.button("👍 This helped", use_container_width=True)
        c2.button("🔁 Explain differently", use_container_width=True)
        c3.button("🧩 Give me another practice task", use_container_width=True)
    st.caption("Design goal: the future model should teach by hints and checks, not simply output final answers.")

# ---------- LEARNING HUB ----------
elif page == "Learning Hub":
    st.markdown("## Learning Hub")
    st.write("Short lessons and practice live inside the platform. External websites are optional references, not the core experience.")
    subjects = ["All"] + sorted(LESSONS["subject"].unique().tolist()) if not LESSONS.empty else ["All"]
    chosen = st.selectbox("Filter by subject", subjects)
    data = LESSONS if chosen == "All" else LESSONS[LESSONS["subject"] == chosen]
    for _,row in data.iterrows():
        key = str(row["id"])
        done = key in st.session_state.completed_lessons
        with st.expander(("✅ " if done else "") + f"{row['title']} · {row['duration']} min"):
            st.markdown(f"<span class='mini'>{row['subject']}</span><span class='mini'>{row['level']}</span>", unsafe_allow_html=True)
            st.write(row["lesson"])
            st.markdown(f"**Practice:** {row['question']}")
            ans = st.text_input("Your answer", key=f"lesson_ans_{key}")
            if st.button("Check / reflect", key=f"check_{key}"):
                expected = str(row["answer"]).strip().lower()
                if expected and ans.strip().lower() == expected:
                    st.success("Correct. Nice work.")
                elif expected:
                    st.info(f"A useful answer is: {row['answer']}. Read the explanation once, then try again without looking.")
                else:
                    st.success("Good. The important part is that you produced an answer instead of only rereading.")
            if st.button("Mark lesson complete", key=f"done_{key}"):
                st.session_state.completed_lessons.add(key); st.rerun()

# ---------- MOTIVATION ----------
elif page == "Motivation":
    st.markdown("## Motivation → evidence → action")
    st.write("The purpose is not celebrity worship. A story should match a barrier, show a real turning point, and end with something the learner can do now.")
    p = st.session_state.profile
    default_barrier = barrier_key(p)
    barriers = STORIES["barrier"].unique().tolist() if not STORIES.empty else []
    idx = barriers.index(default_barrier) if default_barrier in barriers else 0
    chosen_barrier = st.selectbox("What kind of barrier should the story speak to?", barriers, index=idx if barriers else 0)
    matches = STORIES[STORIES["barrier"] == chosen_barrier] if not STORIES.empty else pd.DataFrame()
    for _,x in matches.iterrows():
        st.markdown("<div class='story'>", unsafe_allow_html=True)
        st.markdown(f"### {x['person']} — {x['title']}")
        st.write(x["story"])
        if "turning_point" in x and x["turning_point"]:
            st.markdown(f"**Turning point:** {x['turning_point']}")
        st.markdown(f"**Why this may matter to you:** {x['match_reason']}")
        st.success(f"**Try this now:** {x['action']}")
        if x.get("source_url", ""):
            st.markdown(f"[Source: {x['source_name']}]({x['source_url']})")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- HUMAN SUPPORT ----------
elif page == "Human Support":
    st.markdown("## Human Support")
    st.write("AI can help navigate; it should not replace a qualified teacher, mentor or mental-health professional.")
    p = st.session_state.profile or {}
    with st.form("support_form"):
        need = st.selectbox("What kind of human help do you need?", ["Academic mentor","Subject tutor","University / opportunity guidance","Wellbeing support"])
        language = st.selectbox("Preferred language for support", LANGUAGES, index=LANGUAGES.index(p.get("language","English")) if p.get("language","English") in LANGUAGES else 0)
        message = st.text_area("What would you like the mentor or professional to know?", placeholder="Example: I understand the basics, but I do not know how to plan what to study each week.")
        agree = st.checkbox("I understand this demo does not create a live private chat with an adult.")
        send = st.form_submit_button("Create safe support request", type="primary")
    if send:
        if not agree:
            st.warning("Please confirm the safety note first.")
        else:
            rid = f"SUP-{random.randint(1000,9999)}"
            st.session_state.support_requests.append({"id":rid,"need":need,"language":language,"message":message,"time":datetime.now().isoformat(timespec='minutes')})
            st.success(f"Request {rid} created in the prototype.")
            st.markdown("**What would happen in production:** identity/eligibility checks → matching with a vetted partner → scheduled, logged session → reporting and safeguarding controls.")
            if need == "Wellbeing support":
                st.warning("This platform would not diagnose a condition. If someone is in immediate danger, the safe route is a trusted adult and local emergency/professional services.")
    if st.session_state.support_requests:
        st.markdown("### My requests")
        for r in reversed(st.session_state.support_requests[-3:]):
            st.markdown(f"- **{r['id']}** · {r['need']} · {r['language']} · status: *demo request created*")

# ---------- COMMUNITY ----------
elif page == "Community":
    st.markdown("## Community — moderated, not open DMs")
    st.write("The community is designed around topic rooms, pseudonyms and moderation. Child-to-child private messaging and adult-to-child private messaging are not part of the MVP.")
    tags = ["Math","English","Coding","Study skills","Applications","Motivation"]
    chosen_tag = st.selectbox("Topic room", ["All"] + tags)
    posts = st.session_state.community_posts
    for post in posts:
        if chosen_tag != "All" and post["tag"] != chosen_tag:
            continue
        with st.container(border=True):
            st.markdown(f"**{post['name']}** · `{post['tag']}`")
            st.write(post["text"])
            st.caption(post["status"])
    st.markdown("### Ask the community")
    with st.form("community_form"):
        tag = st.selectbox("Topic", tags, key="newpost_tag")
        text = st.text_area("Your question", placeholder="Do not include your real name, phone number, address, school name or social-media handle.")
        submit = st.form_submit_button("Send to moderation")
    if submit:
        if len(text.strip()) < 8:
            st.warning("Write a little more so a moderator can understand the question.")
        else:
            st.session_state.community_queue.append({"tag":tag,"text":text,"status":"Pending human moderation"})
            st.success("Your question is in the moderation queue. It is not public yet.")
    if st.session_state.community_queue:
        st.markdown("### My pending posts")
        for q in reversed(st.session_state.community_queue[-3:]):
            st.markdown(f"- `{q['tag']}` {q['text']} — **{q['status']}**")

# ---------- OPPORTUNITIES ----------
elif page == "Opportunities":
    st.markdown("## Opportunities")
    st.write("Instead of a list of links, each opportunity includes eligibility, why it may fit, a checklist and a save action. The official page is secondary because applications eventually happen with the provider.")
    p = st.session_state.profile or {}
    categories = ["All"] + sorted(OPPS["category"].unique().tolist()) if not OPPS.empty else ["All"]
    cat = st.selectbox("Category", categories)
    data = OPPS if cat == "All" else OPPS[OPPS["category"] == cat]
    for _,row in data.iterrows():
        oid = str(row["id"])
        with st.container(border=True):
            st.markdown(f"### {row['title']}")
            st.markdown(f"<span class='mini'>{row['category']}</span><span class='mini'>{row['cost']}</span><span class='mini'>{row['region']}</span>", unsafe_allow_html=True)
            st.write(row["summary"])
            st.markdown(f"**Eligibility:** {row['eligibility']}")
            st.markdown(f"**Inside-platform checklist:** {row['checklist']}")
            c1,c2 = st.columns([1,1])
            with c1:
                label = "Saved ✓" if oid in st.session_state.saved_opps else "Save opportunity"
                if st.button(label, key=f"save_{oid}", disabled=oid in st.session_state.saved_opps, use_container_width=True):
                    st.session_state.saved_opps.add(oid); st.rerun()
            with c2:
                if row.get("url", ""):
                    st.link_button("Official provider page", row["url"], use_container_width=True)

# ---------- ABOUT ----------
elif page == "About the Project":
    st.markdown("## About the project")
    st.markdown("### What changed after testing")
    st.markdown("""
1. **MVP 0.1 behaved too much like an aggregator.** It ranked other websites but did not deliver the core support itself.
2. **A broken resource link** showed that external-resource dependency creates reliability problems.
3. **The motivation module was too shallow.** A name and one sentence did not create identification or action.
4. **Human Support was only a promise.** The new version demonstrates an internal request workflow.
5. **The interface looked like a technical demo, not a youth-facing product.** v0.3 uses a site-style dashboard and clear product areas.
6. **Country/language options were artificially limited.** v0.3 uses searchable ISO lists.
""")
    st.markdown("### Product principle")
    st.markdown("<div class='notice'><b>Do not make a teenager assemble the solution alone.</b> Learning, tutoring, motivation, support, community and opportunity navigation should work as one pathway.</div>", unsafe_allow_html=True)
    st.markdown("### What is implemented vs. what is still a prototype")
    st.markdown("""
**Implemented in the portfolio prototype**
- profile with global country/language selection;
- personalized pathway logic;
- in-platform learning modules and practice;
- tutor interaction workflow;
- richer barrier-matched motivation stories;
- safe human-support request flow;
- moderated-community workflow;
- opportunity cards, checklists and saved items.

**Not yet production AI**
- the tutor is a deterministic interface prototype, not a live generative model;
- mentor matching is simulated, not connected to a real partner network;
- community moderation is demonstrated in-session, not backed by a production database;
- recommendations are explainable rules, not a trained ML recommender.

**Next validation before more ML**
1. test with target users;
2. measure time-to-useful-next-step and completion;
3. refine safety and content with educators / safeguarding experts;
4. collect interaction data with consent;
5. only then compare the explainable baseline with more complex recommendation methods.
""")
