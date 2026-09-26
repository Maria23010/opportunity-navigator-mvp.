import base64
import ipaddress
import json
import random
import re
import socket
import zlib
from datetime import datetime
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup

try:
    import pycountry
except Exception:
    pycountry = None

# -------------------- App configuration --------------------
st.set_page_config(
    page_title="Opportunity Navigator",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

VERSION = "0.6"

# -------------------- Visual system --------------------
st.markdown(
    """
    <style>
    :root {
        --ink:#172033;
        --muted:#64748b;
        --line:#e5e7eb;
        --surface:#ffffff;
        --soft:#f7f9fc;
        --brand:#2155f3;
        --brand2:#22a6f2;
        --warm:#fff6e8;
        --ok:#edf9f1;
        --danger:#fff0f0;
    }
    .stApp { background: #ffffff; }
    .block-container { max-width: 1180px; padding-top: 2.0rem; padding-bottom: 5rem; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#101827 0%,#1c2944 100%); }
    [data-testid="stSidebar"] * { color: #f8fafc; }
    [data-testid="stSidebar"] .stButton button {
        width:100%; justify-content:flex-start; border:0; border-radius:10px;
        background:transparent; color:#f8fafc; min-height:42px; font-weight:650;
    }
    [data-testid="stSidebar"] .stButton button:hover { background:rgba(255,255,255,.10); border:0; color:#fff; }
    .site-title { font-size:1.30rem; font-weight:800; margin-bottom:.1rem; }
    .site-sub { font-size:.84rem; opacity:.72; margin-bottom:1rem; }
    .hero {
        border-radius:28px; padding:42px 44px;
        background:linear-gradient(115deg,#244be8 0%,#1765ea 55%,#28a9ec 100%);
        color:white; box-shadow:0 18px 55px rgba(32,77,180,.18); margin-bottom:24px;
    }
    .hero .eyebrow { font-weight:800; letter-spacing:.12em; text-transform:uppercase; font-size:.76rem; opacity:.85; margin-bottom:16px; }
    .hero h1 { font-size:3.10rem; line-height:1.03; margin:0 0 20px 0; color:white; }
    .hero p { font-size:1.08rem; line-height:1.65; max-width:900px; opacity:.96; }
    .feature-card, .card { border:1px solid var(--line); border-radius:20px; padding:22px 24px; background:var(--surface); height:100%; }
    .feature-card .label { color:#789; font-weight:800; text-transform:uppercase; letter-spacing:.10em; font-size:.72rem; margin-bottom:10px; }
    .feature-card h3 { margin:.2rem 0 .5rem 0; }
    .muted { color:var(--muted); }
    .notice { border:1px solid #dbeafe; border-radius:14px; background:#eff6ff; padding:14px 16px; margin:12px 0 18px 0; }
    .successbox { border:1px solid #d1fae5; border-radius:14px; background:#ecfdf5; padding:14px 16px; margin:12px 0; }
    .warnbox { border:1px solid #fde68a; border-radius:14px; background:#fffbeb; padding:14px 16px; margin:12px 0; }
    .story { border-left:5px solid #2155f3; border-radius:16px; background:#f8fbff; padding:22px 24px; margin:12px 0; }
    .path-step { border-left:5px solid #2155f3; border-radius:16px; border:1px solid #e5e7eb; border-left-width:5px; padding:18px 20px; margin:12px 0; background:#fff; }
    .pill { display:inline-block; padding:4px 9px; border-radius:999px; background:#edf2ff; color:#244be8; font-size:.78rem; font-weight:700; margin:0 6px 6px 0; }
    .tiny { font-size:.78rem; color:#6b7280; }
    div[data-testid="stMetric"] { border:1px solid #e5e7eb; padding:12px 16px; border-radius:16px; background:white; }
    @media (max-width: 800px) {
        .hero { padding:28px 24px; border-radius:22px; }
        .hero h1 { font-size:2.15rem; }
        .block-container { padding-top:1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Reference data --------------------
COMMON_COUNTRIES = [
    "Kazakhstan", "Russia", "United Arab Emirates", "United States", "United Kingdom",
    "Türkiye", "Uzbekistan", "Kyrgyzstan", "Norway", "Canada", "Singapore", "Netherlands"
]
if pycountry:
    _all_countries = sorted({c.name for c in pycountry.countries})
else:
    _all_countries = COMMON_COUNTRIES[:]
COUNTRIES = ["Global / not specified"] + [x for x in COMMON_COUNTRIES if x in _all_countries]
COUNTRIES += [x for x in _all_countries if x not in COUNTRIES]

COMMON_LANGS = [
    "English", "Russian", "Kazakh", "Turkish", "Arabic", "Chinese", "Spanish", "French",
    "German", "Portuguese", "Korean", "Japanese", "Hindi", "Uzbek", "Ukrainian"
]
if pycountry:
    _names = set()
    for lang in pycountry.languages:
        name = getattr(lang, "name", None)
        if name and 1 < len(name) <= 45:
            _names.add(name)
    ALL_LANGS = sorted(_names)
else:
    ALL_LANGS = COMMON_LANGS[:]
LANGUAGES = COMMON_LANGS + [x for x in ALL_LANGS if x not in COMMON_LANGS]

GOALS = [
    "Improve school grades", "Understand mathematics", "Learn English", "Learn coding",
    "Prepare for SAT / international exams", "Prepare for university applications",
    "Find scholarships and opportunities", "Build confidence and study habits",
]
BARRIERS = [
    "Lack of guidance", "Financial limits", "Low confidence", "I do not know where to start",
    "Limited access to tutoring", "Language barrier", "Limited device / internet access",
    "School stress or bullying",
]
SUPPORT_PREFS = ["Mostly self-study", "Mostly human support", "A mix of both"]
ACCESS_NEEDS = ["Free only", "Works on a phone", "Low-bandwidth friendly", "Downloadable/offline materials"]

SUBJECT_TOPICS = {
    "Math": ["Linear equations", "Percentages", "Functions and graphs", "Fractions", "Geometry", "Other"],
    "English": ["Articles: a / an / the", "Vocabulary", "Writing", "Speaking", "Grammar", "Other"],
    "Coding": ["Loops", "Variables", "Functions", "Debugging", "Python basics", "Other"],
    "Study skills": ["Getting started", "Planning", "Focus", "Revision", "Exam anxiety", "Other"],
    "University applications": ["Choosing universities", "Admission requirements", "Motivation letter", "Portfolio", "Scholarships", "Other"],
}

# -------------------- Learning content --------------------
# Each module has a small starting set and extra remedial questions. Extra practice is added automatically
# if the learner makes mistakes during the first set.
MODULES = {
    "Linear equations without guessing": {
        "subject": "Math", "minutes": 12,
        "intro": "Learn to isolate the unknown by undoing operations in reverse order.",
        "base": [
            {"q":"Solve: x + 7 = 12", "options":["3","5","7","19"], "answer":"5", "explanation":"Subtract 7 from both sides: x = 12 − 7 = 5."},
            {"q":"Solve: 3x = 18", "options":["3","6","15","54"], "answer":"6", "explanation":"Divide both sides by 3: x = 18 ÷ 3 = 6."},
            {"q":"Solve: 2x + 3 = 11", "options":["3","4","5","7"], "answer":"4", "explanation":"Subtract 3 first: 2x = 8. Then divide by 2: x = 4."},
        ],
        "remedial": [
            {"q":"Solve: x − 9 = 4", "options":["5","13","−5","36"], "answer":"13", "explanation":"Add 9 to both sides: x = 4 + 9 = 13."},
            {"q":"Solve: 4x = 28", "options":["6","7","8","24"], "answer":"7", "explanation":"Divide both sides by 4: x = 7."},
            {"q":"Solve: 5x − 10 = 20", "options":["2","4","6","10"], "answer":"6", "explanation":"Add 10: 5x = 30. Divide by 5: x = 6."},
            {"q":"Solve: 3x + 6 = 24", "options":["4","5","6","10"], "answer":"6", "explanation":"Subtract 6: 3x = 18. Divide by 3: x = 6."},
        ],
    },
    "Percentages in real life": {
        "subject":"Math", "minutes":10,
        "intro":"Convert the percentage to a decimal or fraction, then multiply.",
        "base":[
            {"q":"What is 20% of 150?", "options":["15","20","30","75"], "answer":"30", "explanation":"20% = 0.20, so 0.20 × 150 = 30."},
            {"q":"A $40 item is discounted by 25%. What is the discount?", "options":["$5","$10","$15","$30"], "answer":"$10", "explanation":"25% of 40 = 0.25 × 40 = 10."},
            {"q":"A score rises from 60 to 75. By what percentage did it increase?", "options":["15%","20%","25%","30%"], "answer":"25%", "explanation":"Increase = 15. Divide by the original 60: 15/60 = 25%."},
        ],
        "remedial":[
            {"q":"What is 10% of 90?", "options":["9","10","18","80"], "answer":"9", "explanation":"10% = 0.10, and 0.10 × 90 = 9."},
            {"q":"What is 50% of 36?", "options":["12","18","20","72"], "answer":"18", "explanation":"50% means half, so half of 36 is 18."},
            {"q":"30 is what percent of 120?", "options":["20%","25%","30%","40%"], "answer":"25%", "explanation":"30 ÷ 120 = 0.25 = 25%."},
        ],
    },
    "A / an / the in two rules": {
        "subject":"English", "minutes":10,
        "intro":"Use a/an for one non-specific thing; use the when the listener knows which one.",
        "base":[
            {"q":"I saw ___ elephant at the zoo.", "options":["a","an","the","—"], "answer":"an", "explanation":"Use 'an' before a vowel sound: an elephant."},
            {"q":"Please close ___ door. (There is one obvious door.)", "options":["a","an","the","—"], "answer":"the", "explanation":"Use 'the' when both people know which specific door is meant."},
            {"q":"She wants to buy ___ laptop, but she has not chosen one yet.", "options":["a","an","the","—"], "answer":"a", "explanation":"The laptop is not specific yet, so use 'a'."},
        ],
        "remedial":[
            {"q":"He is ___ university student.", "options":["a","an","the","—"], "answer":"a", "explanation":"University begins with a /y/ consonant sound, so use 'a'."},
            {"q":"I bought a book. ___ book is about space.", "options":["A","An","The","—"], "answer":"The", "explanation":"The second mention refers to the specific book already introduced."},
            {"q":"We saw ___ old castle near the river.", "options":["a","an","the","—"], "answer":"an", "explanation":"Use 'an' before a vowel sound: an old castle."},
            {"q":"Can you pass me ___ pencil on your desk?", "options":["a","an","the","—"], "answer":"the", "explanation":"A specific pencil is identified by its location, so use 'the'."},
        ],
    },
    "Loops as repetition": {
        "subject":"Coding", "minutes":12,
        "intro":"A loop repeats a block of instructions while a rule or range tells it how long.",
        "base":[
            {"q":"In Python, how many times does `for i in range(3)` repeat?", "options":["2","3","4","It never stops"], "answer":"3", "explanation":"range(3) produces 0, 1, 2 — three values."},
            {"q":"Which idea best describes a loop?", "options":["Repeat instructions","Store one text value","Delete a file","Rename a variable"], "answer":"Repeat instructions", "explanation":"Loops repeat an action multiple times."},
            {"q":"How many outputs from `for x in [2,4,6,8]: print(x)`?", "options":["2","3","4","8"], "answer":"4", "explanation":"The list contains four items, so print runs four times."},
        ],
        "remedial":[
            {"q":"How many values are in range(5)?", "options":["4","5","6","10"], "answer":"5", "explanation":"range(5) gives 0,1,2,3,4 — five values."},
            {"q":"Which loop is useful when you know the collection of items?", "options":["for loop","comment","import","variable name"], "answer":"for loop", "explanation":"A for loop is commonly used to visit items in a collection."},
            {"q":"What does `for x in [1, 2, 3]` visit first?", "options":["0","1","2","3"], "answer":"1", "explanation":"The loop visits the list in order, so the first value is 1."},
            {"q":"If a loop runs once for each of 6 items, how many repetitions happen?", "options":["5","6","7","12"], "answer":"6", "explanation":"One repetition per item means six repetitions for six items."},
        ],
    },
    "The 15-minute start": {
        "subject":"Study skills", "minutes":7,
        "intro":"Reduce the activation barrier by defining a very small first action.",
        "base":[
            {"q":"Which is the best 15-minute goal?", "options":["Master all algebra","Open the chapter and solve two equations","Finish every assignment this month","Become fluent in English"], "answer":"Open the chapter and solve two equations", "explanation":"A useful short goal is concrete, small and immediately startable."},
            {"q":"If you get stuck after five minutes, what should you record?", "options":["The exact point where you became confused","Nothing","Only your final score","I am bad at this"], "answer":"The exact point where you became confused", "explanation":"A precise stuck point makes help more useful."},
            {"q":"What should happen after the 15-minute block?", "options":["Decide the next small step","Always study three more hours","Delete your notes","Change goals completely"], "answer":"Decide the next small step", "explanation":"Finish with a clear next action rather than an overwhelming plan."},
        ],
        "remedial":[
            {"q":"Which task is easiest to start?", "options":["Study chemistry","Open page 24 and answer question 1","Fix my whole semester","Become organized"], "answer":"Open page 24 and answer question 1", "explanation":"Specific actions reduce the effort needed to begin."},
            {"q":"A useful study block should end with...", "options":["a next action","guilt","a bigger vague goal","no note"], "answer":"a next action", "explanation":"A next action makes restarting easier."},
            {"q":"Which restart note is most useful?", "options":["Continue question 4 on page 18","Study more","Do better tomorrow","Finish everything"], "answer":"Continue question 4 on page 18", "explanation":"A concrete restart cue removes decision-making when you come back."},
            {"q":"If a task still feels too big after 15 minutes, what should you do?", "options":["Split the next step again","Quit the subject","Add three hours","Ignore the stuck point"], "answer":"Split the next step again", "explanation":"Reducing the next step preserves momentum without creating overload."},
        ],
    },
    "Turn an ambition into an evidence list": {
        "subject":"University applications", "minutes":15,
        "intro":"Strong applications are easier to write when activities are documented as evidence, role, result and reflection.",
        "base":[
            {"q":"Which note is strongest evidence?", "options":["I like volunteering","I volunteered weekly","I designed a language game used by 8 students and recorded feedback","Volunteering is important"], "answer":"I designed a language game used by 8 students and recorded feedback", "explanation":"It shows action, your role, a measurable detail and evidence."},
            {"q":"What should you record after a project?", "options":["Only the title","Your role, outcome and what changed after feedback","Only compliments","Nothing until you apply"], "answer":"Your role, outcome and what changed after feedback", "explanation":"This makes future essays and interviews more specific and credible."},
            {"q":"What is a useful reflection question?", "options":["What assumption did I change after testing?","How can I sound impressive?","How can I hide mistakes?","How can I add adjectives?"], "answer":"What assumption did I change after testing?", "explanation":"Reflection is strongest when it shows learning and changed thinking."},
        ],
        "remedial":[
            {"q":"Which evidence item is easiest to verify?", "options":["I am passionate","A project link plus feedback and your role","I worked hard","I have potential"], "answer":"A project link plus feedback and your role", "explanation":"Verifiable artifacts make claims more concrete."},
            {"q":"Quality in a portfolio is mainly about...", "options":["clear evidence and depth","having the longest list","expensive activities","using formal words"], "answer":"clear evidence and depth", "explanation":"Depth, contribution, learning and proof are more useful than a long vague list."},
            {"q":"Which detail strengthens an application story most?", "options":["What you personally changed or contributed","More adjectives","A longer title","A vague team achievement"], "answer":"What you personally changed or contributed", "explanation":"Admissions readers need to understand your own contribution, not only the activity name."},
            {"q":"What should you keep after testing a project?", "options":["Feedback and the change you made","Only the first version","Only praise","Nothing"], "answer":"Feedback and the change you made", "explanation":"Feedback plus iteration shows learning, judgment and evidence of growth."},
        ],
    },
}

# -------------------- Motivation content --------------------
STORIES = [
    {
        "person":"Jan Koum", "title":"From limited resources to building WhatsApp",
        "barriers":["Financial limits","Lack of guidance","I do not know where to start"],
        "starting":"Koum moved to the United States as a teenager and grew up with limited financial resources. His early path into technology was not a straight, carefully planned route.",
        "turning":"He taught himself computing skills, worked in technology, and later co-founded WhatsApp. The useful pattern is the sequence: learn a skill, use it in a real environment, notice a problem, then build around it.",
        "lesson":"You do not need a complete ten-year plan before taking a useful step. A small skill can become a bridge to the next opportunity when you keep turning learning into evidence.",
        "action":"Choose one skill your current goal requires and complete one free, concrete learning task for it today.",
        "source_label":"Britannica biography", "source_url":"https://www.britannica.com/biography/Jan-Koum",
    },
    {
        "person":"José Hernández", "title":"A long path to becoming an astronaut",
        "barriers":["Low confidence","Lack of guidance","Financial limits"],
        "starting":"Hernández grew up in a migrant farmworker family and spent part of his childhood moving with seasonal work. An aerospace career did not feel automatic or nearby.",
        "turning":"He built prerequisites step by step: education, engineering experience, repeated applications and continued skill development.",
        "lesson":"A distant goal becomes more workable when it is converted into requirements you can build one at a time.",
        "action":"Write one long-term goal, list the next three requirements, and act on the smallest one.",
        "source_label":"NASA biography", "source_url":"https://www.nasa.gov/people/jose-hernandez/",
    },
    {
        "person":"Malala Yousafzai", "title":"Education as an action, not only an aspiration",
        "barriers":["School stress or bullying","Low confidence","Lack of guidance"],
        "starting":"Yousafzai became known internationally through advocacy for girls' education in circumstances where access to schooling itself was under threat.",
        "turning":"Her story shows that education can be both a personal goal and a system-level issue. She continued learning while using writing and public advocacy to make the barrier visible.",
        "lesson":"When a barrier is structural, the answer is not always 'try harder.' Progress may require allies, safer routes, institutions or communities that can change the conditions around you.",
        "action":"Name one barrier that effort alone cannot solve, then identify one person or institution that could reduce it.",
        "source_label":"Nobel Prize biography", "source_url":"https://www.nobelprize.org/prizes/peace/2014/yousafzai/biographical/",
    },
]

COMMUNITY_POSTS = [
    ("Nova15","Math","I used to freeze when I saw functions. Drawing the graph first made the formula less scary."),
    ("Orbit16","Study skills","I study in 20-minute blocks because long sessions made me give up. Short sessions finally became a habit."),
    ("Mira14","English","Reading one short article aloud each day helped me stop being afraid of pronunciation mistakes."),
    ("Atlas16","Applications","I keep one evidence document with projects, results and what I personally did. Essay writing became much easier."),
]

PROVIDER_OPPORTUNITIES = [
    {
        "id":"nyas-junior-academy", "name":"The Junior Academy — New York Academy of Sciences",
        "category":"STEM program", "cost":"Free", "countries":["Global"], "languages":["English"],
        "age_min":13, "age_max":17,
        "goals":["Learn coding","Prepare for university applications","Find scholarships and opportunities"],
        "summary":"Online project-based STEM challenges with international teams and STEM mentors.",
        "eligibility":"Ages 13–17; online; English proficiency is required. Application cycles have deadlines.",
        "checklist":["Check the current application cycle.","Prepare a short explanation of your STEM interests.","Collect one project or investigation example.","Plan time for team collaboration if accepted."],
        "url":"https://www.nyas.org/learning/high-school-research-programs/the-junior-academy/",
    },
    {
        "id":"uwc-scholarships", "name":"UWC — scholarship route through a national committee",
        "category":"Scholarship / school opportunity", "cost":"Financial support available", "countries":["Global"], "languages":["English"],
        "age_min":15, "age_max":18,
        "goals":["Prepare for university applications","Find scholarships and opportunities"],
        "summary":"A route to UWC schools and colleges, with need-based financial support through national committees.",
        "eligibility":"Selection rules and timelines vary by national committee; check the local route before applying.",
        "checklist":["Find your national committee.","Check local age and deadline rules.","Collect evidence of initiative, service and academic readiness.","Review the financial-support process."],
        "url":"https://uwc.org/how-to-apply/",
    },
    {
        "id":"schoolhouse", "name":"Schoolhouse.world", "category":"Free tutoring / admissions support",
        "cost":"Free", "countries":["Global"], "languages":["English"], "age_min":13, "age_max":19,
        "goals":["Understand mathematics","Prepare for SAT / international exams","Prepare for university applications"],
        "summary":"Free peer-led tutoring, SAT support, homework help and college admissions workshops.",
        "eligibility":"Online access; specific programs may have their own requirements.",
        "checklist":["Choose one concrete subject or admissions question.","Prepare the exact point where you are stuck.","Join a session that matches the goal.","Record one next step afterward."],
        "url":"https://schoolhouse.world/",
    },
    {
        "id":"khan", "name":"Khan Academy", "category":"Learning / test preparation", "cost":"Free",
        "countries":["Global"], "languages":["English"], "age_min":12, "age_max":19,
        "goals":["Understand mathematics","Improve school grades","Prepare for SAT / international exams"],
        "summary":"Free learning and practice across mathematics, science and test-preparation topics.",
        "eligibility":"Open online access; course availability and language vary by subject.",
        "checklist":["Choose one skill aligned to your pathway.","Complete a short diagnostic set.","Record errors by concept.","Return to the weakest concept first."],
        "url":"https://www.khanacademy.org/",
    },
]

# -------------------- Lightweight persistence --------------------
# This demo persists non-sensitive profile choices and progress in a compressed URL token.
# Free-text support/community messages are intentionally NOT persisted.
PERSIST_KEYS = [
    "page", "profile", "completed_modules", "saved_opportunities", "support_request_count",
    "lesson_progress", "saved_actions", "admissions_plan", "requirements_checked", "exam_tracker"
]

def _jsonable(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value

def encode_state(data):
    raw = json.dumps(_jsonable(data), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    packed = zlib.compress(raw, level=9)
    return base64.urlsafe_b64encode(packed).decode("ascii")

def decode_state(token):
    try:
        raw = zlib.decompress(base64.urlsafe_b64decode(token.encode("ascii")))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}

def persistent_snapshot():
    profile_data = dict(st.session_state.get("profile") or {})
    # Do not put free-text help requests into the URL token.
    profile_data["current_need"] = ""
    return {
        "page": st.session_state.get("page", "Home"),
        "profile": profile_data or None,
        "completed_modules": sorted(st.session_state.get("completed_modules", set())),
        "saved_opportunities": sorted(st.session_state.get("saved_opportunities", set())),
        "support_request_count": int(st.session_state.get("support_request_count", 0)),
        "lesson_progress": st.session_state.get("lesson_progress", {}),
        "saved_actions": st.session_state.get("saved_actions", [])[-8:],
        "admissions_plan": st.session_state.get("admissions_plan", {}),
        "requirements_checked": sorted(st.session_state.get("requirements_checked", set())),
        "exam_tracker": st.session_state.get("exam_tracker", [])[-12:],
    }

def sync_persistence():
    try:
        st.query_params["state"] = encode_state(persistent_snapshot())
    except Exception:
        pass

# Hydrate before defaults.
if "_hydrated_v06" not in st.session_state:
    st.session_state._hydrated_v06 = True
    token = st.query_params.get("state")
    restored = decode_state(token) if token else {}
    if restored:
        st.session_state.page = restored.get("page", "Home")
        if restored.get("profile"):
            st.session_state.profile = restored["profile"]
        st.session_state.completed_modules = set(restored.get("completed_modules", []))
        st.session_state.saved_opportunities = set(restored.get("saved_opportunities", []))
        st.session_state.support_request_count = int(restored.get("support_request_count", 0))
        st.session_state.lesson_progress = restored.get("lesson_progress", {})
        st.session_state.saved_actions = restored.get("saved_actions", [])
        st.session_state.admissions_plan = restored.get("admissions_plan", {})
        st.session_state.requirements_checked = set(restored.get("requirements_checked", []))
        st.session_state.exam_tracker = restored.get("exam_tracker", [])

# -------------------- Session state --------------------
defaults = {
    "page":"Home", "profile":None, "completed_modules":set(), "saved_opportunities":set(),
    "support_request_count":0, "support_requests":[], "community_submissions":[],
    "tutor_session":None, "lesson_progress":{}, "saved_actions":[], "admissions_plan":{},
    "portfolio_items":[], "requirements_checked":set(), "exam_tracker":[],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------- Navigation --------------------
NAV = [
    ("Home","🏠"), ("My Pathway","🧭"), ("AI Tutor","🤖"), ("Learning Hub","📚"),
    ("Motivation","🌱"), ("Human Support","🤝"), ("Community","💬"),
    ("Opportunities","🎓"), ("University Planner","🗺️"), ("Profile","👤"),
    ("About the Project","ℹ️"),
]

def nav_to(name):
    st.session_state.page = name
    sync_persistence()
    st.rerun()

def btn_nav(label, target, key, primary=False):
    if st.button(label, key=key, type="primary" if primary else "secondary", use_container_width=True):
        nav_to(target)

st.sidebar.markdown("<div class='site-title'>🧭 Opportunity Navigator</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='site-sub'>One place to learn, plan, connect and move forward.</div>", unsafe_allow_html=True)
for name, icon in NAV:
    label = f"{'🔵' if st.session_state.page == name else '⚪'}  {icon} {name}"
    if st.sidebar.button(label, key=f"nav_{name}", use_container_width=True):
        st.session_state.page = name
        sync_persistence()
        st.rerun()

st.sidebar.markdown("---")
if st.session_state.profile:
    p = st.session_state.profile
    st.sidebar.caption(f"Profile: age {p['age']} · {p['country']} · {p['language']}")
else:
    st.sidebar.caption("Create a profile to personalize the platform.")
st.sidebar.caption(f"Prototype v{VERSION}")

with st.sidebar.expander("Save / restore demo progress"):
    st.caption("Profile selections and counters survive refresh through a compact state token in the URL. Free-text messages are not stored there.")
    export_data = json.dumps(_jsonable(persistent_snapshot()), ensure_ascii=False, indent=2)
    st.download_button("Export progress", export_data, file_name="opportunity_navigator_progress.json", mime="application/json", use_container_width=True)
    uploaded = st.file_uploader("Import progress", type=["json"], key="progress_import")
    if uploaded is not None and st.button("Restore imported progress", use_container_width=True):
        try:
            data = json.load(uploaded)
            st.session_state.page = data.get("page", "Home")
            st.session_state.profile = data.get("profile")
            st.session_state.completed_modules = set(data.get("completed_modules", []))
            st.session_state.saved_opportunities = set(data.get("saved_opportunities", []))
            st.session_state.support_request_count = int(data.get("support_request_count", 0))
            st.session_state.lesson_progress = data.get("lesson_progress", {})
            st.session_state.saved_actions = data.get("saved_actions", [])
            st.session_state.admissions_plan = data.get("admissions_plan", {})
            st.session_state.requirements_checked = set(data.get("requirements_checked", []))
            st.session_state.exam_tracker = data.get("exam_tracker", [])
            sync_persistence()
            st.success("Progress restored.")
            st.rerun()
        except Exception:
            st.error("That file could not be restored.")
    if st.button("Reset demo progress", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v.copy() if isinstance(v, dict) else (set(v) if isinstance(v, set) else (list(v) if isinstance(v, list) else v))
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

# -------------------- Helpers --------------------
def profile():
    return st.session_state.profile or {}

def main_goal():
    goals = profile().get("goals", [])
    return goals[0] if goals else "Build a useful next step"

def score_opportunity(o, p):
    score, reasons = 0, []
    age = p.get("age", 15)
    if o["age_min"] <= age <= o["age_max"]:
        score += 3; reasons.append("fits your age")
    country = p.get("country", "Global / not specified")
    if "Global" in o["countries"] or country in o["countries"]:
        score += 2; reasons.append("available globally / in your region")
    overlap = set(p.get("goals", [])).intersection(o["goals"])
    if overlap:
        score += 3 + len(overlap); reasons.append("matches your goal")
    if "Free only" in p.get("access", []) and o["cost"] == "Free":
        score += 2; reasons.append("free")
    lang = p.get("language", "English")
    other = p.get("other_languages", [])
    if lang in o["languages"] or any(x in o["languages"] for x in other):
        score += 1; reasons.append("language match")
    return score, reasons

def normalize_answer(text):
    return re.sub(r"\s+", "", str(text).strip().lower())

def tutor_payload(subject, topic, question, help_style="Explain it simply", variant="main"):
    q = (question or "").lower()
    topic_l = (topic or "").lower()
    if subject == "Math" and ("linear" in topic_l or "equation" in topic_l or "2x" in q or "3x" in q):
        base = {
            "diagnosis":"The key idea is to keep both sides of an equation balanced while you isolate x.",
            "simple":"Undo operations in reverse order. If something is added, subtract it. If x is multiplied, divide.",
            "hint":"For 2x + 3 = 11, remove +3 first. What remains on the left?",
            "example":"Example: 3x + 6 = 18 → subtract 6 → 3x = 12 → divide by 3 → x = 4.",
            "check":"Try this: solve 2x + 3 = 11.",
            "answer":"4",
            "answer_explanation":"Subtract 3 from both sides to get 2x = 8, then divide both sides by 2: x = 4.",
        }
    elif subject == "Math" and "percent" in topic_l:
        base = {
            "diagnosis":"A percentage is a part out of 100. Most questions become easier after converting the percent to a decimal.",
            "simple":"20% means 20/100, which is 0.20. Then multiply by the whole amount.",
            "hint":"For 20% of 150, calculate 0.20 × 150.",
            "example":"25% of 40 = 0.25 × 40 = 10.",
            "check":"What is 20% of 150?",
            "answer":"30",
            "answer_explanation":"0.20 × 150 = 30.",
        }
    elif subject == "Math" and ("graph" in topic_l or "function" in topic_l):
        base = {
            "diagnosis":"A graph connects an input x to an output y. Start by identifying what changes and what stays fixed.",
            "simple":"Pick a few x-values, calculate y for each one, then plot the pairs (x, y).",
            "hint":"For y = 2x + 1, try x = 0 first. What is y?",
            "example":"If y = 2x + 1 and x = 2, then y = 5, so one point is (2,5).",
            "check":"For y = 2x + 1, what is y when x = 3?",
            "answer":"7",
            "answer_explanation":"2 × 3 + 1 = 7.",
        }
    elif subject == "English" and ("article" in topic_l or "a / an" in topic_l):
        base = {
            "diagnosis":"The choice depends on whether the noun is specific and on the sound at the beginning of the next word.",
            "simple":"Use a/an for one non-specific thing. Use the when both people know which thing you mean.",
            "hint":"Listen to the sound: 'an elephant' but 'a university' because university begins with a /y/ sound.",
            "example":"I saw a dog. The dog was wet. First mention: a dog. Second mention: the dog.",
            "check":"Choose the missing word: I saw ___ elephant.",
            "answer":"an",
            "answer_explanation":"Elephant begins with a vowel sound, so use 'an'.",
        }
    elif subject == "Coding" and "loop" in topic_l:
        base = {
            "diagnosis":"A loop repeats an instruction. To understand it, list the values the loop will visit.",
            "simple":"Read the loop as: for each value, do the indented action once.",
            "hint":"range(3) gives 0, 1, 2.",
            "example":"for i in range(3): print(i) prints three lines: 0, 1, 2.",
            "check":"How many times does for i in range(3) repeat?",
            "answer":"3",
            "answer_explanation":"range(3) contains three values: 0, 1 and 2.",
        }
    elif subject == "University applications":
        base = {
            "diagnosis":"Admissions questions become manageable when you separate requirements, evidence and deadlines.",
            "simple":"Make a table with: course, academic requirements, exams, language scores, deadline, essays, portfolio/evidence and financial aid.",
            "hint":"Start with the official course page, not a blog. Record the exact requirement and its source URL.",
            "example":"Evidence item: 'Built a project, tested it with 8 users, changed feature X after feedback, link saved.'",
            "check":"What is the first requirement you still have not verified from an official source?",
            "answer":None,
            "answer_explanation":"A precise unknown tells you what to research next.",
        }
    else:
        base = {
            "diagnosis":f"Your stuck point is: {question.strip() or topic}.",
            "simple":"Break it into one small claim, one example and one question you can test.",
            "hint":"Ask: what do I already understand, and what is the first missing connection?",
            "example":"Write one example that works, then one example that confuses you. Compare the difference.",
            "check":"Explain the first part you cannot yet explain in your own words.",
            "answer":None,
            "answer_explanation":"That identifies where the next explanation should begin.",
        }
    if variant == "hint" or help_style == "Guide me with hints":
        focus = base["hint"]
    elif variant == "example" or help_style == "Show an example":
        focus = base["example"]
    else:
        focus = base["simple"]
    return base, focus

def get_lesson_state(title):
    if title not in st.session_state.lesson_progress:
        st.session_state.lesson_progress[title] = {
            "queue":[0,1,2], "pos":0, "incorrect_attempts":0, "answered":{},
            "wrong_counts":{}, "completed":False, "adaptive_added":0, "last_result":None,
        }
    lp = st.session_state.lesson_progress[title]
    # Migrate older saved demo state safely.
    lp.setdefault("queue", [0,1,2])
    lp.setdefault("pos", 0)
    lp.setdefault("incorrect_attempts", 0)
    lp.setdefault("answered", {})
    lp.setdefault("wrong_counts", {})
    lp.setdefault("completed", False)
    lp.setdefault("adaptive_added", max(0, len(lp.get("queue", [])) - 3))
    lp.setdefault("last_result", None)
    return lp

def full_question_bank(module):
    return module["base"] + module.get("remedial", [])

def pii_findings(text):
    text = text or ""
    findings = []
    if re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, flags=re.I):
        findings.append("email address")
    if re.search(r"(?<!\d)(?:\+?\d[\d\s().-]{5,}\d)(?!\d)", text):
        findings.append("phone number")
    if re.search(r"(?<!\w)@[A-Za-z0-9_]{2,}", text):
        findings.append("social-media handle")
    if re.search(r"\b(?:instagram|telegram|whatsapp|snapchat|discord)\s*[:=@]?\s*[A-Za-z0-9_.+-]{3,}\b", text, flags=re.I):
        findings.append("contact / social-media detail")
    return sorted(set(findings))

def is_safe_public_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower()
        if host in {"localhost", "127.0.0.1", "::1"}:
            return False
        try:
            ip = ipaddress.ip_address(host)
            return not (ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local)
        except ValueError:
            try:
                resolved = socket.gethostbyname(host)
                ip = ipaddress.ip_address(resolved)
                if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                    return False
            except Exception:
                pass
        return True
    except Exception:
        return False

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_page_text(url):
    if not is_safe_public_url(url):
        raise ValueError("Only public http/https pages are allowed.")
    r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 OpportunityNavigatorPrototype/0.5"})
    r.raise_for_status()
    if "text/html" not in r.headers.get("content-type", ""):
        return ""
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script","style","noscript","svg"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    return text[:120000]

def extract_admission_mentions(text):
    clean = re.sub(r"\s+", " ", text or "")
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    groups = {
        "Exams / scores":["ielts","toefl","sat","act","duolingo","ib ","a-level","admission test","entrance exam"],
        "Application writing":["personal statement","motivation letter","statement of purpose","essay","recommendation","reference letter"],
        "Deadlines":["deadline","application closes","apply by","closing date"],
        "Academic requirements":["entry requirement","academic requirement","grade requirement","prerequisite","minimum grade"],
        "Scholarships / aid":["scholarship","financial aid","funding","bursary"],
    }
    out = {}
    for label, keys in groups.items():
        matches = []
        for s in sentences:
            sl = s.lower()
            if any(k in sl for k in keys):
                snippet = s.strip()
                if 25 <= len(snippet) <= 420:
                    matches.append(snippet)
            if len(matches) >= 3:
                break
        if matches:
            out[label] = matches
    return out

def program_foundation(program):
    p = (program or "").lower()
    if any(x in p for x in ["computer", "software", "data", "ai", "artificial", "engineering"]):
        return ["Mathematics / algebra", "Problem solving", "Programming fundamentals", "One documented technical project"]
    if any(x in p for x in ["business", "econom", "finance", "management"]):
        return ["Mathematics / statistics", "Writing and argument", "Economics / business fundamentals", "One evidence-based project or initiative"]
    if any(x in p for x in ["medicine", "biology", "biomed", "chemistry"]):
        return ["Biology", "Chemistry", "Quantitative reasoning", "Evidence of sustained interest or service"]
    if any(x in p for x in ["law", "politic", "history", "humanit", "literature"]):
        return ["Analytical reading", "Structured writing", "Evidence-based argument", "One sustained research / writing project"]
    return ["Strong school fundamentals", "Academic writing", "Evidence of sustained interest", "One project that demonstrates initiative"]


def tutor_followup_response(subject, topic, question, base):
    """Deterministic follow-up logic for the portfolio prototype."""
    q = (question or "").strip().lower()
    topic_l = (topic or "").lower()
    if not q:
        return "Tell me the exact step that is still unclear."
    if subject == "Math" and ("linear" in topic_l or "equation" in topic_l):
        if any(x in q for x in ["why subtract", "why do we subtract", "sign change", "move the", "other side"]):
            return ("Think of an equation as a balanced scale. We are not literally moving a number and changing its sign. "
                    "We do the same operation to both sides. For 2x + 3 = 11, subtract 3 from both sides: "
                    "2x + 3 − 3 = 11 − 3, so 2x = 8.")
        if any(x in q for x in ["why divide", "divide by", "coefficient"]):
            return ("After you get 2x = 8, x is being multiplied by 2. The inverse operation is division, "
                    "so divide both sides by 2: 2x/2 = 8/2, giving x = 4.")
        if "check" in q or "know" in q:
            return "Substitute the answer back into the original equation. If x = 4, then 2×4 + 3 = 11, so it checks."
    if subject == "Math" and ("graph" in topic_l or "function" in topic_l):
        if "slope" in q:
            return "Slope tells you how much y changes when x increases by 1. In y = 2x + 1, the slope is 2."
        if any(x in q for x in ["plot", "point", "where"]):
            return "Choose an x-value, calculate y, and plot the pair (x, y). Repeat for two or three x-values."
    if subject == "English" and "article" in topic_l:
        if "university" in q:
            return "Use 'a university' because university begins with a /y/ sound, like 'you', not a vowel sound."
        if "the" in q:
            return "Use 'the' when the listener can identify the specific noun you mean, often because it was mentioned before or is obvious from context."
    if subject == "Coding" and "loop" in topic_l:
        if "range" in q:
            return "In Python, range(n) starts at 0 and stops before n. So range(3) gives 0, 1, 2."
        return "Trace the loop one repetition at a time. Write down the current value and the output for each pass."
    if subject == "University applications":
        return ("Turn the question into a verification task: identify the exact course, intake year and official page, "
                "then record the requirement, the source link and the date you checked it.")
    return base.get("hint") or base.get("simple") or "Break the problem into one small step and tell me which connection is missing."

@st.cache_data(ttl=1800, show_spinner=False)
def web_search_candidates(query, max_results=6):
    """Small no-key web search helper for finding candidate official pages.
    It uses DuckDuckGo's public HTML results and is intentionally best-effort.
    """
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    r = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0 OpportunityNavigatorPrototype/0.6"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for a in soup.select("a.result__a"):
        href = a.get("href") or ""
        title = " ".join(a.stripped_strings)
        if not href or not title:
            continue
        parsed = urlparse(href)
        if "duckduckgo.com" in (parsed.netloc or ""):
            uddg = parse_qs(parsed.query).get("uddg", [None])[0]
            if uddg:
                href = unquote(uddg)
        if is_safe_public_url(href):
            results.append({"title":title, "url":href})
        if len(results) >= max_results:
            break
    return results


def admissions_search_queries(plan):
    university = (plan.get("university") or "").strip()
    program = (plan.get("program") or "").strip()
    country = (plan.get("country") or "").strip()
    stem = " ".join(x for x in [university, program, country] if x and x != "Global / not specified")
    return {
        "Course & entry requirements": f"{stem} official undergraduate {program} admission entry requirements",
        "Exams & language scores": f"{stem} official IELTS TOEFL SAT admission test score requirements",
        "Scholarships / financial aid": f"{stem} official scholarships financial aid international students",
        "Application essays / personal statement": f"{stem} official application personal statement essay requirements",
    }

# -------------------- Pages --------------------
page = st.session_state.page

if page == "Home":
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">Research-driven social mobility platform</div>
      <h1>Your next step should not depend on knowing where to look.</h1>
      <p>Opportunity Navigator combines learning, tutoring, motivation, safe human support,
      community, admissions planning and opportunity discovery in one place.</p>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("<div class='feature-card'><div class='label'>Learn</div><h3>AI Tutor + Learning Hub</h3><p class='muted'>Ask about the exact stuck point, get hints and explanations, then practise adaptively.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='feature-card'><div class='label'>Navigate</div><h3>Personal pathway</h3><p class='muted'>Turn goals, barriers, progress and admissions targets into useful next actions.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='feature-card'><div class='label'>Connect safely</div><h3>Human support + community</h3><p class='muted'>Request a mentor route and use moderated topic spaces with contact-detail blocking.</p></div>", unsafe_allow_html=True)
    st.write("")
    b1,b2,b3 = st.columns(3)
    with b1:
        btn_nav("Continue my pathway" if profile() else "Build my profile", "My Pathway" if profile() else "Profile", "home_main", primary=True)
    with b2:
        btn_nav("Explore Learning Hub", "Learning Hub", "home_learn")
    with b3:
        btn_nav("Plan university applications", "University Planner", "home_uni")
    st.markdown("### One platform, not another directory")
    st.write("Learning, tutoring, planning, progress tracking and preparation happen inside the platform. Official provider pages are a secondary verification/application layer.")

elif page == "Profile":
    st.title("Build your learner & access profile")
    st.caption("Country and language fields use global searchable lists. Start typing to jump to a value.")
    old = profile()
    with st.form("profile_form"):
        c1,c2 = st.columns(2)
        with c1:
            age = st.slider("Age", 12, 19, int(old.get("age",15)))
            country_default = old.get("country","Global / not specified")
            country = st.selectbox("Country / region", COUNTRIES, index=COUNTRIES.index(country_default) if country_default in COUNTRIES else 0)
            lang_default = old.get("language","English")
            language = st.selectbox("Preferred language", LANGUAGES, index=LANGUAGES.index(lang_default) if lang_default in LANGUAGES else 0)
            other_languages = st.multiselect("Other languages you can use", LANGUAGES, default=old.get("other_languages",[]))
        with c2:
            goals = st.multiselect("What do you want to work on?", GOALS, default=old.get("goals",["Understand mathematics"]))
            barriers = st.multiselect("What makes progress harder right now?", BARRIERS, default=old.get("barriers",["Lack of guidance"]))
            support = st.selectbox("Preferred support", SUPPORT_PREFS, index=SUPPORT_PREFS.index(old.get("support","A mix of both")) if old.get("support","A mix of both") in SUPPORT_PREFS else 2)
            access = st.multiselect("Access needs", ACCESS_NEEDS, default=old.get("access",["Free only","Works on a phone"]))
        current_need = st.text_input("What do you need help with today?", value=old.get("current_need",""), placeholder="Example: I do not understand graphs and I also need a university preparation plan.")
        submitted = st.form_submit_button("Save profile and build my pathway", type="primary", use_container_width=True)
    if submitted:
        st.session_state.profile = {
            "age":age, "country":country, "language":language, "other_languages":other_languages,
            "goals":goals or ["Improve school grades"], "barriers":barriers or ["Lack of guidance"],
            "support":support, "access":access, "current_need":current_need,
        }
        sync_persistence()
        st.success("Profile saved. Your pathway has been rebuilt and core profile selections will survive refresh.")
    if profile() and st.button("Open my pathway", type="primary"):
        nav_to("My Pathway")

elif page == "My Pathway":
    st.title("My pathway")
    p = profile()
    if not p:
        st.info("Create your profile first so the pathway can use your goals, language and access constraints.")
        btn_nav("Create profile", "Profile", "path_create", primary=True)
    else:
        st.markdown(f"<div class='notice'><b>Today:</b> focus on one useful next step, not a long list. Your main goal is <b>{main_goal()}</b>.</div>", unsafe_allow_html=True)
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Learning modules completed", len(st.session_state.completed_modules))
        m2.metric("Saved opportunities", len(st.session_state.saved_opportunities))
        m3.metric("Support requests", st.session_state.support_request_count)
        m4.metric("Saved actions", len(st.session_state.saved_actions))
        need = p.get("current_need","").lower()
        steps = []
        if any("math" in g.lower() for g in p.get("goals",[])) or any(x in need for x in ["math","algebra","graph"]):
            steps.append(("AI Tutor","Do one focused tutoring session and ask at least one follow-up question."))
            steps.append(("Learning Hub","Complete a short math lesson. Extra practice appears automatically after mistakes."))
        else:
            steps.append(("Learning Hub","Complete one short lesson aligned to your current goal."))
        if p.get("barriers"):
            steps.append(("Motivation", f"Read a story matched to '{p['barriers'][0]}' and save one concrete action."))
        if p.get("support") != "Mostly self-study":
            steps.append(("Human Support","Create a structured request for an academic mentor or support route."))
        if any("university" in g.lower() or "scholar" in g.lower() for g in p.get("goals",[])):
            steps.append(("University Planner","Build a target-university research board and portfolio evidence list."))
        steps.append(("Opportunities","Review personalized opportunity cards and save one realistic next option."))
        st.subheader("Today's path")
        for i,(target,desc) in enumerate(steps[:6], start=1):
            st.markdown(f"<div class='path-step'><b>{i}. {target}</b><br><span class='muted'>{desc}</span></div>", unsafe_allow_html=True)
            if st.button(f"Go to {target}", key=f"path_{i}_{target}"):
                nav_to(target)
        if st.session_state.saved_actions:
            st.subheader("Actions I saved")
            for a in st.session_state.saved_actions[-5:]:
                st.write("•", a)

elif page == "AI Tutor":
    st.title("AI Tutor — explain the exact stuck point")
    st.write("Choose a subject and topic, describe exactly what is unclear, then keep asking follow-up questions in the same session. The portfolio prototype uses structured logic rather than a live generative model.")
    with st.expander("Technical note for portfolio reviewers"):
        st.write("A production version would add a safeguarded LLM/RAG layer, source grounding, age-appropriateness checks and answer-quality evaluation.")
    c1,c2 = st.columns(2)
    with c1:
        subject = st.selectbox("Subject", list(SUBJECT_TOPICS.keys()), key="tutor_subject")
        topic_options = SUBJECT_TOPICS[subject]
        topic = st.selectbox("Topic", topic_options, key=f"topic_{subject}")
        if topic == "Other":
            topic = st.text_input("Write the topic", key="custom_topic")
        stuck = st.text_area("What do you not understand?", placeholder="Example: I don't understand why 2x + 3 = 11 means x = 4.")
        tried = st.text_area("What have you tried?", placeholder="Example: I tried subtracting 3 but I do not understand why we do it on both sides.")
    with c2:
        help_style = st.selectbox("How should the tutor help?", ["Explain it simply","Guide me with hints","Show an example"])
        confidence = st.slider("How confident do you feel about this topic?", 1, 5, 2)
        st.caption("The prototype uses this to choose a gentler or more direct starting point.")
    b1,b2 = st.columns([2,1])
    if b1.button("Start tutoring session", type="primary", use_container_width=True):
        if not (topic or "").strip():
            st.warning("Choose or write a topic first.")
        elif not stuck.strip():
            st.warning("Write the exact point that is unclear so the explanation can start there.")
        else:
            base, focus = tutor_payload(subject, topic, stuck, help_style)
            st.session_state.tutor_session = {
                "subject":subject, "topic":topic, "stuck":stuck, "tried":tried,
                "help_style":help_style, "confidence":confidence, "base":base,
                "history":[{"role":"assistant","text":focus}],
            }
            st.rerun()
    if b2.button("Clear session", use_container_width=True):
        st.session_state.tutor_session = None
        st.rerun()

    s = st.session_state.tutor_session
    if s:
        base = s["base"]
        st.markdown("### 1. Locate the stuck point")
        st.markdown(f"<div class='card'><b>Topic:</b> {s['subject']} → {s['topic']}<br><br>{base['diagnosis']}</div>", unsafe_allow_html=True)
        st.markdown("### 2. Explanation and follow-up")
        for msg in s.get("history",[]):
            if msg["role"] == "user":
                st.chat_message("user").write(msg["text"])
            else:
                st.chat_message("assistant").write(msg["text"])
        x1,x2,x3 = st.columns(3)
        if x1.button("Explain more simply", key="tutor_simpler"):
            s["history"].append({"role":"assistant","text":base.get("simple", "Let's make the first step smaller.")})
            st.rerun()
        if x2.button("Give me a hint", key="tutor_hint"):
            s["history"].append({"role":"assistant","text":base.get("hint", "What is the first operation you can undo?")})
            st.rerun()
        if x3.button("Show another example", key="tutor_example"):
            s["history"].append({"role":"assistant","text":base.get("example", "Try a smaller example with the same rule.")})
            st.rerun()
        with st.form("tutor_followup_form", clear_on_submit=True):
            follow = st.text_input("Ask another question about the same topic", placeholder="Example: Why do we subtract 3 from both sides?")
            ask_follow = st.form_submit_button("Ask follow-up")
        if ask_follow and follow.strip():
            s["history"].append({"role":"user","text":follow.strip()})
            reply = tutor_followup_response(s["subject"], s["topic"], follow, base)
            s["history"].append({"role":"assistant","text":reply})
            st.rerun()

        st.markdown("### 3. Check your understanding")
        st.write(base["check"])
        ans = st.text_input("Your answer / explanation", key="tutor_check_answer")
        if st.button("Check my answer", key="tutor_check"):
            if base["answer"] is None:
                st.info(base["answer_explanation"])
            elif normalize_answer(ans) == normalize_answer(base["answer"]):
                st.success("Correct.")
                st.info("Why: " + base["answer_explanation"])
            else:
                st.error("Not yet. Read the explanation, then try again or ask a follow-up question above.")
                st.info("Explanation: " + base["answer_explanation"])
        st.caption("You can continue asking follow-up questions without restarting the session.")

elif page == "Learning Hub":
    st.title("Learning Hub")
    st.write("Lessons begin with three core questions. Mistakes automatically add extra practice, so a learner who is struggling gets more questions instead of stopping after a fixed set.")
    subjects = ["All"] + sorted({m["subject"] for m in MODULES.values()})
    filt = st.selectbox("Filter by subject", subjects)
    available = [name for name,m in MODULES.items() if filt == "All" or m["subject"] == filt]
    title = st.selectbox("Choose a lesson", available)
    module = MODULES[title]
    lp = get_lesson_state(title)
    bank = full_question_bank(module)
    st.markdown(f"<div class='card'><b>{title}</b> · {module['minutes']} min<br><span class='muted'>{module['intro']}</span></div>", unsafe_allow_html=True)

    if lp.get("completed"):
        total_seen = max(1, len(lp.get("queue", [])))
        mistakes = int(lp.get("incorrect_attempts", 0))
        st.success(f"Lesson completed. You worked through {total_seen} question(s).")
        if mistakes:
            st.info(f"Adaptive practice added {lp.get('adaptive_added', 0)} extra question(s) after {mistakes} incorrect attempt(s).")
        if st.button("Practice this lesson again"):
            st.session_state.lesson_progress[title] = {
                "queue":[0,1,2], "pos":0, "incorrect_attempts":0, "answered":{},
                "wrong_counts":{}, "completed":False, "adaptive_added":0, "last_result":None,
            }
            sync_persistence(); st.rerun()
    else:
        pos = min(int(lp.get("pos",0)), len(lp["queue"])-1)
        q_index = lp["queue"][pos]
        q = bank[q_index]
        st.progress(pos / max(1,len(lp["queue"])))
        st.caption(f"Question {pos+1} of {len(lp['queue'])} · mistakes so far: {lp['incorrect_attempts']}")
        st.markdown(f"## {q['q']}")
        choice = st.radio("Choose an answer", q["options"], key=f"lesson_{title}_{q_index}_{pos}", index=None)
        if st.button("Check answer", type="primary", key=f"check_{title}_{q_index}_{pos}"):
            if choice is None:
                st.warning("Choose an answer first.")
            elif choice == q["answer"]:
                lp["answered"][str(q_index)] = "correct"
                lp["last_result"] = "correct"
                sync_persistence(); st.rerun()
            else:
                lp["incorrect_attempts"] += 1
                lp["wrong_counts"][str(q_index)] = int(lp["wrong_counts"].get(str(q_index),0)) + 1
                lp["answered"][str(q_index)] = "wrong"
                lp["last_result"] = "wrong"
                sync_persistence(); st.rerun()

        result = lp.get("last_result")
        if result == "wrong":
            st.error("Not yet — use the explanation, then try the same question again.")
            st.info("Explanation: " + q["explanation"])
            if lp["incorrect_attempts"] >= 2:
                st.caption("The lesson will add extra practice before completion because this topic needs more repetition.")
        elif result == "correct":
            st.success("Correct.")
            st.info("Why: " + q["explanation"])
            if st.button("Next question", key=f"next_{title}_{q_index}_{pos}"):
                lp["last_result"] = None
                remedial_count = len(module.get("remedial", []))
                mistakes = int(lp.get("incorrect_attempts",0))
                if mistakes == 0:
                    target_extra = 0
                elif mistakes == 1:
                    target_extra = min(remedial_count, 1)
                elif mistakes <= 3:
                    target_extra = min(remedial_count, 2)
                else:
                    target_extra = remedial_count
                current_extra = max(0, len(lp["queue"]) - len(module["base"]))
                if target_extra > current_extra:
                    base_len = len(module["base"])
                    already = set(lp["queue"])
                    candidates = [i for i in range(base_len, base_len + remedial_count) if i not in already]
                    to_add = candidates[:target_extra-current_extra]
                    lp["queue"].extend(to_add)
                    lp["adaptive_added"] = max(0, len(lp["queue"]) - base_len)
                if lp["pos"] < len(lp["queue"]) - 1:
                    lp["pos"] += 1
                else:
                    lp["completed"] = True
                    st.session_state.completed_modules.add(title)
                sync_persistence(); st.rerun()
        if lp.get("adaptive_added"):
            st.caption(f"Adaptive practice active: {lp['adaptive_added']} extra question(s) have been added based on mistakes.")

elif page == "Motivation":
    st.title("Motivation → evidence → action")
    st.write("A story should match a real barrier, show a turning point, and end with something the learner can do now.")
    p = profile()
    barrier_options = BARRIERS
    default_barrier = p.get("barriers",["Lack of guidance"])[0] if p.get("barriers") else "Lack of guidance"
    barrier = st.selectbox("What kind of barrier should the story speak to?", barrier_options, index=barrier_options.index(default_barrier) if default_barrier in barrier_options else 0)
    matched = [s for s in STORIES if barrier in s["barriers"]] or STORIES
    story_names = [s["person"] for s in matched]
    selected_name = st.selectbox("Choose a story", story_names)
    s = next(x for x in matched if x["person"] == selected_name)
    st.markdown(f"<div class='story'><h2>{s['person']} — {s['title']}</h2><p><b>Starting point.</b> {s['starting']}</p><p><b>Turning point.</b> {s['turning']}</p><p><b>What this shows.</b> {s['lesson']}</p><p><b>Do one thing now.</b> {s['action']}</p></div>", unsafe_allow_html=True)
    st.link_button("Open source", s["source_url"])
    action = st.text_area("Turn the story into your own next action", value=s["action"])
    if st.button("Save this action to my pathway", type="primary"):
        if action.strip() and action.strip() not in st.session_state.saved_actions:
            st.session_state.saved_actions.append(action.strip())
            sync_persistence()
        st.success("Saved to My Pathway.")

elif page == "Human Support":
    st.title("Human Support")
    st.write("AI can help navigate; it should not replace a qualified teacher, mentor or mental-health professional.")
    p = profile()
    with st.form("support_form"):
        kind = st.selectbox("What kind of human help do you need?", ["Academic mentor","Tutor","University application mentor","School support / safeguarding route"])
        lang = st.selectbox("Preferred language for support", LANGUAGES, index=LANGUAGES.index(p.get("language","English")) if p.get("language","English") in LANGUAGES else 0)
        detail = st.text_area("What would you like the mentor or professional to know?", placeholder="Example: I need help understanding graphs and planning weekly practice.")
        consent = st.checkbox("I understand this prototype does not create an unmoderated private adult-child chat.")
        submit = st.form_submit_button("Create safe support request", type="primary")
    if submit:
        if not consent:
            st.error("Confirm the safeguarding notice first.")
        elif not detail.strip():
            st.error("Add a short description of the support you need.")
        else:
            req_id = f"SUP-{random.randint(10000,99999)}"
            st.session_state.support_requests.append({"id":req_id,"kind":kind,"language":lang,"detail":detail,"created":datetime.utcnow().isoformat()})
            st.session_state.support_request_count += 1
            sync_persistence()
            st.success(f"Request {req_id} created in the prototype.")
    if st.session_state.support_requests:
        st.subheader("Requests created in this session")
        for r in reversed(st.session_state.support_requests[-5:]):
            st.write(f"• {r['id']} · {r['kind']} · {r['language']} · status: demo request created")
    st.caption(f"Persistent request counter: {st.session_state.support_request_count}")

elif page == "Community":
    st.title("Community — moderated, not open DMs")
    st.write("Topic rooms use pseudonyms and moderation. Contact details are blocked before submission. Child-to-child and adult-to-child private messaging are not part of this MVP.")
    topics = ["All","Math","English","Coding","Study skills","Applications","Motivation"]
    room = st.selectbox("Topic room", topics)
    shown = [p for p in COMMUNITY_POSTS if room == "All" or p[1] == room]
    for name,topic,text in shown:
        st.markdown(f"<div class='card'><b>{name}</b> · <span class='muted'>{topic}</span><p>{text}</p><span class='tiny'>Verified peer tip in prototype dataset</span></div>", unsafe_allow_html=True)
        st.write("")
    st.subheader("Ask the community")
    with st.form("community_form"):
        topic = st.selectbox("Topic", topics[1:])
        question = st.text_area("Your question", placeholder="Do not include your real name, phone number, email, address, school name or social-media handle.")
        send = st.form_submit_button("Send to moderation")
    if send:
        findings = pii_findings(question)
        if findings:
            st.error("Not submitted. Remove personal contact information before sending: " + ", ".join(findings) + ".")
        elif len(question.strip()) < 8:
            st.error("Write a little more so moderators can understand the question.")
        else:
            st.session_state.community_submissions.append({"topic":topic,"question":question.strip(),"status":"pending moderation"})
            st.success("Submitted for moderation. It is not published automatically.")
    if st.session_state.community_submissions:
        st.caption(f"Pending moderation in this session: {len(st.session_state.community_submissions)}")

elif page == "Opportunities":
    st.title("Opportunities")
    st.write("This section separates actions you can do inside Opportunity Navigator from real external providers. External links are optional and secondary, but they now open directly when you choose to verify or apply.")
    st.subheader("Your next actions")
    st.markdown("<div class='path-step'><b>Build an application evidence portfolio</b><br><span class='muted'>Create evidence categories for projects, research, volunteering and measurable results.</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='path-step'><b>Build an opportunity shortlist</b><br><span class='muted'>Save realistic options, compare eligibility and choose one application task for this week.</span></div>", unsafe_allow_html=True)
    if st.button("Open University Planner"):
        nav_to("University Planner")
    st.subheader("Opportunities for you")
    st.caption("Provider records are examples for the prototype. Always verify the current cycle, deadline and local eligibility on the official page.")
    cats = ["All"] + sorted({o["category"] for o in PROVIDER_OPPORTUNITIES})
    cat = st.selectbox("Category", cats)
    p = profile()
    ranked = []
    for o in PROVIDER_OPPORTUNITIES:
        if cat != "All" and o["category"] != cat:
            continue
        sc,reasons = score_opportunity(o,p)
        ranked.append((sc,reasons,o))
    ranked.sort(key=lambda x:x[0], reverse=True)
    for sc,reasons,o in ranked:
        pills = "".join([f"<span class='pill'>{x}</span>" for x in [o['category'],o['cost'],f"Ages {o['age_min']}–{o['age_max']}"]])
        st.markdown(f"### {o['name']}", unsafe_allow_html=True)
        st.markdown(pills, unsafe_allow_html=True)
        st.write(o["summary"])
        st.write("**Why this matches:** " + (", ".join(reasons) if reasons else "review manually against your profile"))
        st.write("**Eligibility:** " + o["eligibility"])
        with st.expander("Inside-platform preparation checklist"):
            for item in o["checklist"]:
                st.checkbox(item, key=f"check_{o['id']}_{item}")
        c1,c2 = st.columns(2)
        saved = o["id"] in st.session_state.saved_opportunities
        if c1.button("Saved ✓" if saved else "Save opportunity", key=f"save_{o['id']}", disabled=saved, use_container_width=True):
            st.session_state.saved_opportunities.add(o["id"]); sync_persistence(); st.rerun()
        with c2:
            st.link_button("Open official provider page ↗", o["url"], use_container_width=True)
        st.divider()

elif page == "University Planner":
    st.title("University Planner")
    st.write("Describe the country, university or course you are aiming for. The planner helps you find official pages, track exams and scores, prepare application writing and build a stronger evidence portfolio.")
    old = st.session_state.admissions_plan or {}
    with st.form("admissions_target"):
        c1,c2 = st.columns(2)
        with c1:
            target_country = st.selectbox("Target country", COUNTRIES, index=COUNTRIES.index(old.get("country","Global / not specified")) if old.get("country","Global / not specified") in COUNTRIES else 0)
            university = st.text_input("Target university (optional)", value=old.get("university",""), placeholder="Example: University name — or leave blank if you only know the country")
            program = st.text_input("Course / program", value=old.get("program",""), placeholder="Example: Computer Science")
        with c2:
            levels = ["Bachelor's / undergraduate","Foundation / pathway","Other"]
            old_level = old.get("level", levels[0])
            level = st.selectbox("Study level", levels, index=levels.index(old_level) if old_level in levels else 0)
            year = st.number_input("Target entry year", min_value=datetime.utcnow().year, max_value=datetime.utcnow().year+8, value=int(old.get("year", datetime.utcnow().year+2)))
            scholarship = st.checkbox("I need scholarship / financial aid", value=bool(old.get("scholarship",True)))
        official_url = st.text_input("Official admissions or course page URL (optional)", value=old.get("official_url",""), placeholder="https://...")
        save_plan = st.form_submit_button("Build / update my admissions plan", type="primary")
    if save_plan:
        st.session_state.admissions_plan = {
            "country":target_country,"university":university,"program":program,"level":level,
            "year":int(year),"scholarship":scholarship,"official_url":official_url,
        }
        sync_persistence(); st.success("Admissions target saved. The plan will remain available after refresh through the demo progress token.")

    plan = st.session_state.admissions_plan
    if plan:
        st.subheader("1. Find official information")
        st.info("Admission rules change. Use the planner to locate and organize information, but verify every requirement on an official university, testing-body or scholarship page before acting.")
        qmap = admissions_search_queries(plan)
        if st.button("Search the web for candidate official pages", type="primary"):
            research = {}
            try:
                with st.spinner("Searching for public pages..."):
                    for label, query in qmap.items():
                        research[label] = web_search_candidates(query, max_results=4)
                st.session_state["university_search_results"] = research
            except Exception as e:
                st.warning("Live search was unavailable. Use the direct search buttons below or paste an official page URL. " + str(e))
        results = st.session_state.get("university_search_results", {})
        for label, query in qmap.items():
            with st.expander(label, expanded=(label == "Course & entry requirements")):
                st.link_button("Open web search ↗", "https://www.google.com/search?q=" + quote_plus(query))
                rows = results.get(label, [])
                if rows:
                    st.caption("Candidate pages found by the prototype. Prefer the university's own domain and verify the page title/domain before using a requirement.")
                    for i,row in enumerate(rows, start=1):
                        st.markdown(f"**{i}. {row['title']}**")
                        st.link_button("Open page ↗", row["url"], key=f"search_{label}_{i}")
                elif results:
                    st.caption("No candidate page was returned for this query.")

        st.subheader("2. Requirements board")
        requirement_items = [
            "Exact course / major and intake", "Accepted school qualification", "Required school subjects",
            "Admissions test(s), if any", "English-language test and required score, if applicable",
            "Application deadline", "Essays / personal statement / motivation letter", "References / recommendations",
            "Portfolio / interview / extra assessment, if applicable", "Scholarship or financial-aid deadline",
        ]
        checked_now = set()
        for idx,item in enumerate(requirement_items):
            val = st.checkbox(item, value=item in st.session_state.requirements_checked, key=f"req_v06_{idx}")
            if val:
                checked_now.add(item)
        if checked_now != st.session_state.requirements_checked:
            st.session_state.requirements_checked = checked_now
            sync_persistence()
        st.caption(f"Verified checklist progress: {len(checked_now)} / {len(requirement_items)}")

        if plan.get("official_url"):
            st.link_button("Open the official page ↗", plan["official_url"])
            if st.button("Extract requirement mentions from this page"):
                try:
                    with st.spinner("Reading the public page..."):
                        text = fetch_page_text(plan["official_url"])
                    mentions = extract_admission_mentions(text)
                    if not mentions:
                        st.warning("The page loaded, but clear requirement keywords were not found. Try a more specific admissions/course page.")
                    else:
                        st.session_state["admission_mentions"] = mentions
                except Exception as e:
                    st.error("Could not read that page. Try the direct public admissions/course URL. " + str(e))
            mentions = st.session_state.get("admission_mentions",{})
            for label, snippets in mentions.items():
                with st.expander("Extracted: " + label):
                    for sn in snippets:
                        st.write("•", sn)

        st.subheader("3. Preparation courses / skills")
        st.write("These are preparation areas inferred from the program name — not official prerequisites. Use them to decide what to strengthen while you verify the real course requirements.")
        for item in program_foundation(plan.get("program","")):
            st.write("•", item)
        prep_query = " ".join(x for x in [plan.get("program",""), plan.get("country","")] if x and x != "Global / not specified") + " free online preparation course"
        st.link_button("Search preparation courses ↗", "https://www.google.com/search?q=" + quote_plus(prep_query))

        st.subheader("4. Exam & score tracker")
        st.write("Record a score only after checking an official source. The planner deliberately does not invent a minimum score.")
        with st.form("exam_tracker_form", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            with c1:
                exam_name = st.text_input("Exam / qualification", placeholder="IELTS / TOEFL / SAT / IB / A-level / local exam")
            with c2:
                exam_required = st.text_input("Official required / competitive score", placeholder="Paste the verified number")
            with c3:
                exam_current = st.text_input("Your current score", placeholder="Optional")
            exam_source = st.text_input("Official source URL", placeholder="https://...")
            add_exam = st.form_submit_button("Add verified exam requirement")
        if add_exam:
            if not exam_name.strip():
                st.error("Add the exam or qualification name.")
            elif exam_source.strip() and not is_safe_public_url(exam_source.strip()):
                st.error("Use a public http/https source URL.")
            else:
                st.session_state.exam_tracker.append({
                    "exam":exam_name.strip(), "required":exam_required.strip(),
                    "current":exam_current.strip(), "source":exam_source.strip(),
                })
                sync_persistence(); st.rerun()
        if st.session_state.exam_tracker:
            for i,row in enumerate(st.session_state.exam_tracker, start=1):
                st.markdown(f"<div class='card'><b>{i}. {row['exam']}</b><br><span class='muted'>Required / competitive:</span> {row['required'] or 'not recorded'}<br><span class='muted'>Current:</span> {row['current'] or 'not recorded'}</div>", unsafe_allow_html=True)
                if row.get("source"):
                    st.link_button("Open source ↗", row["source"], key=f"exam_source_{i}")
                st.write("")

        st.subheader("5. Motivation letter builder")
        st.write("Build the letter from evidence rather than generic praise. The strongest draft usually connects motivation → evidence → reflection → specific fit → next step.")
        why = st.text_area("Why this course?", placeholder="What problem, subject or question keeps your attention?")
        evidence = st.text_area("Best evidence", placeholder="Describe one project/activity: your role, result, proof and what changed after feedback.")
        reflection = st.text_area("What did you learn or change?", placeholder="What assumption changed? What skill became stronger? What would you do differently now?")
        future = st.text_area("Why this university and what next?", placeholder="Connect specific course features to what you want to learn, research or build next.")
        if any(x.strip() for x in [why,evidence,reflection,future]):
            draft = (
                f"I am applying to {plan.get('program') or 'this program'} at {plan.get('university') or 'this university'} because {why.strip()}\n\n"
                f"The strongest evidence of my preparation is {evidence.strip()}\n\n"
                f"This experience changed my thinking because {reflection.strip()}\n\n"
                f"This program is a strong next step for me because {future.strip()}"
            )
            st.text_area("Structured first draft", value=draft, height=260)
            checks = {
                "specific course motivation": len(why.strip()) >= 40,
                "concrete evidence / personal role": len(evidence.strip()) >= 60,
                "reflection / learning": len(reflection.strip()) >= 40,
                "specific university fit / next step": len(future.strip()) >= 50,
            }
            st.write("**Draft strength check:**")
            for label,ok in checks.items():
                st.write(("✅" if ok else "⬜") + " " + label)
            st.download_button("Download draft as text", draft, file_name="motivation_letter_draft.txt", mime="text/plain")

        st.subheader("6. Portfolio evidence tracker")
        st.write("There is no universal required number of achievements. A stronger portfolio usually shows depth and proof across a few meaningful areas rather than a long list of vague activities.")
        st.markdown("**Useful evidence categories:** academic depth · project/research · initiative/leadership · service/community · reflection/iteration.")
        with st.form("portfolio_add"):
            p_title = st.text_input("Evidence item", placeholder="Project, research, volunteering, competition, initiative...")
            p_role = st.text_input("What did you personally do?")
            p_result = st.text_input("Result / impact / measurable outcome")
            p_proof = st.text_input("Proof", placeholder="Link, file, certificate, feedback, data, reflection")
            add = st.form_submit_button("Add evidence item")
        if add and p_title.strip():
            st.session_state.portfolio_items.append({"title":p_title,"role":p_role,"result":p_result,"proof":p_proof})
            st.rerun()
        if st.session_state.portfolio_items:
            st.caption(f"Evidence items in this session: {len(st.session_state.portfolio_items)}. Quality and relevance matter more than reaching a fixed number.")
            for i,item in enumerate(st.session_state.portfolio_items, start=1):
                st.markdown(f"<div class='card'><b>{i}. {item['title']}</b><br><span class='muted'>Role:</span> {item['role']}<br><span class='muted'>Result:</span> {item['result']}<br><span class='muted'>Proof:</span> {item['proof']}</div>", unsafe_allow_html=True)
                st.write("")

elif page == "About the Project":
    st.title("About the project")
    st.subheader("What changed after testing")
    st.markdown("""
1. **Global profile fields:** country and language use broad searchable lists.
2. **Navigation:** profile → “Open my pathway” changes the page correctly, and the current page can be restored after refresh.
3. **AI Tutor:** learners choose subject + topic, describe the exact stuck point, ask repeated follow-up questions, request simpler explanations/hints/examples and check understanding.
4. **Adaptive Learning Hub:** lessons start with three core questions; mistakes add extra practice automatically and every wrong answer includes an explanation.
5. **Motivation:** richer barrier-matched stories include starting point, turning point, evidence and one action that can be saved to the pathway.
6. **Community safety:** phone numbers, emails and social handles are blocked before moderation submission.
7. **Opportunities:** saved-item counters persist and official provider links open directly.
8. **University planning:** learners can enter a country/university/course, search for candidate official pages, extract requirement mentions, track verified exams/scores, build a motivation-letter draft and organize portfolio evidence.
9. **Refresh persistence:** non-sensitive profile selections, lesson progress, saved opportunities, support counters, admissions targets and exam tracker survive refresh through a compact state token; export/import is also available.
    """)
    st.subheader("Product principle")
    st.markdown("<div class='notice'><b>Do not make a teenager assemble the solution alone.</b> Learning, tutoring, motivation, support, community, admissions planning and opportunity navigation should work as one pathway.</div>", unsafe_allow_html=True)
    st.subheader("What is still a prototype")
    st.markdown("""
- the AI tutor uses deterministic teaching logic, not a live generative model;
- live mentor matching is simulated, not connected to a partner network;
- community moderation is demonstrated in-session, not backed by a production database;
- web search and admissions-page extraction are research aids, not a guaranteed complete admissions database;
- free-text support/community/essay content is intentionally not stored in the URL persistence token;
- production deployment would need authenticated accounts, a database, moderation infrastructure and safeguarding review.
    """)
