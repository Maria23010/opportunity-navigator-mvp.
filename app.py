
import random
import re
from datetime import datetime
import streamlit as st

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

VERSION = "0.4"

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
    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 5rem; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#101827 0%,#1c2944 100%);
    }
    [data-testid="stSidebar"] * { color: #f8fafc; }
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        justify-content: flex-start;
        border: 0;
        border-radius: 10px;
        background: transparent;
        color: #f8fafc;
        min-height: 42px;
        font-weight: 650;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,.10);
        border: 0;
        color: #ffffff;
    }
    .site-title { font-size:1.30rem; font-weight:800; margin-bottom:.1rem; }
    .site-sub { font-size:.84rem; opacity:.72; margin-bottom:1rem; }
    .hero {
        border-radius: 28px;
        padding: 42px 44px;
        background: linear-gradient(115deg,#244be8 0%,#1765ea 55%,#28a9ec 100%);
        color:white;
        box-shadow: 0 18px 55px rgba(32,77,180,.18);
        margin-bottom: 24px;
    }
    .hero .eyebrow {
        font-weight:800; letter-spacing:.12em; text-transform:uppercase;
        font-size:.76rem; opacity:.85; margin-bottom:16px;
    }
    .hero h1 { font-size:3.15rem; line-height:1.03; margin:0 0 20px 0; color:white; }
    .hero p { font-size:1.08rem; line-height:1.65; max-width:900px; opacity:.96; }
    .feature-card, .card {
        border:1px solid var(--line); border-radius:20px; padding:22px 24px;
        background:var(--surface); height:100%;
    }
    .feature-card .label {
        color:#789; font-weight:800; text-transform:uppercase;
        letter-spacing:.10em; font-size:.72rem; margin-bottom:10px;
    }
    .feature-card h3 { margin:.2rem 0 .5rem 0; }
    .muted { color:var(--muted); }
    .notice {
        border:1px solid #dbeafe; border-radius:14px; background:#eff6ff;
        padding:14px 16px; margin:12px 0 18px 0;
    }
    .successbox {
        border:1px solid #d1fae5; border-radius:14px; background:#ecfdf5;
        padding:14px 16px; margin:12px 0;
    }
    .warnbox {
        border:1px solid #fde68a; border-radius:14px; background:#fffbeb;
        padding:14px 16px; margin:12px 0;
    }
    .story {
        border-left:5px solid #2155f3; border-radius:16px; background:#f8fbff;
        padding:22px 24px; margin:12px 0;
    }
    .path-step {
        border-left:5px solid #2155f3; border-radius:16px; border-top:1px solid #e5e7eb;
        border-right:1px solid #e5e7eb; border-bottom:1px solid #e5e7eb;
        padding:18px 20px; margin:12px 0; background:#fff;
    }
    .pill {
        display:inline-block; padding:4px 9px; border-radius:999px;
        background:#edf2ff; color:#244be8; font-size:.78rem; font-weight:700;
        margin:0 6px 6px 0;
    }
    .tiny { font-size:.78rem; color:#6b7280; }
    .section-head { margin-top: 8px; margin-bottom: 4px; }
    div[data-testid="stMetric"] {
        border:1px solid #e5e7eb; padding:12px 16px; border-radius:16px; background:white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Reference data --------------------
COMMON_COUNTRIES = [
    "Kazakhstan", "Russia", "United Arab Emirates", "United States",
    "United Kingdom", "Türkiye", "Uzbekistan", "Kyrgyzstan", "Norway"
]
if pycountry:
    _all_countries = sorted({c.name for c in pycountry.countries})
else:
    _all_countries = COMMON_COUNTRIES[:]
COUNTRIES = ["Global / not specified"] + [x for x in COMMON_COUNTRIES if x in _all_countries]
COUNTRIES += [x for x in _all_countries if x not in COUNTRIES]

COMMON_LANGS = [
    "English", "Russian", "Kazakh", "Turkish", "Arabic", "Chinese",
    "Spanish", "French", "German", "Portuguese", "Korean", "Japanese",
    "Hindi", "Uzbek", "Ukrainian"
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
    "Improve school grades",
    "Understand mathematics",
    "Learn English",
    "Learn coding",
    "Prepare for SAT / international exams",
    "Prepare for university applications",
    "Find scholarships and opportunities",
    "Build confidence and study habits",
]
BARRIERS = [
    "Lack of guidance",
    "Financial limits",
    "Low confidence",
    "I do not know where to start",
    "Limited access to tutoring",
    "Language barrier",
    "Limited device / internet access",
    "School stress or bullying",
]
SUPPORT_PREFS = ["Mostly self-study", "Mostly human support", "A mix of both"]
ACCESS_NEEDS = ["Free only", "Works on a phone", "Low-bandwidth friendly", "Downloadable/offline materials"]

# -------------------- Content: lessons --------------------
MODULES = {
    "Linear equations without guessing": {
        "subject": "Math",
        "minutes": 12,
        "intro": "Learn to isolate the unknown by undoing operations in reverse order.",
        "exercises": [
            {
                "q": "Solve: x + 7 = 12",
                "options": ["3", "5", "7", "19"],
                "answer": "5",
                "explanation": "Subtract 7 from both sides: x = 12 − 7 = 5.",
            },
            {
                "q": "Solve: 3x = 18",
                "options": ["3", "6", "15", "54"],
                "answer": "6",
                "explanation": "Divide both sides by 3: x = 18 ÷ 3 = 6.",
            },
            {
                "q": "Solve: 2x + 3 = 11",
                "options": ["3", "4", "5", "7"],
                "answer": "4",
                "explanation": "First subtract 3: 2x = 8. Then divide by 2: x = 4.",
            },
            {
                "q": "Solve: 5x − 10 = 20",
                "options": ["2", "4", "6", "10"],
                "answer": "6",
                "explanation": "Add 10: 5x = 30. Divide by 5: x = 6.",
            },
        ],
    },
    "Percentages in real life": {
        "subject": "Math",
        "minutes": 10,
        "intro": "Convert the percentage to a decimal or fraction, then multiply.",
        "exercises": [
            {
                "q": "What is 20% of 150?",
                "options": ["15", "20", "30", "75"],
                "answer": "30",
                "explanation": "20% = 0.20, so 0.20 × 150 = 30.",
            },
            {
                "q": "A $40 item is discounted by 25%. What is the discount?",
                "options": ["$5", "$10", "$15", "$30"],
                "answer": "$10",
                "explanation": "25% of 40 = 0.25 × 40 = 10.",
            },
            {
                "q": "A score rises from 60 to 75. By what percentage did it increase?",
                "options": ["15%", "20%", "25%", "30%"],
                "answer": "25%",
                "explanation": "Increase = 15. Divide by the original 60: 15/60 = 0.25 = 25%.",
            },
        ],
    },
    "A / an / the in two rules": {
        "subject": "English",
        "minutes": 10,
        "intro": "Use a/an for one non-specific thing; use the when the listener knows which one.",
        "exercises": [
            {
                "q": "I saw ___ elephant at the zoo.",
                "options": ["a", "an", "the", "—"],
                "answer": "an",
                "explanation": "Use 'an' before a vowel sound: an elephant.",
            },
            {
                "q": "Please close ___ door. (There is one obvious door.)",
                "options": ["a", "an", "the", "—"],
                "answer": "the",
                "explanation": "Use 'the' when both people know which specific door is meant.",
            },
            {
                "q": "She wants to buy ___ laptop, but she has not chosen one yet.",
                "options": ["a", "an", "the", "—"],
                "answer": "a",
                "explanation": "The laptop is not specific yet, so use 'a'.",
            },
        ],
    },
    "Remember vocabulary with retrieval": {
        "subject": "English",
        "minutes": 8,
        "intro": "Retrieval practice means trying to recall before looking at the answer.",
        "exercises": [
            {
                "q": "Which method best uses retrieval practice?",
                "options": [
                    "Re-read the same list five times",
                    "Cover the answer and try to recall it",
                    "Highlight every word",
                    "Copy the list without testing yourself",
                ],
                "answer": "Cover the answer and try to recall it",
                "explanation": "Retrieval practice strengthens memory by forcing recall, not just recognition.",
            },
            {
                "q": "When should you review a word you almost forgot?",
                "options": ["Never", "Only after a month", "Soon, then again later", "Only once"],
                "answer": "Soon, then again later",
                "explanation": "Spaced retrieval works best when reviews are repeated over increasing intervals.",
            },
            {
                "q": "What makes a useful flashcard?",
                "options": [
                    "One clear prompt and one answer",
                    "A whole textbook page",
                    "Five unrelated questions",
                    "Only a highlighted word",
                ],
                "answer": "One clear prompt and one answer",
                "explanation": "A focused cue makes recall measurable and reduces ambiguity.",
            },
        ],
    },
    "Loops as repetition": {
        "subject": "Coding",
        "minutes": 12,
        "intro": "A loop repeats a block of instructions while a rule or range tells it how long.",
        "exercises": [
            {
                "q": "In Python, how many times does `for i in range(3)` repeat?",
                "options": ["2", "3", "4", "It never stops"],
                "answer": "3",
                "explanation": "range(3) produces 0, 1, 2 — three values, so the loop runs three times.",
            },
            {
                "q": "Which idea best describes a loop?",
                "options": [
                    "Repeat instructions",
                    "Store one text value",
                    "Delete a file",
                    "Rename a variable",
                ],
                "answer": "Repeat instructions",
                "explanation": "Loops are used when the same action must happen multiple times.",
            },
            {
                "q": "What is the output count of `for x in [2,4,6,8]: print(x)`?",
                "options": ["2", "3", "4", "8"],
                "answer": "4",
                "explanation": "The list contains four items, so print runs four times.",
            },
        ],
    },
    "The 15-minute start": {
        "subject": "Study skills",
        "minutes": 7,
        "intro": "Reduce the activation barrier by defining a very small first action.",
        "exercises": [
            {
                "q": "Which is the best 15-minute goal?",
                "options": [
                    "Master all algebra",
                    "Open the chapter and solve two equations",
                    "Finish every assignment this month",
                    "Become fluent in English",
                ],
                "answer": "Open the chapter and solve two equations",
                "explanation": "A useful short goal is concrete, small and immediately startable.",
            },
            {
                "q": "If you get stuck after five minutes, what should you record?",
                "options": [
                    "The exact point where you became confused",
                    "Nothing",
                    "Only your final score",
                    "A general statement like 'I am bad at this'",
                ],
                "answer": "The exact point where you became confused",
                "explanation": "A precise stuck point makes it easier for a tutor, mentor or AI system to help.",
            },
            {
                "q": "What should happen after the 15-minute block?",
                "options": [
                    "Decide the next small step",
                    "Always study for three more hours",
                    "Delete your notes",
                    "Start a completely different goal",
                ],
                "answer": "Decide the next small step",
                "explanation": "The aim is continuity: finish with a clear next action rather than an overwhelming plan.",
            },
        ],
    },
    "Turn an ambition into an evidence list": {
        "subject": "University applications",
        "minutes": 15,
        "intro": "Strong applications are easier to write when activities are documented as evidence, role, result and reflection.",
        "exercises": [
            {
                "q": "Which note is strongest evidence?",
                "options": [
                    "I like volunteering",
                    "I volunteered weekly",
                    "I designed a language game used by 8 students and recorded their feedback",
                    "Volunteering is important",
                ],
                "answer": "I designed a language game used by 8 students and recorded their feedback",
                "explanation": "It shows a concrete action, your role, a measurable detail and evidence you can later verify.",
            },
            {
                "q": "What should you record after a project?",
                "options": [
                    "Only the project title",
                    "Your exact role, outcome and what changed after feedback",
                    "Only compliments",
                    "Nothing until you apply",
                ],
                "answer": "Your exact role, outcome and what changed after feedback",
                "explanation": "This makes future essays and interviews more specific and credible.",
            },
            {
                "q": "What is a useful reflection question?",
                "options": [
                    "What assumption did I change after testing?",
                    "How can I make this sound impressive?",
                    "How can I hide mistakes?",
                    "How can I add more adjectives?",
                ],
                "answer": "What assumption did I change after testing?",
                "explanation": "Reflection is strongest when it shows learning, iteration and changed thinking.",
            },
        ],
    },
}

# -------------------- Content: motivation --------------------
STORIES = [
    {
        "person": "Jan Koum",
        "title": "From limited resources to building WhatsApp",
        "barriers": ["Financial limits", "Lack of guidance", "I do not know where to start"],
        "starting": (
            "Koum moved to the United States as a teenager and grew up with limited financial resources. "
            "His early path into technology was not a straight, carefully planned route."
        ),
        "turning": (
            "He taught himself computing skills, worked in technology, and later co-founded WhatsApp. "
            "The useful part of the story is not the scale of the company; it is the sequence: learn one skill, "
            "use it in a real environment, notice a communication problem, then build around that problem."
        ),
        "lesson": (
            "You do not need a complete ten-year plan before taking a useful step. A small skill can become a bridge "
            "to the next opportunity when you keep turning learning into evidence."
        ),
        "action": "Choose one skill your current goal requires and complete one free, concrete learning task for it today.",
        "source_label": "Britannica biography",
        "source_url": "https://www.britannica.com/biography/Jan-Koum",
    },
    {
        "person": "José Hernández",
        "title": "A long path to becoming an astronaut",
        "barriers": ["Low confidence", "Lack of guidance", "Financial limits"],
        "starting": (
            "Hernández grew up in a migrant farmworker family and spent part of his childhood moving with seasonal work. "
            "The environment around him did not make an aerospace career feel automatic or nearby."
        ),
        "turning": (
            "He built the prerequisites step by step: education, engineering experience, repeated applications, "
            "and continued skill development. His progress came from converting a distant ambition into requirements "
            "he could work on one at a time."
        ),
        "lesson": (
            "A goal can stay realistic even when it is far away if you can identify the next requirement. "
            "The question changes from 'Can I become that?' to 'What is the next piece I can build?'"
        ),
        "action": "Write one long-term goal, then list the next three requirements. Pick the smallest requirement and act on it.",
        "source_label": "NASA biography",
        "source_url": "https://www.nasa.gov/people/jose-hernandez/",
    },
    {
        "person": "Sara Blakely",
        "title": "Using rejection as information",
        "barriers": ["Low confidence", "I do not know where to start"],
        "starting": (
            "Before founding Spanx, Blakely worked in sales and faced repeated rejection. She did not begin as a fashion "
            "industry insider with a ready-made network."
        ),
        "turning": (
            "She treated rejection as part of the process rather than proof that the idea had no value. "
            "She learned what she needed, kept refining the product, and persisted through conversations where others "
            "did not immediately understand the concept."
        ),
        "lesson": (
            "Failure becomes more useful when it produces information. A rejected attempt can tell you what to change, "
            "which skill is missing, or how to explain the idea better."
        ),
        "action": "Take one recent failure and write: What did it reveal? What is one change I can test next?",
        "source_label": "Spanx founder story",
        "source_url": "https://spanx.com/pages/about-us",
    },
    {
        "person": "Malala Yousafzai",
        "title": "Education as an action, not only an aspiration",
        "barriers": ["School stress or bullying", "Low confidence", "Lack of guidance"],
        "starting": (
            "Yousafzai became known internationally through her advocacy for girls' education in circumstances where "
            "access to schooling itself was under threat."
        ),
        "turning": (
            "Her story shows that education can be both a personal goal and a system-level issue. "
            "She continued learning while also using writing and public advocacy to make the barrier visible."
        ),
        "lesson": (
            "When a barrier is structural, the answer is not always 'try harder.' Sometimes progress also requires "
            "finding allies, safer routes, institutions, or communities that can change the conditions around you."
        ),
        "action": "Name one barrier that cannot be solved by effort alone. Identify one person, institution or support route that could reduce it.",
        "source_label": "Nobel Prize biography",
        "source_url": "https://www.nobelprize.org/prizes/peace/2014/yousafzai/biographical/",
    },
]

# -------------------- Content: community --------------------
COMMUNITY_POSTS = [
    ("Nova15", "Math", "I used to freeze when I saw functions. Drawing the graph first made the formula less scary."),
    ("Orbit16", "Study skills", "I study in 20-minute blocks because long sessions made me give up. Short sessions finally became a habit."),
    ("Mira14", "English", "Reading one short article aloud each day helped me stop being afraid of pronunciation mistakes."),
    ("Atlas16", "Applications", "I keep one evidence document with projects, results and what I personally did. Essay writing became much easier."),
    ("Pixel15", "Coding", "When code fails, I change one thing at a time. It is slower than guessing but I actually understand the bug."),
]

# -------------------- Content: opportunities --------------------
PROVIDER_OPPORTUNITIES = [
    {
        "id": "nyas-junior-academy",
        "name": "The Junior Academy — New York Academy of Sciences",
        "category": "STEM program",
        "cost": "Free",
        "countries": ["Global"],
        "languages": ["English"],
        "age_min": 13,
        "age_max": 17,
        "goals": ["Learn coding", "Prepare for university applications", "Find scholarships and opportunities"],
        "summary": "Online project-based STEM challenges with international teams and STEM mentors.",
        "eligibility": "Ages 13–17; online; English proficiency is required. Application cycles have deadlines.",
        "checklist": [
            "Check the current application cycle on the official page.",
            "Prepare a short explanation of your STEM interests.",
            "Collect one example of a project, investigation or problem you tried to solve.",
            "Plan enough weekly time for team collaboration if accepted.",
        ],
        "url": "https://www.nyas.org/learning/high-school-research-programs/the-junior-academy/",
    },
    {
        "id": "uwc-scholarships",
        "name": "UWC — scholarship route through a national committee",
        "category": "Scholarship / school opportunity",
        "cost": "Financial support available",
        "countries": ["Global"],
        "languages": ["English"],
        "age_min": 15,
        "age_max": 18,
        "goals": ["Prepare for university applications", "Find scholarships and opportunities"],
        "summary": "A route to UWC schools and colleges, with need-based financial support through national committees.",
        "eligibility": "Selection rules and timelines vary by national committee; students are typically 16 or 17 when beginning the IBDP/IBCP.",
        "checklist": [
            "Find the national committee for your country of residence or citizenship.",
            "Check the local age and deadline rules.",
            "Collect examples showing initiative, service, resilience and academic readiness.",
            "Review the financial-support process before choosing an application route.",
        ],
        "url": "https://uwc.org/how-to-apply/",
    },
    {
        "id": "schoolhouse",
        "name": "Schoolhouse.world",
        "category": "Free tutoring / admissions support",
        "cost": "Free",
        "countries": ["Global"],
        "languages": ["English"],
        "age_min": 13,
        "age_max": 19,
        "goals": ["Understand mathematics", "Prepare for SAT / international exams", "Prepare for university applications"],
        "summary": "Free peer-led tutoring, SAT support, homework help and college admissions workshops.",
        "eligibility": "Online access; specific programs may have their own requirements.",
        "checklist": [
            "Choose one concrete subject or admissions question.",
            "Prepare the exact point where you are stuck.",
            "Join one session that matches the goal.",
            "After the session, record one next step in your pathway.",
        ],
        "url": "https://schoolhouse.world/",
    },
]

# -------------------- Session state --------------------
defaults = {
    "page": "Home",
    "profile": None,
    "completed_modules": set(),
    "saved_opportunities": set(),
    "support_requests": [],
    "community_submissions": [],
    "tutor_session": None,
    "tutor_mode": "explain",
    "lesson_progress": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

NAV = [
    ("Home", "🏠"),
    ("My Pathway", "🧭"),
    ("AI Tutor", "🤖"),
    ("Learning Hub", "📚"),
    ("Motivation", "🌱"),
    ("Human Support", "🤝"),
    ("Community", "💬"),
    ("Opportunities", "🎓"),
    ("Profile", "👤"),
    ("About the Project", "ℹ️"),
]

def nav_to(name):
    st.session_state.page = name
    st.rerun()

def btn_nav(label, target, key, primary=False):
    if st.button(label, key=key, type="primary" if primary else "secondary", use_container_width=True):
        nav_to(target)

# -------------------- Sidebar --------------------
st.sidebar.markdown("<div class='site-title'>🧭 Opportunity Navigator</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='site-sub'>One place to learn, plan, connect and move forward.</div>", unsafe_allow_html=True)

for name, icon in NAV:
    label = f"{'🔵' if st.session_state.page == name else '⚪'}  {icon} {name}"
    if st.sidebar.button(label, key=f"nav_{name}", use_container_width=True):
        st.session_state.page = name
        st.rerun()

st.sidebar.markdown("---")
if st.session_state.profile:
    p = st.session_state.profile
    st.sidebar.caption(f"Profile: age {p['age']} · {p['country']} · {p['language']}")
else:
    st.sidebar.caption("Create a profile to personalize the platform.")
st.sidebar.caption(f"Prototype v{VERSION}")

# -------------------- Helpers --------------------
def profile():
    return st.session_state.profile or {}

def main_goal():
    goals = profile().get("goals", [])
    return goals[0] if goals else "Build a useful next step"

def primary_barrier():
    barriers = profile().get("barriers", [])
    return barriers[0] if barriers else "Lack of guidance"

def tutor_pack(subject, topic, help_style="Explain it simply", mode="explain"):
    t = (topic or "").strip().lower()

    if subject == "Math":
        if any(k in t for k in ["linear", "equation", "algebra", "x"]):
            base = {
                "diagnosis": "The key idea is to keep both sides of an equation balanced while you isolate x.",
                "simple": "Undo operations in reverse order. If something is added, subtract it. If x is multiplied, divide.",
                "hint": "For 2x + 3 = 11, remove +3 first. What remains on the left?",
                "example": "Example: 3x + 6 = 18 → subtract 6 → 3x = 12 → divide by 3 → x = 4.",
                "check": "Try this: solve 2x + 3 = 11.",
                "answer": "4",
                "explain_answer": "Subtract 3 from both sides to get 2x = 8, then divide by 2.",
            }
        elif any(k in t for k in ["percent", "%", "percentage"]):
            base = {
                "diagnosis": "Percent means 'out of 100', so you can convert it to a decimal and multiply.",
                "simple": "20% = 0.20. To find 20% of 150, calculate 0.20 × 150.",
                "hint": "Move the decimal two places left: 20% becomes 0.20.",
                "example": "Example: 15% of 80 = 0.15 × 80 = 12.",
                "check": "Try this: what is 20% of 150?",
                "answer": "30",
                "explain_answer": "0.20 × 150 = 30.",
            }
        else:
            base = {
                "diagnosis": f"You said you are stuck on: {topic or 'a math topic'}. First we need to locate the exact step that feels unclear.",
                "simple": "Write one example problem. Then mark the first line where you stop knowing what to do.",
                "hint": "Do not solve the whole problem at once. Name the operation or rule needed for only the next line.",
                "example": "A useful pattern is: identify what is known → identify what is unknown → choose one rule → check the result.",
                "check": "In one sentence, what is the first step you do not understand?",
                "answer": None,
                "explain_answer": "The goal is to identify the exact stuck point so the explanation can target it.",
            }

    elif subject == "English":
        if any(k in t for k in ["article", "a/an", "a an", "the"]):
            base = {
                "diagnosis": "Articles become easier if you ask two questions: Is it one thing? Is it specific?",
                "simple": "Use a/an for one non-specific thing. Use the when both people know which specific thing you mean.",
                "hint": "Listen to the sound, not only the letter: 'an elephant', but 'a university' because university starts with a /y/ sound.",
                "example": "I saw a dog. The dog was wet. First mention: a dog. Second mention: the dog.",
                "check": "Choose the missing word: 'I saw ___ elephant.'",
                "answer": "an",
                "explain_answer": "Elephant begins with a vowel sound, so use 'an'.",
            }
        else:
            base = {
                "diagnosis": f"Your English question is about: {topic or 'a topic you want to improve'}.",
                "simple": "Start with one real sentence that confuses you rather than a whole grammar chapter.",
                "hint": "Compare two examples and ask what changes between them.",
                "example": "For vocabulary, recall the word before looking. For grammar, create one correct example and one contrast.",
                "check": "Write one example sentence that you are unsure about.",
                "answer": None,
                "explain_answer": "A concrete sentence lets the tutor explain the rule in context.",
            }

    elif subject == "Coding":
        base = {
            "diagnosis": f"You are working on: {topic or 'a coding concept'}. The fastest route is to reduce it to input → rule → output.",
            "simple": "Read the code one line at a time and say what changes after each line.",
            "hint": "If a loop is confusing, write the values it will visit before thinking about the full program.",
            "example": "for i in range(3) uses i = 0, then 1, then 2: three repetitions.",
            "check": "How many times does `for i in range(3)` repeat?",
            "answer": "3",
            "explain_answer": "range(3) contains 0, 1 and 2 — three values.",
        }

    else:
        base = {
            "diagnosis": f"You are trying to understand: {topic or 'a topic'}.",
            "simple": "Break the topic into one claim, one example and one question you can test.",
            "hint": "Ask: what do I already know, and what is the first missing connection?",
            "example": "A good study note uses: concept → example → why it works → one self-check question.",
            "check": "What is the first part you cannot explain in your own words?",
            "answer": None,
            "explain_answer": "That answer identifies where the next explanation should begin.",
        }

    if mode == "hint":
        focus = base["hint"]
    elif mode == "example":
        focus = base["example"]
    elif mode == "simpler":
        focus = base["simple"]
    else:
        focus = base["simple"]

    if help_style == "Guide me with hints":
        focus = base["hint"]
    elif help_style == "Show an example":
        focus = base["example"]

    return base, focus

def score_opportunity(o, p):
    score = 0
    reasons = []
    age = p.get("age", 15)
    if o["age_min"] <= age <= o["age_max"]:
        score += 3
        reasons.append("fits your age")
    country = p.get("country", "Global / not specified")
    if "Global" in o["countries"] or country in o["countries"]:
        score += 2
        reasons.append("available globally / in your region")
    goals = set(p.get("goals", []))
    overlap = goals.intersection(o["goals"])
    if overlap:
        score += 3 + len(overlap)
        reasons.append("matches your goal")
    if "Free only" in p.get("access", []) and o["cost"] == "Free":
        score += 2
        reasons.append("free")
    lang = p.get("language", "English")
    other = p.get("other_languages", [])
    if lang in o["languages"] or any(x in o["languages"] for x in other):
        score += 1
        reasons.append("language match")
    return score, reasons

# -------------------- Pages --------------------
page = st.session_state.page

# HOME
if page == "Home":
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Research-driven social mobility platform</div>
          <h1>Your next step should not depend on knowing where to look.</h1>
          <p>Opportunity Navigator combines learning, tutoring, motivation, safe human support,
          community and opportunity discovery in one place — so a teenager does not have to
          assemble a support system alone.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div class='feature-card'><div class='label'>Learn</div><h3>AI Tutor + Learning Hub</h3>"
            "<p class='muted'>Explain a stuck point, practise several questions and see why an answer was wrong.</p></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            "<div class='feature-card'><div class='label'>Navigate</div><h3>Personal pathway</h3>"
            "<p class='muted'>Turn goals, barriers, language and access constraints into a short set of useful actions.</p></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            "<div class='feature-card'><div class='label'>Connect safely</div><h3>Human support + community</h3>"
            "<p class='muted'>Request a vetted mentor route or use moderated topic spaces without open private DMs.</p></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        if st.session_state.profile:
            btn_nav("Continue my pathway", "My Pathway", "home_path", primary=True)
        else:
            btn_nav("Build my profile", "Profile", "home_profile", primary=True)
    with b2:
        btn_nav("Explore the Learning Hub", "Learning Hub", "home_learn")

    st.markdown("### One platform, not another directory")
    st.write(
        "The core experience happens inside Opportunity Navigator. External providers are a secondary layer "
        "for opportunities or specialist support that cannot realistically happen inside one prototype."
    )

# PROFILE
elif page == "Profile":
    st.title("Build your learner & access profile")
    st.caption("Country and language fields are searchable. Start typing to jump to a value.")
    old = st.session_state.profile or {}

    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.slider("Age", 12, 19, int(old.get("age", 15)))
            country_default = old.get("country", "Global / not specified")
            country = st.selectbox(
                "Country / region",
                COUNTRIES,
                index=COUNTRIES.index(country_default) if country_default in COUNTRIES else 0,
            )
            lang_default = old.get("language", "English")
            language = st.selectbox(
                "Preferred language",
                LANGUAGES,
                index=LANGUAGES.index(lang_default) if lang_default in LANGUAGES else 0,
            )
            other_languages = st.multiselect(
                "Other languages you can use",
                LANGUAGES,
                default=old.get("other_languages", []),
            )
        with c2:
            goals = st.multiselect(
                "What do you want to work on?",
                GOALS,
                default=old.get("goals", ["Understand mathematics"]),
            )
            barriers = st.multiselect(
                "What makes progress harder right now?",
                BARRIERS,
                default=old.get("barriers", ["Lack of guidance"]),
            )
            support = st.selectbox(
                "Preferred support",
                SUPPORT_PREFS,
                index=SUPPORT_PREFS.index(old.get("support", "A mix of both"))
                if old.get("support", "A mix of both") in SUPPORT_PREFS
                else 2,
            )
            access = st.multiselect(
                "Access needs",
                ACCESS_NEEDS,
                default=old.get("access", ["Free only", "Works on a phone"]),
            )

        current_need = st.text_input(
            "What do you need help with today?",
            value=old.get("current_need", ""),
            placeholder="Example: I do not understand linear equations and I need a plan for university preparation.",
        )
        submitted = st.form_submit_button("Save profile and build my pathway", type="primary", use_container_width=True)

    if submitted:
        st.session_state.profile = {
            "age": age,
            "country": country,
            "language": language,
            "other_languages": other_languages,
            "goals": goals or ["Improve school grades"],
            "barriers": barriers or ["Lack of guidance"],
            "support": support,
            "access": access,
            "current_need": current_need,
        }
        st.success("Profile saved. Your pathway has been rebuilt.")

    if st.session_state.profile:
        if st.button("Open my pathway", type="primary"):
            nav_to("My Pathway")

# PATHWAY
elif page == "My Pathway":
    st.title("My pathway")
    p = profile()
    if not p:
        st.info("Create your profile first so the pathway can use your goals, language and access constraints.")
        btn_nav("Create profile", "Profile", "path_create", primary=True)
    else:
        st.markdown(
            f"<div class='notice'><b>Today:</b> focus on one useful next step, not a long list. "
            f"Your main goal is <b>{main_goal()}</b>.</div>",
            unsafe_allow_html=True,
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Learning modules completed", len(st.session_state.completed_modules))
        m2.metric("Saved opportunities", len(st.session_state.saved_opportunities))
        m3.metric("Support requests", len(st.session_state.support_requests))

        steps = []
        need = p.get("current_need", "")
        if any("math" in g.lower() for g in p.get("goals", [])) or "algebra" in need.lower() or "math" in need.lower():
            steps.append(("AI Tutor", "Do one focused 15-minute math session inside the platform.", "AI Tutor"))
            steps.append(("Learning Hub", "Complete one short math lesson and review every explanation.", "Learning Hub"))
        elif any("english" in g.lower() for g in p.get("goals", [])):
            steps.append(("AI Tutor", "Bring one sentence or grammar point you do not understand.", "AI Tutor"))
            steps.append(("Learning Hub", "Complete one short English lesson and review the explanation.", "Learning Hub"))
        else:
            steps.append(("Learning Hub", "Complete one short lesson connected to your goal.", "Learning Hub"))

        if p.get("barriers"):
            steps.append(("Motivation", f"Read a story matched to '{p['barriers'][0]}' and choose one action.", "Motivation"))
        if p.get("support") != "Mostly self-study" or "Lack of guidance" in p.get("barriers", []):
            steps.append(("Human Support", "Create a structured request for an academic mentor or support route.", "Human Support"))
        if any("opportunit" in g.lower() or "university" in g.lower() for g in p.get("goals", [])):
            steps.append(("Opportunities", "Review personalized opportunity cards and save one realistic next option.", "Opportunities"))

        st.subheader("Today's path")
        for i, (title, text, target) in enumerate(steps[:5], 1):
            st.markdown(
                f"<div class='path-step'><b>{i}. {title}</b><br><span class='muted'>{text}</span></div>",
                unsafe_allow_html=True,
            )
            if st.button(f"Go to {title}", key=f"path_go_{i}_{title}"):
                nav_to(target)

        st.subheader("Why these steps?")
        st.write(
            "The pathway uses your selected goal, barriers, support preference and access constraints. "
            "This version deliberately uses transparent rules so you can see why each step appears. "
            "A later research phase can compare this baseline with a trained recommender."
        )

# AI TUTOR
elif page == "AI Tutor":
    st.title("AI Tutor — learning interface prototype")
    st.write(
        "Tell the tutor exactly what you do not understand. The prototype responds with a structured explanation, "
        "hint, example and check question instead of only sending you to another website."
    )

    with st.expander("Technical note for portfolio reviewers"):
        st.write(
            "This version demonstrates the tutoring workflow with deterministic lesson logic. "
            "It is not connected to a live generative model. The next technical phase is a safeguarded LLM/RAG layer "
            "with answer-quality, hallucination and age-appropriateness evaluation."
        )

    c1, c2 = st.columns([1, 1])
    with c1:
        subject = st.selectbox("Subject", ["Math", "English", "Coding", "Study skills", "University applications"])
        topic = st.text_input(
            "What do you not understand?",
            placeholder="Example: I do not understand why we subtract 3 first in 2x + 3 = 11",
        )
        tried = st.text_area(
            "What have you tried?",
            placeholder="Example: I tried moving the 3 but I do not understand why the sign changes.",
            height=100,
        )
    with c2:
        help_style = st.selectbox("How should the tutor help?", ["Explain it simply", "Guide me with hints", "Show an example"])
        confidence = st.slider("How confident do you feel about this topic?", 1, 5, 2)
        st.caption("The prototype uses this to choose a gentler or more direct starting point.")

    if st.button("Start tutoring session", type="primary"):
        if not topic.strip():
            st.warning("Write the exact point you do not understand first.")
        else:
            st.session_state.tutor_session = {
                "subject": subject,
                "topic": topic,
                "tried": tried,
                "style": help_style,
                "confidence": confidence,
            }
            st.session_state.tutor_mode = "explain"

    ts = st.session_state.tutor_session
    if ts:
        pack, focus = tutor_pack(ts["subject"], ts["topic"], ts["style"], st.session_state.tutor_mode)
        st.markdown("### 1. Locate the stuck point")
        st.markdown(f"<div class='card'>{pack['diagnosis']}</div>", unsafe_allow_html=True)

        st.markdown("### 2. Explanation")
        if ts["confidence"] <= 2:
            st.markdown(f"<div class='notice'><b>Start small:</b> {focus}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='notice'>{focus}</div>", unsafe_allow_html=True)

        a, b, c = st.columns(3)
        with a:
            if st.button("Explain more simply", use_container_width=True):
                st.session_state.tutor_mode = "simpler"
                st.rerun()
        with b:
            if st.button("Give me a hint", use_container_width=True):
                st.session_state.tutor_mode = "hint"
                st.rerun()
        with c:
            if st.button("Show another example", use_container_width=True):
                st.session_state.tutor_mode = "example"
                st.rerun()

        st.markdown("### 3. Check your understanding")
        st.write(pack["check"])
        with st.form("tutor_check"):
            learner_answer = st.text_input("Your answer / explanation")
            check = st.form_submit_button("Check my answer")
        if check:
            if pack["answer"] is None:
                if learner_answer.strip():
                    st.success("Good — you identified a concrete point. Use that sentence as the next tutoring prompt.")
                    st.info(pack["explain_answer"])
                else:
                    st.warning("Write one sentence so the tutor can target the next explanation.")
            else:
                normalized = learner_answer.strip().lower().replace(" ", "")
                expected = str(pack["answer"]).strip().lower().replace(" ", "")
                if normalized == expected:
                    st.success("Correct. Now explain in your own words why that step works.")
                else:
                    st.error("Not yet. Read the explanation below and try again.")
                    st.info(pack["explain_answer"])

# LEARNING HUB
elif page == "Learning Hub":
    st.title("Learning Hub")
    st.write("Short lessons and repeated practice live inside the platform. Every wrong answer now includes an explanation.")

    subjects = ["All"] + sorted({m["subject"] for m in MODULES.values()})
    chosen_subject = st.selectbox("Filter by subject", subjects)
    names = [name for name, m in MODULES.items() if chosen_subject == "All" or m["subject"] == chosen_subject]
    module_name = st.selectbox("Choose a lesson", names)
    module = MODULES[module_name]

    st.markdown(
        f"<div class='card'><b>{module_name}</b> · {module['minutes']} min<br>"
        f"<span class='muted'>{module['intro']}</span></div>",
        unsafe_allow_html=True,
    )

    idx = int(st.session_state.lesson_progress.get(module_name, 0))
    total = len(module["exercises"])

    if idx >= total:
        st.success("Lesson complete. You finished all practice questions.")
        st.session_state.completed_modules.add(module_name)
        if st.button("Restart this lesson"):
            st.session_state.lesson_progress[module_name] = 0
            st.rerun()
    else:
        st.progress(idx / total)
        st.caption(f"Question {idx + 1} of {total}")
        ex = module["exercises"][idx]
        st.subheader(ex["q"])
        answer = st.radio("Choose an answer", ex["options"], index=None, key=f"lesson_{module_name}_{idx}")
        feedback_key = f"feedback_{module_name}_{idx}"

        if st.button("Check answer", type="primary"):
            if answer is None:
                st.warning("Choose an answer first.")
            elif answer == ex["answer"]:
                st.success("Correct.")
                st.info(f"Why: {ex['explanation']}")
                st.session_state[feedback_key] = "correct"
            else:
                st.error("Not yet — use the explanation, then try the same question again.")
                st.info(f"Explanation: {ex['explanation']}")
                st.session_state[feedback_key] = "wrong"

        if st.session_state.get(feedback_key) == "correct":
            if st.button("Next question"):
                st.session_state.lesson_progress[module_name] = idx + 1
                st.session_state.pop(feedback_key, None)
                st.rerun()

# MOTIVATION
elif page == "Motivation":
    st.title("Motivation → evidence → action")
    st.write(
        "The purpose is not celebrity worship. A story should match a real barrier, show a turning point, "
        "and end with something the learner can do now."
    )

    default_barrier = primary_barrier()
    barrier = st.selectbox(
        "What kind of barrier should the story speak to?",
        BARRIERS,
        index=BARRIERS.index(default_barrier) if default_barrier in BARRIERS else 0,
    )
    matched = [s for s in STORIES if barrier in s["barriers"]]
    if not matched:
        matched = STORIES

    selected_name = st.selectbox("Choose a story", [s["person"] for s in matched])
    story = next(s for s in matched if s["person"] == selected_name)

    st.markdown(
        f"<div class='story'><h3>{story['person']} — {story['title']}</h3>"
        f"<p><b>Starting point.</b> {story['starting']}</p>"
        f"<p><b>Turning point.</b> {story['turning']}</p>"
        f"<p><b>What this shows.</b> {story['lesson']}</p>"
        f"<p><b>Do one thing now.</b> {story['action']}</p></div>",
        unsafe_allow_html=True,
    )
    st.link_button(f"Source: {story['source_label']}", story["source_url"])

    with st.form("motivation_action"):
        chosen_action = st.text_input(
            "Turn the story into your own next action",
            value=story["action"],
        )
        saved = st.form_submit_button("Save this action to my pathway")
    if saved and chosen_action.strip():
        st.session_state["motivation_action"] = chosen_action.strip()
        st.success("Saved. Your action is now part of this session's pathway.")

# HUMAN SUPPORT
elif page == "Human Support":
    st.title("Human Support")
    st.write("AI can help navigate; it should not replace a qualified teacher, mentor or mental-health professional.")

    with st.form("support_form"):
        kind = st.selectbox(
            "What kind of human help do you need?",
            ["Academic mentor", "University-application mentor", "Language tutor", "Career guidance", "Wellbeing / professional support route"],
        )
        default_lang = profile().get("language", "English")
        support_lang = st.selectbox(
            "Preferred language for support",
            LANGUAGES,
            index=LANGUAGES.index(default_lang) if default_lang in LANGUAGES else 0,
        )
        note = st.text_area(
            "What would you like the mentor or professional to know?",
            placeholder="Example: I understand equations until graphs begin. I want someone to show me how the two connect.",
        )
        consent = st.checkbox(
            "I understand this prototype does not create an unmoderated private adult-child chat."
        )
        submit_support = st.form_submit_button("Create safe support request", type="primary")

    if submit_support:
        if not consent:
            st.warning("Please confirm the safeguarding note before creating the request.")
        elif not note.strip():
            st.warning("Write a short description of what help you need.")
        else:
            rid = f"SUP-{random.randint(10000,99999)}"
            st.session_state.support_requests.append({
                "id": rid,
                "kind": kind,
                "language": support_lang,
                "note": note.strip(),
                "status": "demo request created",
                "created": datetime.utcnow().strftime("%Y-%m-%d"),
            })
            st.success(f"Request {rid} created in the prototype.")
            st.write(
                "**Production flow:** eligibility / safeguarding checks → matching with a vetted partner → "
                "scheduled, logged session → reporting and safeguarding controls."
            )

    if st.session_state.support_requests:
        st.subheader("My requests")
        for r in reversed(st.session_state.support_requests):
            st.write(f"• **{r['id']}** · {r['kind']} · {r['language']} · status: *{r['status']}*")

# COMMUNITY
elif page == "Community":
    st.title("Community — moderated, not open DMs")
    st.write(
        "The community is designed around topic rooms, pseudonyms and moderation. "
        "Child-to-child private messaging and adult-to-child private messaging are not part of this MVP."
    )

    topics = ["All", "Math", "English", "Coding", "Study skills", "Applications", "Motivation"]
    room = st.selectbox("Topic room", topics)
    for user, topic, text in COMMUNITY_POSTS:
        if room == "All" or room == topic:
            st.markdown(
                f"<div class='card'><b>{user}</b> · <span class='tiny'>{topic}</span>"
                f"<p>{text}</p><span class='tiny'>Verified peer tip in prototype dataset</span></div>",
                unsafe_allow_html=True,
            )
            st.write("")

    st.subheader("Ask the community")
    with st.form("community_form"):
        q_topic = st.selectbox("Topic", topics[1:])
        q = st.text_area(
            "Your question",
            placeholder="Do not include your real name, phone number, address, school name or social-media handle.",
        )
        send = st.form_submit_button("Send to moderation")
    if send:
        if len(q.strip()) < 8:
            st.warning("Write a little more detail so the question can be useful.")
        else:
            st.session_state.community_submissions.append({
                "topic": q_topic,
                "text": q.strip(),
                "status": "pending moderation",
            })
            st.success("Submitted for moderation. It is not published automatically.")

# OPPORTUNITIES
elif page == "Opportunities":
    st.title("Opportunities")
    st.write(
        "This section now separates actions you can do *inside* Opportunity Navigator from real external providers. "
        "External links are optional and secondary."
    )

    p = profile()
    st.subheader("Your next actions")
    actions = []
    goals = p.get("goals", [])
    if "Prepare for university applications" in goals:
        actions.append(("Build an application evidence portfolio",
                        "Create evidence categories for projects, research, volunteering and measurable results."))
    if "Prepare for SAT / international exams" in goals:
        actions.append(("Create a two-week exam sprint",
                        "Pick one section, take a diagnostic, log errors, practise daily and retest after seven days."))
    if "Find scholarships and opportunities" in goals:
        actions.append(("Build an opportunity shortlist",
                        "Save three realistic options, compare eligibility and choose one application task for this week."))
    if "Learn coding" in goals:
        actions.append(("Build a first coding project",
                        "Choose one small problem, build one feature, test it, and write what changed after feedback."))
    if not actions:
        actions.append(("Create a 7-day evidence plan",
                        "Choose one goal and define one measurable action for each of the next seven days."))

    for title, body in actions:
        st.markdown(f"<div class='path-step'><b>{title}</b><br><span class='muted'>{body}</span></div>", unsafe_allow_html=True)

    st.subheader("Opportunities for you")
    st.caption(
        "Provider records are examples for the prototype. Always verify the current cycle, deadline and local eligibility on the official page."
    )

    ranked = []
    for o in PROVIDER_OPPORTUNITIES:
        sc, reasons = score_opportunity(o, p)
        ranked.append((sc, reasons, o))
    ranked.sort(key=lambda x: x[0], reverse=True)

    category_filter = st.selectbox("Category", ["All"] + sorted({o["category"] for o in PROVIDER_OPPORTUNITIES}))

    for score, reasons, o in ranked:
        if category_filter != "All" and o["category"] != category_filter:
            continue
        st.markdown(f"### {o['name']}")
        st.markdown(
            " ".join([
                f"<span class='pill'>{o['category']}</span>",
                f"<span class='pill'>{o['cost']}</span>",
                f"<span class='pill'>Ages {o['age_min']}–{o['age_max']}</span>",
            ]),
            unsafe_allow_html=True,
        )
        st.write(o["summary"])
        st.write(f"**Why this matches:** {', '.join(reasons) if reasons else 'general exploratory match — review eligibility carefully'}")
        st.write(f"**Eligibility:** {o['eligibility']}")
        with st.expander("Inside-platform preparation checklist"):
            for i, item in enumerate(o["checklist"], 1):
                st.write(f"{i}. {item}")

        c1, c2 = st.columns(2)
        with c1:
            saved = o["id"] in st.session_state.saved_opportunities
            if st.button("✓ Saved" if saved else "Save opportunity", key=f"save_{o['id']}", disabled=saved, use_container_width=True):
                st.session_state.saved_opportunities.add(o["id"])
                st.rerun()
        with c2:
            st.link_button("Official provider page", o["url"], use_container_width=True)
        st.divider()

    if st.session_state.saved_opportunities:
        st.success(f"You have {len(st.session_state.saved_opportunities)} saved opportunity item(s). They appear in My Pathway.")

# ABOUT
elif page == "About the Project":
    st.title("About the project")
    st.markdown("## Product problem")
    st.write(
        "Useful educational services already exist, but they are fragmented. The prototype explores the "
        "opportunity-navigation gap: the distance between an opportunity existing and a young person being able "
        "to find, understand, access and use it."
    )

    st.markdown("## What changed after testing")
    changes = [
        "The first MVP behaved too much like an aggregator, so core learning and planning moved inside the platform.",
        "A broken external resource showed that the product cannot depend on third-party links for its core experience.",
        "The motivation module was too shallow, so stories now include starting point, turning point, evidence, reflection and an action.",
        "The AI Tutor had no place for a learner to state what they did not understand; it now begins from the learner's exact stuck point.",
        "The Learning Hub gave too little practice and did not show explanations; lessons now contain multiple questions and feedback.",
        "The profile was artificially limited; country and language selectors now use broad searchable lists.",
        "Navigation buttons now move between sections correctly and home-page actions change after profile creation.",
        "Opportunities are split into inside-platform actions and optional external provider opportunities.",
    ]
    for i, x in enumerate(changes, 1):
        st.write(f"{i}. {x}")

    st.markdown("## Product principle")
    st.markdown(
        "<div class='notice'><b>Do not make a teenager assemble the solution alone.</b> "
        "Learning, tutoring, motivation, support, community and opportunity navigation should work as one pathway.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("## What is implemented in this portfolio prototype")
    st.write(
        "• global country / language selection\n"
        "• personalized transparent pathway logic\n"
        "• structured tutoring workflow with a learner 'stuck point'\n"
        "• multi-question in-platform lessons with explanations\n"
        "• barrier-matched motivation stories\n"
        "• safe human-support request workflow\n"
        "• moderated-community workflow\n"
        "• personalized opportunity cards, preparation checklists and saved items"
    )

    st.markdown("## What is not yet production AI")
    st.write(
        "• the tutor uses deterministic prototype logic rather than a live generative model\n"
        "• mentor matching is simulated rather than connected to a real partner network\n"
        "• community moderation is demonstrated in-session, not backed by a production moderation service\n"
        "• recommendation logic is an explainable rule-based baseline, not a trained ML recommender\n"
        "• session data is not a production user database"
    )

    st.markdown("## Next validation before more ML")
    st.write(
        "1. Test with target users and record confusion points and time-to-useful-next-step.\n"
        "2. Measure lesson completion and whether explanations help after mistakes.\n"
        "3. Compare generic vs barrier-matched motivation stories.\n"
        "4. Refine safeguarding with educators / youth-support specialists.\n"
        "5. Only then compare the explainable rule-based baseline with more complex recommendation models."
    )
