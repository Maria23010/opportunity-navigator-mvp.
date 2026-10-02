import base64
import gettext
import ipaddress
import json
import os
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
    from deep_translator import GoogleTranslator, MyMemoryTranslator
except Exception:
    GoogleTranslator = None
    MyMemoryTranslator = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

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

VERSION = "1.3"

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

    /* Keep sidebar select values readable: sidebar text is light, select controls are white. */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div { background:#ffffff !important; }
    [data-testid="stSidebar"] div[data-baseweb="select"] *,
    [data-testid="stSidebar"] div[data-baseweb="select"] span,
    [data-testid="stSidebar"] div[data-baseweb="select"] input,
    [data-testid="stSidebar"] div[data-baseweb="select"] [role="combobox"] {
        color:#111827 !important; -webkit-text-fill-color:#111827 !important; opacity:1 !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] svg { fill:#111827 !important; color:#111827 !important; }
    div[data-baseweb="popover"] li, div[data-baseweb="popover"] li * { color:#111827 !important; }
    .language-badge {
        margin:.35rem 0 1rem 0; padding:.5rem .7rem; border-radius:10px;
        background:rgba(255,255,255,.10); color:#f8fafc; font-size:.82rem; font-weight:700;
    }
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

# -------------------- Interface language --------------------
# v0.9 ships with a complete English/Russian interface for the MVP. Country and
# language names are localized from pycountry's ISO translation catalogues, so a
# Russian-speaking learner does not need to know English country names.

# Interface language is independent from country. v1.0 exposes every language
# supported by the translation engine. English and Russian keep hand-edited
# strings where available; other languages use cached automatic translation.
_NATIVE_LANGUAGE_LABELS = {
    "en":"English", "ru":"Русский", "kk":"Қазақша", "tr":"Türkçe", "ar":"العربية",
    "uk":"Українська", "uz":"Oʻzbekcha", "de":"Deutsch", "fr":"Français",
    "es":"Español", "it":"Italiano", "pt":"Português", "nl":"Nederlands",
    "pl":"Polski", "cs":"Čeština", "sk":"Slovenčina", "ro":"Română",
    "bg":"Български", "sr":"Српски", "hr":"Hrvatski", "sl":"Slovenščina",
    "el":"Ελληνικά", "he":"עברית", "fa":"فارسی", "hi":"हिन्दी", "ur":"اردو",
    "bn":"বাংলা", "id":"Bahasa Indonesia", "ms":"Bahasa Melayu", "vi":"Tiếng Việt",
    "th":"ไทย", "ko":"한국어", "ja":"日本語", "zh-CN":"中文（简体）",
    "zh-TW":"中文（繁體）", "az":"Azərbaycanca", "hy":"Հայերեն", "ka":"ქართული",
    "sv":"Svenska", "no":"Norsk", "da":"Dansk", "fi":"Suomi", "et":"Eesti",
    "lv":"Latviešu", "lt":"Lietuvių", "sw":"Kiswahili", "af":"Afrikaans",
}

def _supported_interface_languages():
    fallback = {
        "english":"en", "russian":"ru", "kazakh":"kk", "turkish":"tr",
        "arabic":"ar", "spanish":"es", "french":"fr", "german":"de",
        "portuguese":"pt", "italian":"it", "chinese (simplified)":"zh-CN",
        "chinese (traditional)":"zh-TW", "japanese":"ja", "korean":"ko",
        "hindi":"hi", "ukrainian":"uk", "uzbek":"uz", "indonesian":"id",
        "vietnamese":"vi", "thai":"th", "dutch":"nl", "polish":"pl",
    }
    if GoogleTranslator is None:
        return fallback
    try:
        data = GoogleTranslator().get_supported_languages(as_dict=True)
        return data or fallback
    except Exception:
        return fallback

_TRANSLATOR_LANGS = _supported_interface_languages()
INTERFACE_LANG_OPTIONS = {}
for _name, _code in _TRANSLATOR_LANGS.items():
    _native = _NATIVE_LANGUAGE_LABELS.get(_code)
    if _native and _native.lower() != str(_name).lower():
        _label = f"{_native} — {_name.title()} ({_code})"
    else:
        _label = f"{str(_name).title()} ({_code})"
    INTERFACE_LANG_OPTIONS[_label] = _code

# Keep the most common choices at the top; the select box remains searchable.
_PRIORITY_CODES = ["en","ru","kk","tr","ar","uk","uz","es","fr","de","zh-CN","hi"]
INTERFACE_LANG_OPTIONS = dict(sorted(
    INTERFACE_LANG_OPTIONS.items(),
    key=lambda kv: (
        _PRIORITY_CODES.index(kv[1]) if kv[1] in _PRIORITY_CODES else 999,
        kv[0].lower(),
    )
))


# Core offline fallback for the language shown in the current test.
# The rest of the interface continues through the automatic translation pipeline.
CORE_UI_FALLBACK = {
    "kk": {
        "sidebar_sub":"Оқу, жоспарлау, байланысу және алға жылжу үшін бір орын.",
        "nav_home":"Басты бет", "nav_path":"Менің бағытым", "nav_tutor":"AI тәлімгер", "nav_learning":"Оқу орталығы",
        "nav_motivation":"Мотивация", "nav_support":"Адам көмегі", "nav_community":"Қауымдастық",
        "nav_opportunities":"Мүмкіндіктер", "nav_university":"Университет жоспары", "nav_profile":"Профиль", "nav_about":"Жоба туралы",
        "home_eyebrow":"Зерттеуге негізделген әлеуметтік мобильдік платформасы",
        "home_title":"Келесі қадам қайдан іздеу керегін білуге тәуелді болмауы тиіс.",
        "home_sub":"Opportunity Navigator оқу, тәлімгерлік, мотивация, қауіпсіз адам көмегі, қауымдастық, университетке түсу жоспары және мүмкіндіктерді іздеуді бір жерде біріктіреді.",
        "learn":"ОҚУ", "navigate":"БАҒЫТ", "connect_safely":"ҚАУІПСІЗ БАЙЛАНЫС",
        "tutor_hub":"AI тәлімгер + Оқу орталығы", "personal_pathway":"Жеке бағыт", "support_community":"Адам көмегі + қауымдастық",
        "learn_desc":"Түсінбей тұрған нақты жеріңізді сұраңыз, түсіндірме мен кеңес алыңыз, содан кейін бейімделетін жаттығулар орындаңыз.",
        "navigate_desc":"Мақсаттар, кедергілер, прогресс және түсу жоспарын нақты келесі қадамдарға айналдырыңыз.",
        "connect_desc":"Тәлімгер көмегін сұраңыз және байланыс деректері қорғалған модерацияланған қауымдастықты пайдаланыңыз.",
        "continue_path":"Бағытымды жалғастыру", "build_profile":"Профиль құру", "explore_learning":"Оқу орталығын ашу",
        "plan_university":"Университетке түсуді жоспарлау", "one_platform":"Жай анықтамалық емес, біртұтас платформа",
        "selected_language":"Таңдалған тіл",
    }
}

UI_TEXT = {
    "en": {
        "sidebar_sub":"One place to learn, plan, connect and move forward.",
        "interface_language":"🌐 Interface language / Язык",
        "nav_home":"Home", "nav_path":"My Pathway", "nav_tutor":"AI Tutor", "nav_learning":"Learning Hub",
        "nav_motivation":"Motivation", "nav_support":"Human Support", "nav_community":"Community",
        "nav_opportunities":"Opportunities", "nav_university":"University Planner", "nav_profile":"Profile", "nav_about":"About the Project",
        "profile_caption":"Profile: age {age} · {country} · {language}",
        "create_profile_caption":"Create a profile to personalize the platform.",
        "save_restore":"Save / restore demo progress", "export_progress":"Export progress", "import_progress":"Import progress",
        "restore_progress":"Restore imported progress", "reset_progress":"Reset demo progress", "progress_restored":"Progress restored.",
        "home_eyebrow":"Research-driven social mobility platform",
        "home_title":"Your next step should not depend on knowing where to look.",
        "home_sub":"Opportunity Navigator combines learning, tutoring, motivation, safe human support, community, admissions planning and opportunity discovery in one place.",
        "learn":"Learn", "navigate":"Navigate", "connect_safely":"Connect safely",
        "tutor_hub":"AI Tutor + Learning Hub", "personal_pathway":"Personal pathway", "support_community":"Human support + community",
        "learn_desc":"Ask about the exact stuck point, get hints and explanations, then practise adaptively.",
        "navigate_desc":"Turn goals, barriers, progress and admissions targets into useful next actions.",
        "connect_desc":"Request a mentor route and use moderated topic spaces with contact-detail blocking.",
        "continue_path":"Continue my pathway", "build_profile":"Build my profile", "explore_learning":"Explore Learning Hub",
        "plan_university":"Plan university applications", "one_platform":"One platform, not another directory",
        "one_platform_desc":"Learning, tutoring, planning, progress tracking and preparation happen inside the platform. Official provider pages are a secondary verification/application layer.",
        "profile_title":"Build your learner & access profile", "profile_hint":"Country and language fields are searchable and shown in your interface language.",
        "age":"Age", "country_region":"Country / region", "preferred_language":"Preferred language", "other_languages":"Other languages you can use",
        "goals":"What do you want to work on?", "barriers":"What makes progress harder right now?", "preferred_support":"Preferred support",
        "access_needs":"Access needs", "current_need":"What do you need help with today?", "save_profile":"Save profile and build my pathway",
        "open_pathway":"Open my pathway", "profile_saved":"Profile saved. Your pathway has been rebuilt and core profile selections will survive refresh.",
        "my_pathway":"My pathway", "create_profile_first":"Create your profile first so the pathway can use your goals, language and access constraints.",
        "create_profile":"Create profile", "today":"Today", "focus_next":"focus on one useful next step, not a long list. Your main goal is",
        "completed_modules":"Learning modules completed", "saved_opportunities":"Saved opportunities", "support_requests":"Support requests", "saved_actions":"Saved actions",
        "todays_path":"Today's path", "actions_saved":"Actions I saved", "go_to":"Go to {target}",
        "tutor_title":"AI Tutor — explain the exact stuck point", "tutor_desc":"Choose a subject and topic, describe exactly what is unclear, then keep asking follow-up questions in the same session.",
        "technical_note":"Technical note for portfolio reviewers", "subject":"Subject", "topic":"Topic", "write_topic":"Write the topic",
        "what_unclear":"What do you not understand?", "what_tried":"What have you tried?", "how_help":"How should the tutor help?",
        "confidence":"How confident do you feel about this topic?", "start_session":"Start tutoring session", "clear_session":"Clear session",
        "locate_stuck":"1. Locate the stuck point", "explanation_follow":"2. Explanation and follow-up", "explain_simpler":"Explain more simply",
        "give_hint":"Give me a hint", "show_example":"Show another example", "ask_same":"Ask another question about the same topic",
        "ask_follow":"Ask follow-up", "check_understanding":"3. Check your understanding", "your_answer":"Your answer / explanation", "check_answer":"Check my answer",
        "learning_title":"Learning Hub", "learning_desc":"Short lessons begin with a small diagnostic set. If mistakes show a weak point, the lesson adds extra practice automatically.",
        "filter_subject":"Filter by subject", "choose_lesson":"Choose a lesson", "question_of":"Question {current} of {total}", "choose_answer":"Choose an answer",
        "next_question":"Next question", "lesson_complete":"Lesson complete.", "restart_lesson":"Restart this lesson",
        "motivation_title":"Motivation → evidence → action", "motivation_desc":"A story should match a real barrier, show a turning point, and end with something the learner can do now.",
        "barrier_story":"What kind of barrier should the story speak to?", "choose_story":"Choose a story", "open_source":"Open source",
        "own_action":"Turn the story into your own next action", "save_action":"Save this action to my pathway", "saved_path":"Saved to My Pathway.",
        "support_title":"Human Support", "support_desc":"AI can help navigate; it should not replace a qualified teacher, mentor or mental-health professional.",
        "support_kind":"What kind of human help do you need?", "support_language":"Preferred language for support", "support_detail":"What would you like the mentor or professional to know?",
        "support_consent":"I understand this prototype does not create an unmoderated private adult-child chat.", "create_support":"Create safe support request",
        "community_title":"Community — moderated, not open DMs", "community_desc":"Topic rooms use pseudonyms and moderation. Contact details are blocked before submission. Private messaging is not part of this MVP.",
        "topic_room":"Topic room", "ask_community":"Ask the community", "your_question":"Your question", "send_moderation":"Send to moderation",
        "opportunities_title":"Opportunities", "next_actions":"Your next actions", "opportunities_for_you":"Opportunities for you", "category":"Category",
        "save_opportunity":"Save opportunity", "saved":"Saved ✓", "official_provider":"Open official provider page ↗",
        "university_title":"University Planner", "university_desc":"Tell the planner where you want to apply. For supported universities, it shows published requirements, exams, scores, deadlines and preparation steps directly inside the platform.",
        "target_country":"Target country", "target_university":"Target university", "course_program":"Course / program", "study_level":"Study level",
        "entry_year":"Target entry year", "need_aid":"I need scholarship / financial aid", "official_url":"Official admissions or course page URL (optional)",
        "build_plan":"Build / update my admissions plan", "plan_saved":"Admissions target saved.",
        "auto_research":"Automatic official-information research", "research_button":"Research this university automatically",
        "research_fallback":"For universities without a curated record, the planner tries the institution's own official website. If the site blocks server access, the learner sees a clear message instead of a technical traceback.",
        "preparation_areas":"Preparation areas", "portfolio_tracker":"Portfolio evidence tracker", "about_title":"About the project",
        "global_unspecified":"Global / not specified",
    },
    "ru": {
        "sidebar_sub":"Одно место, чтобы учиться, планировать, получать поддержку и двигаться дальше.",
        "interface_language":"🌐 Язык интерфейса / Interface language",
        "nav_home":"Главная", "nav_path":"Мой маршрут", "nav_tutor":"AI-репетитор", "nav_learning":"Учебный центр",
        "nav_motivation":"Мотивация", "nav_support":"Поддержка человека", "nav_community":"Сообщество",
        "nav_opportunities":"Возможности", "nav_university":"План поступления", "nav_profile":"Профиль", "nav_about":"О проекте",
        "profile_caption":"Профиль: {age} лет · {country} · {language}",
        "create_profile_caption":"Создайте профиль, чтобы платформа персонализировала помощь.",
        "save_restore":"Сохранить / восстановить прогресс", "export_progress":"Экспорт прогресса", "import_progress":"Импорт прогресса",
        "restore_progress":"Восстановить прогресс", "reset_progress":"Сбросить демо-прогресс", "progress_restored":"Прогресс восстановлен.",
        "home_eyebrow":"Платформа социальной мобильности на основе исследований",
        "home_title":"Следующий шаг не должен зависеть от того, знаете ли вы, где искать.",
        "home_sub":"Opportunity Navigator объединяет обучение, репетитора, мотивацию, безопасную поддержку, сообщество, планирование поступления и поиск возможностей в одном месте.",
        "learn":"Учиться", "navigate":"Планировать", "connect_safely":"Получать безопасную поддержку",
        "tutor_hub":"AI-репетитор + Учебный центр", "personal_pathway":"Персональный маршрут", "support_community":"Поддержка + сообщество",
        "learn_desc":"Опишите точное место, где вы запутались, получите подсказки и объяснения, а затем тренируйтесь адаптивно.",
        "navigate_desc":"Превратите цели, ограничения, прогресс и планы поступления в конкретные следующие шаги.",
        "connect_desc":"Запросите помощь наставника и используйте модерируемые тематические комнаты без обмена личными контактами.",
        "continue_path":"Продолжить мой маршрут", "build_profile":"Создать мой профиль", "explore_learning":"Открыть Учебный центр",
        "plan_university":"Спланировать поступление", "one_platform":"Одна платформа, а не ещё один каталог ссылок",
        "one_platform_desc":"Обучение, репетитор, планирование, отслеживание прогресса и подготовка происходят внутри платформы. Официальные сайты остаются вторичным слоем для подтверждения информации и подачи заявки.",
        "profile_title":"Создайте профиль ученика и условий доступа", "profile_hint":"Страны и языки доступны в поиске и показываются на языке интерфейса.",
        "age":"Возраст", "country_region":"Страна / регион", "preferred_language":"Предпочитаемый язык", "other_languages":"Другие языки, которыми вы владеете",
        "goals":"Над чем вы хотите работать?", "barriers":"Что сейчас мешает продвигаться?", "preferred_support":"Предпочитаемая поддержка",
        "access_needs":"Условия доступа", "current_need":"С чем вам нужна помощь сегодня?", "save_profile":"Сохранить профиль и построить маршрут",
        "open_pathway":"Открыть мой маршрут", "profile_saved":"Профиль сохранён. Маршрут перестроен, основные настройки сохранятся после обновления страницы.",
        "my_pathway":"Мой маршрут", "create_profile_first":"Сначала создайте профиль, чтобы маршрут учитывал ваши цели, язык и ограничения доступа.",
        "create_profile":"Создать профиль", "today":"Сегодня", "focus_next":"сосредоточьтесь на одном полезном следующем шаге. Главная цель:",
        "completed_modules":"Пройденные модули", "saved_opportunities":"Сохранённые возможности", "support_requests":"Запросы поддержки", "saved_actions":"Сохранённые действия",
        "todays_path":"Маршрут на сегодня", "actions_saved":"Мои сохранённые действия", "go_to":"Перейти: {target}",
        "tutor_title":"AI-репетитор — разберите точное место, где возникла трудность", "tutor_desc":"Выберите предмет и тему, опишите, что именно непонятно, и задавайте дополнительные вопросы в одной сессии.",
        "technical_note":"Техническая заметка для портфолио", "subject":"Предмет", "topic":"Тема", "write_topic":"Напишите тему",
        "what_unclear":"Что именно вам непонятно?", "what_tried":"Что вы уже пробовали?", "how_help":"Как репетитор должен помочь?",
        "confidence":"Насколько уверенно вы чувствуете себя в этой теме?", "start_session":"Начать занятие", "clear_session":"Очистить сессию",
        "locate_stuck":"1. Найдём точное место трудности", "explanation_follow":"2. Объяснение и дополнительные вопросы", "explain_simpler":"Объясни ещё проще",
        "give_hint":"Дай подсказку", "show_example":"Покажи другой пример", "ask_same":"Задайте ещё один вопрос по этой теме",
        "ask_follow":"Задать вопрос", "check_understanding":"3. Проверим понимание", "your_answer":"Ваш ответ / объяснение", "check_answer":"Проверить ответ",
        "learning_title":"Учебный центр", "learning_desc":"Урок начинается с небольшого диагностического набора. Если ошибки показывают слабое место, система автоматически добавляет практику.",
        "filter_subject":"Фильтр по предмету", "choose_lesson":"Выберите урок", "question_of":"Вопрос {current} из {total}", "choose_answer":"Выберите ответ",
        "next_question":"Следующий вопрос", "lesson_complete":"Урок завершён.", "restart_lesson":"Пройти урок заново",
        "motivation_title":"Мотивация → доказательства → действие", "motivation_desc":"История должна соответствовать реальной трудности, показывать поворотный момент и завершаться конкретным действием.",
        "barrier_story":"Какой трудности должна соответствовать история?", "choose_story":"Выберите историю", "open_source":"Открыть источник",
        "own_action":"Превратите историю в свой следующий шаг", "save_action":"Сохранить действие в мой маршрут", "saved_path":"Сохранено в «Мой маршрут».",
        "support_title":"Поддержка человека", "support_desc":"AI помогает ориентироваться, но не должен заменять квалифицированного учителя, наставника или специалиста по психическому здоровью.",
        "support_kind":"Какая помощь человека вам нужна?", "support_language":"Предпочитаемый язык поддержки", "support_detail":"Что наставнику или специалисту важно знать?",
        "support_consent":"Я понимаю, что прототип не создаёт немодерируемый личный чат взрослого с ребёнком.", "create_support":"Создать безопасный запрос поддержки",
        "community_title":"Сообщество — с модерацией, без личных сообщений", "community_desc":"Тематические комнаты используют псевдонимы и модерацию. Контактные данные блокируются до отправки.",
        "topic_room":"Тематическая комната", "ask_community":"Спросить сообщество", "your_question":"Ваш вопрос", "send_moderation":"Отправить на модерацию",
        "opportunities_title":"Возможности", "next_actions":"Ваши следующие действия", "opportunities_for_you":"Возможности для вас", "category":"Категория",
        "save_opportunity":"Сохранить возможность", "saved":"Сохранено ✓", "official_provider":"Открыть официальный сайт ↗",
        "university_title":"План поступления", "university_desc":"Укажите, куда вы хотите поступать. Для поддерживаемых университетов платформа сразу показывает опубликованные требования, экзамены, баллы, сроки и шаги подготовки.",
        "target_country":"Страна поступления", "target_university":"Университет", "course_program":"Программа / специальность", "study_level":"Уровень обучения",
        "entry_year":"Год поступления", "need_aid":"Мне нужна стипендия / финансовая помощь", "official_url":"Официальная страница поступления или программы (необязательно)",
        "build_plan":"Построить / обновить план поступления", "plan_saved":"Цель поступления сохранена.",
        "auto_research":"Автоматический поиск официальной информации", "research_button":"Исследовать университет автоматически",
        "research_fallback":"Если университет ещё не добавлен в проверенную базу, платформа пытается прочитать его официальный сайт. Если сайт блокирует серверный доступ, ребёнок увидит понятное сообщение, а не техническую ошибку.",
        "preparation_areas":"Направления подготовки", "portfolio_tracker":"Трекер портфолио", "about_title":"О проекте",
        "global_unspecified":"Весь мир / не указано",
    }
}

RU_DYNAMIC = {
    "Improve school grades":"Улучшить школьные оценки", "Understand mathematics":"Разобраться в математике",
    "Learn English":"Учить английский", "Learn coding":"Учиться программированию",
    "Prepare for SAT / international exams":"Готовиться к SAT / международным экзаменам",
    "Prepare for university applications":"Готовиться к поступлению в университет",
    "Find scholarships and opportunities":"Найти стипендии и возможности", "Build confidence and study habits":"Развить уверенность и учебные привычки",
    "Lack of guidance":"Не хватает понятного руководства", "Financial limits":"Финансовые ограничения", "Low confidence":"Низкая уверенность",
    "I do not know where to start":"Не знаю, с чего начать", "Limited access to tutoring":"Ограниченный доступ к репетиторам",
    "Language barrier":"Языковой барьер", "Limited device / internet access":"Ограниченный доступ к устройствам / интернету",
    "School stress or bullying":"Школьный стресс или буллинг", "Mostly self-study":"В основном самостоятельно",
    "Mostly human support":"В основном помощь человека", "A mix of both":"Сочетание самостоятельной работы и поддержки",
    "Free only":"Только бесплатно", "Works on a phone":"Работает на телефоне", "Low-bandwidth friendly":"Подходит для слабого интернета",
    "Downloadable/offline materials":"Материалы для скачивания / офлайн", "Math":"Математика", "English":"Английский",
    "Coding":"Программирование", "Study skills":"Учебные навыки", "University applications":"Поступление в университет",
    "Linear equations":"Линейные уравнения", "Percentages":"Проценты", "Functions and graphs":"Функции и графики", "Fractions":"Дроби",
    "Geometry":"Геометрия", "Other":"Другое", "Articles: a / an / the":"Артикли a / an / the", "Vocabulary":"Словарный запас",
    "Writing":"Письмо", "Speaking":"Говорение", "Grammar":"Грамматика", "Loops":"Циклы", "Variables":"Переменные",
    "Functions":"Функции", "Debugging":"Отладка", "Python basics":"Основы Python", "Getting started":"Как начать",
    "Planning":"Планирование", "Focus":"Концентрация", "Revision":"Повторение", "Exam anxiety":"Тревога перед экзаменом",
    "Choosing universities":"Выбор университетов", "Admission requirements":"Требования к поступлению", "Motivation letter":"Мотивационное письмо",
    "Portfolio":"Портфолио", "Scholarships":"Стипендии", "Explain it simply":"Объясни просто", "Guide me with hints":"Веди меня подсказками",
    "Show an example":"Покажи пример", "Academic mentor":"Академический наставник", "Tutor":"Репетитор",
    "University application mentor":"Наставник по поступлению", "School support / safeguarding route":"Школьная поддержка / безопасный маршрут помощи",
    "All":"Все", "Applications":"Поступление", "Motivation":"Мотивация",
    "Bachelor's / undergraduate":"Бакалавриат", "Foundation / pathway":"Подготовительная программа / pathway",
    "Foundation / pathway":"Подготовительная программа / pathway", "Free":"Бесплатно", "Financial support available":"Доступна финансовая поддержка",
}

RU_DYNAMIC.update({
    "Linear equations without guessing":"Линейные уравнения без угадывания",
    "Learn to isolate the unknown by undoing operations in reverse order.":"Научитесь находить неизвестное, выполняя обратные операции по порядку.",
    "Solve: x + 7 = 12":"Решите: x + 7 = 12", "Subtract 7 from both sides: x = 12 − 7 = 5.":"Вычтите 7 из обеих частей: x = 12 − 7 = 5.",
    "Solve: 3x = 18":"Решите: 3x = 18", "Divide both sides by 3: x = 18 ÷ 3 = 6.":"Разделите обе части на 3: x = 18 ÷ 3 = 6.",
    "Solve: 2x + 3 = 11":"Решите: 2x + 3 = 11", "Subtract 3 first: 2x = 8. Then divide by 2: x = 4.":"Сначала вычтите 3: 2x = 8. Затем разделите на 2: x = 4.",
    "Solve: x − 9 = 4":"Решите: x − 9 = 4", "Add 9 to both sides: x = 4 + 9 = 13.":"Прибавьте 9 к обеим частям: x = 4 + 9 = 13.",
    "Solve: 4x = 28":"Решите: 4x = 28", "Divide both sides by 4: x = 7.":"Разделите обе части на 4: x = 7.",
    "Solve: 5x − 10 = 20":"Решите: 5x − 10 = 20", "Add 10: 5x = 30. Divide by 5: x = 6.":"Прибавьте 10: 5x = 30. Разделите на 5: x = 6.",
    "Solve: 3x + 6 = 24":"Решите: 3x + 6 = 24", "Subtract 6: 3x = 18. Divide by 3: x = 6.":"Вычтите 6: 3x = 18. Разделите на 3: x = 6.",
    "Percentages in real life":"Проценты в реальной жизни", "Convert the percentage to a decimal or fraction, then multiply.":"Преобразуйте процент в десятичную дробь или обычную дробь, затем умножьте.",
    "What is 20% of 150?":"Сколько будет 20% от 150?", "20% = 0.20, so 0.20 × 150 = 30.":"20% = 0,20, поэтому 0,20 × 150 = 30.",
    "A $40 item is discounted by 25%. What is the discount?":"Товар стоит $40. Скидка 25%. Какова сумма скидки?", "25% of 40 = 0.25 × 40 = 10.":"25% от 40 = 0,25 × 40 = 10.",
    "A score rises from 60 to 75. By what percentage did it increase?":"Результат вырос с 60 до 75. На сколько процентов он увеличился?", "Increase = 15. Divide by the original 60: 15/60 = 25%.":"Рост = 15. Делим на исходные 60: 15/60 = 25%.",
    "What is 10% of 90?":"Сколько будет 10% от 90?", "10% = 0.10, and 0.10 × 90 = 9.":"10% = 0,10, и 0,10 × 90 = 9.",
    "What is 50% of 36?":"Сколько будет 50% от 36?", "50% means half, so half of 36 is 18.":"50% — это половина, поэтому половина от 36 равна 18.",
    "30 is what percent of 120?":"30 — это сколько процентов от 120?", "30 ÷ 120 = 0.25 = 25%.":"30 ÷ 120 = 0,25 = 25%.",
    "A / an / the in two rules":"A / an / the по двум правилам", "Use a/an for one non-specific thing; use the when the listener knows which one.":"Используйте a/an для одного неопределённого предмета, а the — когда понятно, о каком конкретно предмете речь.",
    "I saw ___ elephant at the zoo.":"Я увидел(а) ___ elephant в зоопарке.", "Use 'an' before a vowel sound: an elephant.":"Перед гласным звуком используйте 'an': an elephant.",
    "Please close ___ door. (There is one obvious door.)":"Пожалуйста, закрой ___ door. (Понятно, о какой двери речь.)", "Use 'the' when both people know which specific door is meant.":"Используйте 'the', когда обоим понятно, какая именно дверь имеется в виду.",
    "She wants to buy ___ laptop, but she has not chosen one yet.":"Она хочет купить ___ laptop, но ещё не выбрала конкретный.", "The laptop is not specific yet, so use 'a'.":"Ноутбук пока не конкретный, поэтому используйте 'a'.",
    "He is ___ university student.":"Он ___ university student.", "University begins with a /y/ consonant sound, so use 'a'.":"University начинается со звука /y/, поэтому используется 'a'.",
    "Loops as repetition":"Циклы как повторение", "A loop repeats a block of instructions while a rule or range tells it how long.":"Цикл повторяет блок инструкций столько раз, сколько задаёт правило или диапазон.",
    "In Python, how many times does `for i in range(3)` repeat?":"Сколько раз в Python выполнится `for i in range(3)`?", "range(3) produces 0, 1, 2 — three values.":"range(3) даёт 0, 1, 2 — три значения.",
    "Which idea best describes a loop?":"Что лучше всего описывает цикл?", "Repeat instructions":"Повторять инструкции", "Store one text value":"Хранить одно текстовое значение", "Delete a file":"Удалить файл", "Rename a variable":"Переименовать переменную", "Loops repeat an action multiple times.":"Циклы повторяют действие несколько раз.",
    "How many outputs from `for x in [2,4,6,8]: print(x)`?":"Сколько значений выведет `for x in [2,4,6,8]: print(x)`?", "The list contains four items, so print runs four times.":"В списке четыре элемента, поэтому print выполнится четыре раза.",
    "The 15-minute start":"Старт за 15 минут", "Reduce the activation barrier by defining a very small first action.":"Снизьте барьер старта, выбрав очень маленькое первое действие.",
    "Which is the best 15-minute goal?":"Какая цель лучше всего подходит для 15 минут?", "Master all algebra":"Освоить всю алгебру", "Open the chapter and solve two equations":"Открыть главу и решить два уравнения", "Finish every assignment this month":"Закончить все задания за месяц", "Become fluent in English":"Свободно заговорить по-английски", "A useful short goal is concrete, small and immediately startable.":"Хорошая короткая цель конкретна, мала и её можно начать сразу.",
    "Turn an ambition into an evidence list":"Превратите цель в список доказательств", "Strong applications are easier to write when activities are documented as evidence, role, result and reflection.":"Сильную заявку легче писать, когда активность оформлена как доказательство: роль, результат и выводы.",
    "Which note is strongest evidence?":"Какая запись является самым сильным доказательством?", "I like volunteering":"Мне нравится волонтёрство", "I volunteered weekly":"Я волонтёрил(а) каждую неделю", "I designed a language game used by 8 students and recorded feedback":"Я разработал(а) языковую игру, которой пользовались 8 учеников, и собрал(а) обратную связь", "Volunteering is important":"Волонтёрство важно", "It shows action, your role, a measurable detail and evidence.":"Здесь есть действие, ваша роль, измеримая деталь и доказательство.",
    "What should you record after a project?":"Что стоит записать после проекта?", "Only the title":"Только название", "Your role, outcome and what changed after feedback":"Вашу роль, результат и что изменилось после обратной связи", "Only compliments":"Только похвалу", "Nothing until you apply":"Ничего до момента подачи", "This makes future essays and interviews more specific and credible.":"Это делает будущие эссе и интервью более конкретными и убедительными.",
    "What is a useful reflection question?":"Какой вопрос полезен для рефлексии?", "What assumption did I change after testing?":"Какое предположение я изменил(а) после тестирования?", "How can I sound impressive?":"Как звучать впечатляюще?", "How can I hide mistakes?":"Как скрыть ошибки?", "How can I add adjectives?":"Как добавить больше прилагательных?", "Reflection is strongest when it shows learning and changed thinking.":"Сильная рефлексия показывает, чему вы научились и как изменилось мышление.",
})

RU_STORIES = {
    "Jan Koum": {
        "title":"От ограниченных ресурсов к созданию WhatsApp",
        "starting":"Коум переехал в США подростком и рос в условиях ограниченных финансовых ресурсов. Его путь в технологии не был заранее выстроенным и прямым.",
        "turning":"Он самостоятельно изучал компьютерные навыки, работал в технологиях и позже стал сооснователем WhatsApp. Полезный паттерн здесь — выучить навык, применить его в реальной среде, заметить проблему и построить решение вокруг неё.",
        "lesson":"Не обязательно иметь готовый десятилетний план. Небольшой навык может стать мостом к следующей возможности, если превращать обучение в реальные доказательства.",
        "action":"Выберите один навык, необходимый для вашей текущей цели, и сегодня выполните одно бесплатное конкретное учебное действие.",
    },
    "José Hernández": {
        "title":"Долгий путь к профессии астронавта",
        "starting":"Эрнандес вырос в семье сезонных сельскохозяйственных работников и часть детства переезжал вместе с семьёй. Карьера в аэрокосмической сфере не была для него очевидным ближайшим вариантом.",
        "turning":"Он шаг за шагом выстраивал необходимые условия: образование, инженерный опыт, повторные заявки и постоянное развитие навыков.",
        "lesson":"Далёкая цель становится управляемой, когда вы превращаете её в требования, которые можно закрывать по одному.",
        "action":"Запишите одну долгосрочную цель, три ближайших требования и сделайте действие по самому маленькому из них.",
    },
    "Malala Yousafzai": {
        "title":"Образование как действие, а не только мечта",
        "starting":"Юсуфзай стала известна благодаря защите права девочек на образование в условиях, где сам доступ к школе был под угрозой.",
        "turning":"Её история показывает, что образование бывает не только личной целью, но и системной проблемой. Она продолжала учиться и одновременно делала барьер видимым через тексты и публичную деятельность.",
        "lesson":"Когда барьер системный, ответ не всегда заключается в том, чтобы «стараться сильнее». Иногда нужны союзники, безопасные маршруты и институты, которые меняют условия вокруг человека.",
        "action":"Назовите один барьер, который нельзя решить только усилием, и определите одного человека или организацию, которые могут его уменьшить.",
    },
}

RU_COMMUNITY_POSTS = {
    "I used to freeze when I saw functions. Drawing the graph first made the formula less scary.":"Раньше я терялся(ась), когда видел(а) функции. Если сначала рисовать график, формула становится менее страшной.",
    "I study in 20-minute blocks because long sessions made me give up. Short sessions finally became a habit.":"Я занимаюсь по 20 минут, потому что длинные сессии заставляли меня сдаваться. Короткие занятия наконец стали привычкой.",
    "Reading one short article aloud each day helped me stop being afraid of pronunciation mistakes.":"Чтение одной короткой статьи вслух каждый день помогло мне перестать бояться ошибок в произношении.",
    "I keep one evidence document with projects, results and what I personally did. Essay writing became much easier.":"Я веду один документ с проектами, результатами и тем, что сделал(а) лично. Писать эссе стало гораздо легче.",
    "When code fails, I change one thing at a time. It is slower than guessing but I actually understand the bug.":"Когда код не работает, я меняю по одной вещи за раз. Это медленнее случайных попыток, но зато я понимаю ошибку.",
}

RU_TUTOR = {
    "The key idea is to keep both sides of an equation balanced while you isolate x.":"Главная идея — сохранять равенство: выполняйте одну и ту же операцию с обеими частями, пока не останется x.",
    "Undo operations in reverse order. If something is added, subtract it. If x is multiplied, divide.":"Отменяйте операции в обратном порядке. Если к x что-то прибавили — вычтите это из обеих частей. Если x умножен — разделите обе части.",
    "For 2x + 3 = 11, remove +3 first. What remains on the left?":"Для 2x + 3 = 11 сначала уберите +3, вычитая 3 из обеих частей. Что останется слева?",
    "Example: 3x + 6 = 18 → subtract 6 → 3x = 12 → divide by 3 → x = 4.":"Пример: 3x + 6 = 18 → вычесть 6 → 3x = 12 → разделить на 3 → x = 4.",
    "Try this: solve 2x + 3 = 11.":"Попробуйте решить: 2x + 3 = 11.",
    "Subtract 3 from both sides to get 2x = 8, then divide both sides by 2: x = 4.":"Вычтите 3 из обеих частей: 2x = 8. Затем разделите обе части на 2: x = 4.",
    "A percentage is a part out of 100. Most questions become easier after converting the percent to a decimal.":"Процент — это часть из 100. Большинство задач упрощается, если перевести процент в десятичную дробь.",
    "20% means 20/100, which is 0.20. Then multiply by the whole amount.":"20% означает 20/100, то есть 0,20. Затем умножьте на целое количество.",
    "For 20% of 150, calculate 0.20 × 150.":"Чтобы найти 20% от 150, посчитайте 0,20 × 150.",
    "25% of 40 = 0.25 × 40 = 10.":"25% от 40 = 0,25 × 40 = 10.",
    "A graph connects an input x to an output y. Start by identifying what changes and what stays fixed.":"График связывает вход x с результатом y. Сначала определите, что меняется, а что остаётся постоянным.",
    "Pick a few x-values, calculate y for each one, then plot the pairs (x, y).":"Выберите несколько значений x, вычислите y для каждого и отметьте пары (x, y) на графике.",
    "For y = 2x + 1, try x = 0 first. What is y?":"Для y = 2x + 1 сначала возьмите x = 0. Чему равен y?",
    "If y = 2x + 1 and x = 2, then y = 5, so one point is (2,5).":"Если y = 2x + 1 и x = 2, то y = 5, значит одна точка — (2,5).",
    "The choice depends on whether the noun is specific and on the sound at the beginning of the next word.":"Выбор зависит от того, конкретный ли это предмет, и от звука в начале следующего слова.",
    "Use a/an for one non-specific thing. Use the when both people know which thing you mean.":"Используйте a/an для одного неопределённого предмета. Используйте the, когда понятно, какой именно предмет имеется в виду.",
    "Listen to the sound: 'an elephant' but 'a university' because university begins with a /y/ sound.":"Слушайте первый звук: 'an elephant', но 'a university', потому что university начинается со звука /y/.",
    "A loop repeats an instruction. To understand it, list the values the loop will visit.":"Цикл повторяет инструкцию. Чтобы его понять, выпишите значения, которые он проходит.",
    "Read the loop as: for each value, do the indented action once.":"Читайте цикл так: для каждого значения один раз выполнить действие с отступом.",
    "range(3) gives 0, 1, 2.":"range(3) даёт 0, 1, 2.",
    "Admissions questions become manageable when you separate requirements, evidence and deadlines.":"Поступление становится понятнее, если разделить требования, доказательства и сроки.",
    "Make a table with: course, academic requirements, exams, language scores, deadline, essays, portfolio/evidence and financial aid.":"Сделайте таблицу: программа, академические требования, экзамены, языковые баллы, дедлайны, эссе, портфолио/доказательства и финансовая помощь.",
    "Start with the official course page, not a blog. Record the exact requirement and its source URL.":"Начинайте с официальной страницы программы, а не с блога. Запишите точное требование и ссылку-источник.",
    "A precise unknown tells you what to research next.":"Точное неизвестное показывает, что нужно проверить следующим шагом.",
}


def interface_lang():
    return st.session_state.get("interface_lang", "en")

def _protect_placeholders(text):
    placeholders = {}
    def repl(match):
        key = f"ZXPH{len(placeholders)}XZ"
        placeholders[key] = match.group(0)
        return key
    return re.sub(r"\{[^{}]+\}", repl, text), placeholders

def _openai_api_key():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        return ""

def _openai_model():
    try:
        return str(st.secrets.get("OPENAI_MODEL", "gpt-5")).strip() or "gpt-5"
    except Exception:
        return os.getenv("OPENAI_MODEL", "gpt-5") or "gpt-5"

@st.cache_data(ttl=86400, show_spinner=False)
def _openai_translate(text, target):
    key = _openai_api_key()
    if not key or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=key, timeout=45.0)
        response = client.responses.create(
            model=_openai_model(),
            input=(
                f"Translate the following interface text into language code {target}. "
                "Preserve placeholders such as {name}, numbers, URLs, Markdown, emojis and product names. "
                "Return only the translation, with no explanation.\n\n" + text
            ),
        )
        value = (response.output_text or "").strip()
        return value or None
    except Exception:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def _google_http_translate(text, target):
    """Lightweight web translation fallback that does not require a project API key."""
    if not text or not target:
        return None
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client":"gtx", "sl":"auto", "tl":target, "dt":"t", "q":text},
            timeout=12,
            headers={"User-Agent":"Mozilla/5.0"},
        )
        r.raise_for_status()
        payload = r.json()
        parts = payload[0] if isinstance(payload, list) and payload else []
        translated = "".join(str(p[0]) for p in parts if isinstance(p, list) and p and p[0])
        return translated.strip() or None
    except Exception:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def _auto_translate(text, target):
    """Translate learner-facing text. Use several fallbacks; never break the page if translation fails."""
    if not isinstance(text, str) or not text.strip() or target in {"", "en", None}:
        return text
    if re.match(r"^https?://", text.strip()) or len(text.strip()) <= 1:
        return text
    protected, placeholders = _protect_placeholders(text)
    translated = None
    # Direct HTTP translation is intentionally first: on Streamlit it is often
    # more reliable than third-party wrappers that may fail silently.
    translated = _google_http_translate(protected, target)
    if not translated and GoogleTranslator is not None:
        try:
            translated = GoogleTranslator(source="auto", target=target).translate(protected)
        except Exception:
            translated = None
    if not translated and MyMemoryTranslator is not None:
        try:
            translated = MyMemoryTranslator(source="en", target=target).translate(protected)
        except Exception:
            translated = None
    if not translated:
        translated = _openai_translate(protected, target)
    if not translated:
        return text
    for token, original in placeholders.items():
        translated = translated.replace(token, original)
    return translated

def localize_tutor_base(base):
    lang = interface_lang()
    if lang == "en":
        return base
    out = {}
    for k, v in base.items():
        if not isinstance(v, str):
            out[k] = v
        elif lang == "ru":
            out[k] = RU_TUTOR.get(v, RU_DYNAMIC.get(v, v))
        else:
            out[k] = _auto_translate(v, lang)
    return out

def t(key, **kwargs):
    lang = interface_lang()
    english = UI_TEXT["en"].get(key, key)
    if lang == "ru":
        text = UI_TEXT.get("ru", {}).get(key, english)
    elif lang == "en":
        text = english
    elif key in CORE_UI_FALLBACK.get(lang, {}):
        text = CORE_UI_FALLBACK[lang][key]
    else:
        text = _auto_translate(english, lang)
    try:
        return text.format(**kwargs)
    except Exception:
        return text

def lx(text):
    """Localize dynamic learner-facing content."""
    if not isinstance(text, str):
        return text
    lang = interface_lang()
    if lang == "en":
        return text
    if lang == "ru":
        return RU_DYNAMIC.get(text, RU_TUTOR.get(text, text))
    return _auto_translate(text, lang)

def ui(en, ru=None):
    """Small helper for strings that were previously hard-coded in EN/RU branches."""
    lang = interface_lang()
    if lang == "ru" and ru:
        return ru
    if lang == "en":
        return en
    return _auto_translate(en, lang)

def _iso_translation(domain, text):
    if not pycountry or not text:
        return text
    lang = interface_lang()
    if lang == "en":
        return text
    # pycountry has local gettext catalogues for many locales. This is much
    # faster and more reliable than making a web translation request for 200 countries.
    try:
        tr = gettext.translation(domain, pycountry.LOCALES_DIR, languages=[lang])
        translated = tr.gettext(text)
        if translated and translated != text:
            return translated
    except Exception:
        pass
    # Fallback for language engines whose locale is not in pycountry.
    return _auto_translate(text, lang)

def country_display(name):
    if name == "Global / not specified":
        return t("global_unspecified")
    return _iso_translation("iso3166-1", name)

def language_display(name):
    return _iso_translation("iso639-3", name)

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

RU_OPPORTUNITIES = {
    "nyas-junior-academy": {
        "category":"STEM-программа", "cost":"Бесплатно",
        "summary":"Онлайн STEM-челленджи с международными командами и STEM-наставниками.",
        "eligibility":"Возраст 13–17 лет; онлайн; требуется английский. У циклов подачи есть дедлайны.",
        "checklist":["Проверьте текущий цикл подачи.", "Подготовьте короткое объяснение ваших STEM-интересов.", "Соберите один пример проекта или исследования.", "Запланируйте время для командной работы, если вас примут."],
    },
    "uwc-scholarships": {
        "category":"Стипендия / школьная возможность", "cost":"Доступна финансовая поддержка",
        "summary":"Маршрут в школы и колледжи UWC с need-based финансовой поддержкой через национальные комитеты.",
        "eligibility":"Правила отбора и сроки зависят от национального комитета; проверьте локальный маршрут перед подачей.",
        "checklist":["Найдите национальный комитет своей страны.", "Проверьте локальные возрастные правила и дедлайны.", "Соберите доказательства инициативы, служения сообществу и академической готовности.", "Изучите процесс финансовой поддержки."],
    },
    "schoolhouse": {
        "category":"Бесплатные занятия / помощь с поступлением", "cost":"Бесплатно",
        "summary":"Бесплатные peer-led занятия, SAT-подготовка, помощь с домашними заданиями и workshops по поступлению.",
        "eligibility":"Доступ онлайн; у отдельных программ могут быть свои требования.",
        "checklist":["Выберите один конкретный учебный или admissions-вопрос.", "Подготовьте точное место, где вы застряли.", "Выберите подходящую сессию.", "После неё запишите один следующий шаг."],
    },
    "khan": {
        "category":"Обучение / подготовка к экзаменам", "cost":"Бесплатно",
        "summary":"Бесплатное обучение и практика по математике, естественным наукам и подготовке к экзаменам.",
        "eligibility":"Открытый онлайн-доступ; доступность курсов и языков зависит от предмета.",
        "checklist":["Выберите навык, связанный с вашим маршрутом.", "Пройдите короткую диагностику.", "Запишите ошибки по темам.", "Сначала вернитесь к самой слабой теме."],
    },
}

def localized_opportunity(o):
    if interface_lang() != "ru":
        return o
    out = dict(o)
    out.update(RU_OPPORTUNITIES.get(o.get("id"), {}))
    return out

# -------------------- Lightweight persistence --------------------
# This demo persists non-sensitive profile choices and progress in a compressed URL token.
# Free-text support/community messages are intentionally NOT persisted.
PERSIST_KEYS = [
    "page", "profile", "completed_modules", "saved_opportunities", "support_request_count",
    "lesson_progress", "saved_actions", "admissions_plan", "requirements_checked", "exam_tracker", "interface_lang"
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
        "interface_lang": st.session_state.get("interface_lang", "en"),
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
        st.session_state.interface_lang = restored.get("interface_lang", "ru" if (restored.get("profile") or {}).get("language") == "Russian" else "en")


# -------------------- Curated admissions profiles --------------------
# These records are deliberately explicit and source-linked. They let the MVP
# show what a production Opportunity Navigator should feel like: the learner
# sees the requirement directly, while the official page remains available as
# evidence rather than being the main place where the learner has to research.
CURATED_ADMISSIONS = {
    "mbzuai_bsc_ai_business_2027": {
        "match_terms": ["mbzuai", "mohamed bin zayed university of artificial intelligence"],
        "program_terms": ["artificial intelligence", "ai", "business"],
        "university": "Mohamed bin Zayed University of Artificial Intelligence (MBZUAI)",
        "program": "Bachelor of Science in Artificial Intelligence (Business)",
        "country": "United Arab Emirates",
        "entry_year": 2027,
        "year_specific": True,
        "verified_date": "26 Sep 2026",
        "sources": {
            "admissions": "https://mbzuai.ac.ae/admissions/undergraduate-admissions",
            "program": "https://mbzuai.ac.ae/academics/undergraduate-program/bachelor-in-artificial-intelligence-business",
            "faq": "https://mbzuai.ac.ae/about-us/frequently-asked-questions/admissions",
        },
        "academic": [
            {"label":"Secondary-school qualification", "value":"Recognized secondary / high-school qualification; final-year students may apply with predicted or provisional results.", "status":"required"},
            {"label":"Overall academic average", "value":"Minimum overall average of 90% or equivalent, depending on curriculum and the competitiveness of the cycle.", "status":"required"},
            {"label":"Mathematics", "value":"Mathematics should be studied in the final two years of high school, preferably at the most advanced level offered. Strong mathematics and science performance is expected.", "status":"required"},
            {"label":"Coding experience", "value":"Not required for entry. Demonstrated coding / GitHub work can strengthen the application and may support exemption from elementary programming courses.", "status":"optional"},
        ],
        "tests": [
            {"name":"MBZUAI online screening exam", "required":"Required for applicants unless a published waiver condition is met.", "score":"No admission pass-score minimum is published on the current public admissions page.", "note":"The exam covers Math; Computational Thinking & Logic; Programming Fundamentals; and Data & AI Reasoning.", "source":"admissions"},
            {"name":"SAT", "required":"Not required for admission.", "score":"For screening-exam waiver: SAT Math 760 AND SAT total 1400.", "note":"Both thresholds must be met. An eligible international Olympiad medal can also qualify for a screening-exam waiver.", "source":"admissions"},
            {"name":"IELTS Academic", "required":"Accepted proof of English proficiency when an exemption does not apply.", "score":"6.5 minimum overall", "note":"Must be taken at an approved physical test center.", "source":"admissions"},
            {"name":"TOEFL iBT", "required":"Accepted proof of English proficiency when an exemption does not apply.", "score":"90 / 4.5 minimum as currently listed by MBZUAI", "note":"Must be taken at an approved physical test center.", "source":"admissions"},
            {"name":"PTE Academic", "required":"Accepted proof of English proficiency when an exemption does not apply.", "score":"60 minimum overall", "note":"Official result must be valid at application time.", "source":"admissions"},
            {"name":"Cambridge C1 Advanced", "required":"Accepted proof of English proficiency when an exemption does not apply.", "score":"180 minimum overall", "note":"Official result must be valid at application time.", "source":"admissions"},
            {"name":"Cambridge C2 Proficiency", "required":"Accepted proof of English proficiency when an exemption does not apply.", "score":"200 minimum overall", "note":"Official result must be valid at application time.", "source":"admissions"},
            {"name":"Duolingo English Test", "required":"Accepted only when access to IELTS / TOEFL / PTE / Cambridge is limited.", "score":"120 minimum overall", "note":"Evidence of limited access to other English tests may be requested.", "source":"admissions"},
        ],
        "screening_topics": {
            "Math": ["Algebra", "Functions", "Probability", "Statistics", "Matrices & Vectors", "Calculus", "Discrete Mathematics"],
            "Computational Thinking & Logic": ["Logic", "Pattern Recognition"],
            "Programming Fundamentals": ["Algorithmic Problem Solving", "Basic Syntax Concepts", "Functions", "Basic Data Structures"],
            "Data & AI Reasoning": ["Data Interpretation", "Basic Machine Learning Concepts"],
        },
        "dates": [
            ("Application portal opens", "7 Sep 2026, 8:00 a.m. GST"),
            ("Early Action deadline", "1 Nov 2026, 5:00 p.m. GST"),
            ("Early Action decision release", "15 Jan 2027, 5:00 p.m. GST"),
            ("Regular Decision deadline", "1 Feb 2027, 5:00 p.m. GST"),
            ("Regular Decision decision release", "1 Apr 2027, 5:00 p.m. GST"),
            ("Fall 2027 semester", "Begins in mid-August 2027"),
        ],
        "documents": [
            ("Academic records", "Official secondary-school transcripts; predicted/provisional results may be used while final results are pending."),
            ("Personal statement", "Required. It should explain interest in AI, academic/personal experiences, goals, achievements, extracurricular involvement and fit with MBZUAI."),
            ("CV / resume", "Required on the current undergraduate admissions page; include education, achievements, activities and work experience where relevant."),
            ("Recommendation letters", "Recommended but not mandatory on the program page; up to two teachers, mentors or supervisors may be nominated."),
            ("Technical portfolio / GitHub", "Recommended but not mandatory. Relevant projects can strengthen the application."),
            ("Video statement", "Recommended: a brief video describing interest in the program, goals and intended use of the knowledge."),
            ("Interview", "Shortlisted applicants are invited to an online faculty interview; current FAQ describes the interview as a mandatory part of evaluation for shortlisted applicants."),
        ],
        "fees_aid": [
            ("Application fee", "AED 200 after completing the screening exam."),
            ("Fee waiver", "Available if screening-exam score is 75% or above, the applicant enrolls (reimbursement), or the undergraduate screening exam is waived."),
            ("Scholarships", "Merit-based and need-based scholarships are available, covering up to 100% of tuition and cost of attendance."),
            ("Tuition", "$45,000 USD per year plus additional cost of attendance, before scholarship support."),
        ],
        "recommended_courses": [
            "An Intuitive Introduction to Probability",
            "Computational Thinking for Problem Solving",
            "Machine Learning Introduction for Everyone",
            "Mathematics for Machine Learning: Linear Algebra",
            "Programming for Everybody (Getting Started with Python)",
            "Introduction to Calculus",
        ],
        "portfolio_signals": [
            "Strong mathematics / STEM performance",
            "Problem-solving evidence",
            "Communication skills",
            "Leadership or entrepreneurial initiative",
            "Technical projects / GitHub (helpful, not mandatory)",
            "Research, competitions, community engagement or other evidence of initiative",
        ],
    },
    "iau_industrial_engineering_2027": {
        "match_terms": ["istanbul aydin", "istanbul aydın", "aydin university", "aydın university", "университет айдын", "стамбульский университет айдын", "айдын"],
        "program_terms": ["industrial engineering", "промышленная инженерия", "endüstri mühendisliği", "engineering"],
        "university": "Istanbul Aydın University (IAU)",
        "program": "Industrial Engineering",
        "country": "Türkiye",
        "entry_year": 2027,
        "year_specific": False,
        "verified_date": "26 Sep 2026",
        "sources": {
            "program": "https://study.aydin.edu.tr/industrial-engineering/",
            "admissions": "https://study.aydin.edu.tr/how-to-apply/",
            "faq": "https://study.aydin.edu.tr/faq/",
            "guideline": "https://study.aydin.edu.tr/wp-content/uploads/2022/06/ING-Guideline-2022.pdf",
        },
        "academic": [
            {"label":"Program format", "value":"Industrial Engineering is an English-taught undergraduate program with a published duration of 48 months at Florya Campus.", "status":"required"},
            {"label":"Online application documents", "value":"The current How to Apply page asks for a valid passport, high-school diploma and high-school transcript for the online application.", "status":"required"},
            {"label":"Application fee", "value":"The current international admissions page says there is no application fee.", "status":"required"},
            {"label":"Program-language proficiency", "value":"Students must take the proficiency exam for the language of their program unless they provide accepted proof of proficiency.", "status":"required"},
            {"label":"High-school average", "value":"An older official 2022 international-student guideline listed a minimum 60% high-school average for associate/bachelor applicants. This is historical evidence and must be re-verified for the 2027 intake before relying on it.", "status":"historical"},
        ],
        "tests": [
            {"name":"TOEFL iBT", "required":"Accepted current English-proficiency evidence; Home Edition is not accepted according to the current FAQ.", "score":"79 in the university's 2022 official undergraduate guideline — re-verify for 2027.", "note":"The current FAQ confirms TOEFL iBT is accepted but does not publish the undergraduate minimum score on that page.", "source":"faq"},
            {"name":"PTE", "required":"Accepted current English-proficiency evidence.", "score":"55 in the university's 2022 official undergraduate guideline — re-verify for 2027.", "note":"The current FAQ confirms PTE is accepted but does not publish the undergraduate minimum score on that page.", "source":"faq"},
            {"name":"YÖKDİL / YDS", "required":"Listed as accepted English certificates on the current FAQ.", "score":"No current undergraduate minimum was found on the public FAQ page.", "note":"Do not invent a score; verify the current undergraduate threshold with IAU before applying.", "source":"faq"},
            {"name":"IAU English Proficiency Exam", "required":"Alternative route when an applicant does not provide accepted proof of English proficiency.", "score":"A current undergraduate admission pass threshold is not published on the pages used for this record.", "note":"The university publishes exam dates separately for registered students.", "source":"admissions"},
        ],
        "screening_topics": {},
        "dates": [
            ("Fall application window", "The current FAQ says 1 Apr – 30 Sep each year."),
            ("Fall final registration", "The current FAQ says 15 Jun – 30 Sep each year."),
            ("2027 intake", "Re-check the university's current calendar before acting because annual dates can change."),
        ],
        "documents": [
            ("Passport", "Required for the online application according to the current How to Apply page."),
            ("High-school diploma", "Required for the online application; registration may require translation/notarization and equivalency documents."),
            ("High-school transcript", "Required for the online application; registration may require translated/notarized copies."),
            ("Language proficiency", "Provide accepted proof or take the university's proficiency exam for the program language."),
            ("Application portal", "The current international admissions site links to IAU's online application portal."),
        ],
        "fees_aid": [
            ("Application fee", "No application fee on the current international How to Apply page."),
            ("Scholarship / aid", "No universal scholarship amount for this program is asserted in this curated record. Check the current official scholarship/tuition information before planning finances."),
        ],
        "recommended_courses": [
            "Calculus / advanced school mathematics",
            "Physics fundamentals",
            "Algorithmic thinking and introductory programming",
            "Technical drawing / spatial reasoning",
            "English academic vocabulary for engineering",
        ],
        "portfolio_signals": [
            "Strong mathematics evidence",
            "Problem-solving or engineering project",
            "Programming / data-analysis evidence",
            "Teamwork and communication",
            "A measurable project result or iteration after feedback",
        ],
    }
}

CURATED_RU = {
    "mbzuai_bsc_ai_business_2027": {
        "university":"Университет искусственного интеллекта имени Мохаммеда бин Заида (MBZUAI)",
        "program":"Бакалавр искусственного интеллекта — Business stream",
        "verified_date":"26 сентября 2026",
        "academic":[
            {"label":"Аттестат / школьная квалификация", "value":"Нужна признанная квалификация средней школы. Ученики выпускного класса могут подавать прогнозируемые или предварительные результаты.", "status":"required"},
            {"label":"Средний академический результат", "value":"Опубликованный ориентир: минимум 90% или эквивалент, с учётом школьной системы и конкурсности набора.", "status":"required"},
            {"label":"Математика", "value":"Математика должна изучаться в последние два года школы, желательно на самом продвинутом доступном уровне. Ожидаются сильные результаты по математике и естественным наукам.", "status":"required"},
            {"label":"Опыт программирования", "value":"Для поступления не обязателен. Проекты / GitHub могут усилить заявку и потенциально помочь с освобождением от базовых курсов программирования.", "status":"optional"},
        ],
        "tests":[
            {"name":"Онлайн screening exam MBZUAI", "required":"Обязателен, если кандидат не подходит под опубликованное условие освобождения.", "score":"Публичный минимальный проходной балл для поступления сейчас не опубликован.", "note":"Экзамен охватывает математику, вычислительное мышление и логику, основы программирования, а также Data & AI Reasoning.", "source":"admissions"},
            {"name":"SAT", "required":"Для поступления не обязателен.", "score":"Для освобождения от screening exam: SAT Math 760 И общий SAT 1400.", "note":"Нужно выполнить оба порога. Некоторые международные олимпиадные медали также могут дать освобождение.", "source":"admissions"},
            {"name":"IELTS Academic", "required":"Принимается как подтверждение английского, если освобождение от языкового требования не применяется.", "score":"Минимум 6.5 overall", "note":"Экзамен должен быть сдан в одобренном очном тестовом центре.", "source":"admissions"},
            {"name":"TOEFL iBT", "required":"Принимается как подтверждение английского.", "score":"Минимум 90 / 4.5 — в текущей формулировке MBZUAI", "note":"Экзамен должен быть сдан в одобренном очном тестовом центре.", "source":"admissions"},
            {"name":"PTE Academic", "required":"Принимается как подтверждение английского.", "score":"Минимум 60 overall", "note":"Результат должен быть действителен на момент подачи.", "source":"admissions"},
            {"name":"Cambridge C1 Advanced", "required":"Принимается как подтверждение английского.", "score":"Минимум 180 overall", "note":"Результат должен быть действителен на момент подачи.", "source":"admissions"},
            {"name":"Cambridge C2 Proficiency", "required":"Принимается как подтверждение английского.", "score":"Минимум 200 overall", "note":"Результат должен быть действителен на момент подачи.", "source":"admissions"},
            {"name":"Duolingo English Test", "required":"Допускается, когда доступ к IELTS / TOEFL / PTE / Cambridge ограничен.", "score":"Минимум 120 overall", "note":"Университет может попросить подтвердить ограниченный доступ к другим экзаменам.", "source":"admissions"},
        ],
        "screening_topics":{
            "Математика":["Алгебра", "Функции", "Вероятность", "Статистика", "Матрицы и векторы", "Математический анализ", "Дискретная математика"],
            "Вычислительное мышление и логика":["Логика", "Распознавание закономерностей"],
            "Основы программирования":["Алгоритмическое решение задач", "Базовый синтаксис", "Функции", "Базовые структуры данных"],
            "Работа с данными и AI":["Интерпретация данных", "Базовые понятия машинного обучения"],
        },
        "dates":[
            ("Открытие портала", "7 сентября 2026, 08:00 GST"),
            ("Early Action", "1 ноября 2026, 17:00 GST"),
            ("Решение Early Action", "15 января 2027, 17:00 GST"),
            ("Regular Decision", "1 февраля 2027, 17:00 GST"),
            ("Решение Regular Decision", "1 апреля 2027, 17:00 GST"),
            ("Начало Fall 2027", "Середина августа 2027"),
        ],
        "documents":[
            ("Школьные документы", "Официальные выписки/транскрипты; до финальных результатов допускаются прогнозируемые или предварительные результаты."),
            ("Personal statement", "Требуется. Нужно связать интерес к AI, опыт, цели, достижения, внеучебную активность и соответствие MBZUAI."),
            ("CV / resume", "Требуется на текущей странице undergraduate admissions; укажите образование, достижения, активности и опыт работы, если он есть."),
            ("Рекомендательные письма", "Рекомендуются, но не обязательны; можно указать до двух преподавателей, наставников или руководителей."),
            ("Техническое портфолио / GitHub", "Рекомендуется, но не является обязательным. Релевантные проекты могут усилить заявку."),
            ("Видео", "Рекомендуется короткое видео об интересе к программе, целях и том, как вы хотите использовать знания."),
            ("Интервью", "Кандидатов из shortlist приглашают на онлайн-интервью с преподавателями."),
        ],
        "fees_aid":[
            ("Сбор за заявку", "AED 200 после прохождения screening exam."),
            ("Освобождение от сбора", "Возможны опубликованные условия освобождения/возмещения, включая высокий результат screening exam или освобождение от него."),
            ("Стипендии", "Есть merit-based и need-based scholarships, вплоть до 100% tuition и стоимости обучения/проживания по опубликованным условиям."),
            ("Tuition", "$45,000 USD в год плюс дополнительные расходы до применения стипендии."),
        ],
        "recommended_courses":[
            "Интуитивное введение в вероятность", "Вычислительное мышление для решения задач", "Введение в машинное обучение",
            "Линейная алгебра для машинного обучения", "Programming for Everybody / Python", "Введение в математический анализ",
        ],
        "portfolio_signals":[
            "Сильные результаты по математике / STEM", "Доказательства умения решать задачи", "Коммуникационные навыки",
            "Лидерство или предпринимательская инициатива", "Технические проекты / GitHub (полезно, но не обязательно)",
            "Исследования, конкурсы, волонтёрство или другой подтверждённый опыт инициативы",
        ],
    },
    "iau_industrial_engineering_2027": {
        "university":"Стамбульский университет Айдын (Istanbul Aydın University, IAU)",
        "program":"Промышленная инженерия / Industrial Engineering",
        "verified_date":"26 сентября 2026",
        "academic":[
            {"label":"Формат программы", "value":"Industrial Engineering — программа бакалавриата на английском языке, опубликованная длительность 48 месяцев, кампус Florya.", "status":"required"},
            {"label":"Документы для онлайн-заявки", "value":"На текущей странице How to Apply указаны действующий паспорт, школьный диплом/аттестат и школьный transcript.", "status":"required"},
            {"label":"Сбор за заявку", "value":"На текущей международной странице поступления указано, что application fee отсутствует.", "status":"required"},
            {"label":"Язык программы", "value":"Если абитуриент не предоставляет принимаемое подтверждение языка программы, университет требует пройти языковой proficiency exam.", "status":"required"},
            {"label":"Средний школьный балл", "value":"В официальном международном guideline 2022 года был указан минимум 60% для associate/bachelor applicants. Это историческое официальное значение: его нужно перепроверить для набора 2027.", "status":"historical"},
        ],
        "tests":[
            {"name":"TOEFL iBT", "required":"В текущем FAQ указан как принимаемое подтверждение английского; Home Edition не принимается.", "score":"79 — в официальном undergraduate guideline 2022 года; обязательно перепроверить для 2027.", "note":"Текущий FAQ подтверждает сам экзамен, но не публикует undergraduate minimum на этой странице.", "source":"faq"},
            {"name":"PTE", "required":"В текущем FAQ указан как принимаемое подтверждение английского.", "score":"55 — в официальном undergraduate guideline 2022 года; обязательно перепроверить для 2027.", "note":"Текущий FAQ подтверждает сам экзамен, но не публикует undergraduate minimum на этой странице.", "source":"faq"},
            {"name":"YÖKDİL / YDS", "required":"Указаны в текущем FAQ среди принимаемых сертификатов английского.", "score":"Текущий undergraduate minimum на используемой публичной странице не найден.", "note":"Платформа не придумывает число — нужно проверить действующий порог у IAU перед подачей.", "source":"faq"},
            {"name":"Внутренний English Proficiency Exam IAU", "required":"Альтернативный путь, если абитуриент не предоставляет принимаемое подтверждение английского.", "score":"Текущий публичный проходной порог для undergraduate admission на используемых страницах не опубликован.", "note":"Даты экзамена университет публикует отдельно для зарегистрированных студентов.", "source":"admissions"},
        ],
        "screening_topics":{},
        "dates":[
            ("Приём на Fall intake", "Текущий FAQ указывает ежегодное окно 1 апреля – 30 сентября."),
            ("Финальная регистрация Fall", "Текущий FAQ указывает 15 июня – 30 сентября."),
            ("Набор 2027", "Перед подачей нужно проверить календарь 2027, потому что ежегодные даты могут измениться."),
        ],
        "documents":[
            ("Паспорт", "Нужен для онлайн-заявки по текущей странице How to Apply."),
            ("Школьный диплом / аттестат", "Нужен для онлайн-заявки; при финальной регистрации могут потребоваться перевод, нотариальное заверение и документ об эквивалентности."),
            ("Школьный transcript", "Нужен для онлайн-заявки; для регистрации могут понадобиться переведённые/заверенные копии."),
            ("Подтверждение языка", "Предоставьте принимаемый сертификат или сдайте внутренний proficiency exam для языка программы."),
            ("Портал подачи", "Текущий международный сайт IAU ведёт на официальный онлайн-портал подачи заявки."),
        ],
        "fees_aid":[
            ("Сбор за заявку", "На текущей странице How to Apply указан application fee = 0."),
            ("Стипендии / помощь", "В этой проверенной карточке не заявляется универсальная сумма стипендии для программы. Финансовые условия нужно сверять с текущей официальной страницей tuition/scholarship."),
        ],
        "recommended_courses":[
            "Математический анализ / сильная школьная математика", "Основы физики", "Алгоритмическое мышление и вводное программирование",
            "Техническое черчение / пространственное мышление", "Академический английский для инженерии",
        ],
        "portfolio_signals":[
            "Сильная математика", "Инженерный или problem-solving проект", "Программирование / анализ данных",
            "Командная работа и коммуникация", "Проект с измеримым результатом или улучшением после обратной связи",
        ],
    },
}

def localized_curated(curated):
    if interface_lang() != "ru":
        return curated
    key = curated.get("_key")
    override = CURATED_RU.get(key)
    if not override:
        return curated
    merged = dict(curated)
    for field, value in override.items():
        merged[field] = value
    return merged

def curated_admissions_profile(plan):
    """Return a structured admissions profile when the target matches a curated university/program."""
    university = (plan.get("university") or "").lower().strip()
    program = (plan.get("program") or "").lower().strip()
    year = int(plan.get("year") or 0)
    for key, profile in CURATED_ADMISSIONS.items():
        university_match = any(term.lower() in university for term in profile["match_terms"])
        program_hits = sum(1 for term in profile["program_terms"] if term.lower() in program)
        year_ok = (not profile.get("year_specific", True)) or (not year) or year == profile["entry_year"]
        if university_match and program_hits >= 1 and year_ok:
            out = dict(profile)
            out["_key"] = key
            return out
    return None

def status_badge(label):
    labels = {
        "required": ui("Required", "Обязательно"),
        "optional": ui("Helpful / optional", "Полезно / необязательно"),
        "historical": ui("Re-verify for 2027", "Нужно перепроверить для 2027"),
    }
    value = labels.get(label, "")
    return f"<span class='pill'>{value}</span>" if value else ""


# -------------------- Session state --------------------
defaults = {
    "page":"Home", "profile":None, "completed_modules":set(), "saved_opportunities":set(),
    "support_request_count":0, "support_requests":[], "community_submissions":[],
    "tutor_session":None, "lesson_progress":{}, "saved_actions":[], "admissions_plan":{},
    "portfolio_items":[], "requirements_checked":set(), "exam_tracker":[], "interface_lang":"en",
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
PAGE_LABEL_KEY = {
    "Home":"nav_home", "My Pathway":"nav_path", "AI Tutor":"nav_tutor", "Learning Hub":"nav_learning",
    "Motivation":"nav_motivation", "Human Support":"nav_support", "Community":"nav_community",
    "Opportunities":"nav_opportunities", "University Planner":"nav_university", "Profile":"nav_profile", "About the Project":"nav_about",
}

def nav_to(name):
    st.session_state.page = name
    sync_persistence()
    st.rerun()

def btn_nav(label, target, key, primary=False):
    if st.button(label, key=key, type="primary" if primary else "secondary", use_container_width=True):
        nav_to(target)

st.sidebar.markdown("<div class='site-title'>🧭 Opportunity Navigator</div>", unsafe_allow_html=True)
# Language is independent from country. A learner in Kazakhstan, Türkiye or Norway can still choose Russian.
_language_names = list(INTERFACE_LANG_OPTIONS.keys())
_current_lang_code = st.session_state.get("interface_lang", "en")
_current_lang_name = next((name for name, code in INTERFACE_LANG_OPTIONS.items() if code == _current_lang_code), _language_names[0])
_selected_lang_name = st.sidebar.selectbox(
    "🌐 Language / Язык / Dil / اللغة / Idioma",
    _language_names,
    index=_language_names.index(_current_lang_name),
    key="interface_language_selector",
)
_selected_lang_code = INTERFACE_LANG_OPTIONS[_selected_lang_name]
if _selected_lang_code != st.session_state.get("interface_lang", "en"):
    st.session_state.interface_lang = _selected_lang_code
    sync_persistence()
    st.rerun()

_selected_native = _selected_lang_name.split(" — ")[0].strip()
st.sidebar.markdown(
    f"<div class='language-badge'>✓ {CORE_UI_FALLBACK.get(interface_lang(), {}).get('selected_language', ui('Selected language', 'Выбранный язык'))}: {_selected_native}</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(f"<div class='site-sub'>{t('sidebar_sub')}</div>", unsafe_allow_html=True)
for name, icon in NAV:
    display_name = t(PAGE_LABEL_KEY[name])
    label = f"{'🔵' if st.session_state.page == name else '⚪'}  {icon} {display_name}"
    if st.sidebar.button(label, key=f"nav_{name}", use_container_width=True):
        st.session_state.page = name
        sync_persistence()
        st.rerun()

st.sidebar.markdown("---")
if st.session_state.profile:
    p = st.session_state.profile
    st.sidebar.caption(t("profile_caption", age=p['age'], country=country_display(p['country']), language=language_display(p['language'])))
else:
    st.sidebar.caption(t("create_profile_caption"))
st.sidebar.caption(f"Prototype v{VERSION}")

with st.sidebar.expander(t("save_restore")):
    st.caption(ui("Profile selections and counters survive refresh through a compact state token in the URL. Free-text messages are not stored there.", "Основные настройки и счётчики сохраняются после обновления страницы. Текст сообщений не хранится в URL."))
    export_data = json.dumps(_jsonable(persistent_snapshot()), ensure_ascii=False, indent=2)
    st.download_button(t("export_progress"), export_data, file_name="opportunity_navigator_progress.json", mime="application/json", use_container_width=True)
    uploaded = st.file_uploader(t("import_progress"), type=["json"], key="progress_import")
    if uploaded is not None and st.button(t("restore_progress"), use_container_width=True):
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
            st.success(t("progress_restored"))
            st.rerun()
        except Exception:
            st.error(ui("That file could not be restored."))
    if st.button(t("reset_progress"), use_container_width=True):
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
    base = localize_tutor_base(base)
    if variant == "hint" or help_style == "Guide me with hints":
        focus = base.get("hint", focus)
    elif variant == "example" or help_style == "Show an example":
        focus = base.get("example", focus)
    else:
        focus = base.get("simple", focus)
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
    ru = interface_lang() == "ru"
    if not q:
        return "Напишите точный шаг, который всё ещё непонятен." if ru else "Tell me the exact step that is still unclear."
    if subject == "Math" and ("linear" in topic_l or "equation" in topic_l):
        if any(x in q for x in ["why subtract", "why do we subtract", "sign change", "move the", "other side"]):
            return ("Представьте уравнение как весы. Мы не «переносим» число и не меняем знак магически — мы выполняем одну и ту же операцию с обеими частями. Для 2x + 3 = 11 вычтите 3 из обеих частей: 2x + 3 − 3 = 11 − 3, поэтому 2x = 8." if ru else
                    "Think of an equation as a balanced scale. We are not literally moving a number and changing its sign. We do the same operation to both sides. For 2x + 3 = 11, subtract 3 from both sides: 2x + 3 − 3 = 11 − 3, so 2x = 8.")
        if any(x in q for x in ["why divide", "divide by", "coefficient"]):
            return ("После 2x = 8 переменная x умножена на 2. Обратная операция — деление, поэтому делим обе части на 2: 2x/2 = 8/2, получаем x = 4." if ru else
                    "After you get 2x = 8, x is being multiplied by 2. The inverse operation is division, so divide both sides by 2: 2x/2 = 8/2, giving x = 4.")
        if "check" in q or "know" in q:
            return "Подставьте ответ обратно в исходное уравнение. Если x = 4, то 2×4 + 3 = 11 — значит ответ проверен." if ru else "Substitute the answer back into the original equation. If x = 4, then 2×4 + 3 = 11, so it checks."
    if subject == "Math" and ("graph" in topic_l or "function" in topic_l):
        if "slope" in q:
            return "Наклон показывает, на сколько меняется y, когда x увеличивается на 1. В y = 2x + 1 наклон равен 2." if ru else "Slope tells you how much y changes when x increases by 1. In y = 2x + 1, the slope is 2."
        if any(x in q for x in ["plot", "point", "where"]):
            return "Выберите значение x, вычислите y и отметьте пару (x, y). Повторите для ещё двух-трёх значений x." if ru else "Choose an x-value, calculate y, and plot the pair (x, y). Repeat for two or three x-values."
    if subject == "English" and "article" in topic_l:
        if "university" in q:
            return "Используйте 'a university', потому что university начинается со звука /y/, как 'you', а не с гласного звука." if ru else "Use 'a university' because university begins with a /y/ sound, like 'you', not a vowel sound."
        if "the" in q:
            return "Используйте 'the', когда слушателю понятно, о каком конкретном предмете речь — например, он уже упоминался или очевиден из контекста." if ru else "Use 'the' when the listener can identify the specific noun you mean, often because it was mentioned before or is obvious from context."
    if subject == "Coding" and "loop" in topic_l:
        if "range" in q:
            return "В Python range(n) начинается с 0 и останавливается перед n. Поэтому range(3) даёт 0, 1, 2." if ru else "In Python, range(n) starts at 0 and stops before n. So range(3) gives 0, 1, 2."
        return "Разберите цикл по одному повторению: запишите текущее значение и результат каждого прохода." if ru else "Trace the loop one repetition at a time. Write down the current value and the output for each pass."
    if subject == "University applications":
        return ("Превратите вопрос в задачу проверки: укажите точную программу, год набора и официальную страницу, затем сохраните требование, ссылку-источник и дату проверки." if ru else
                "Turn the question into a verification task: identify the exact course, intake year and official page, then record the requirement, the source link and the date you checked it.")
    return base.get("hint") or base.get("simple") or ("Разбейте задачу на один маленький шаг и скажите, какая связь непонятна." if ru else "Break the problem into one small step and tell me which connection is missing.")


def _extract_json_object(text):
    if not isinstance(text, str):
        return None
    raw = text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end+1])
        except Exception:
            return None
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def deep_research_university_openai(country, university, program, level, year, official_url=""):
    """Research admissions with a web-search capable model. Numeric claims must carry an official source URL."""
    key = _openai_api_key()
    if not key or OpenAI is None:
        return None
    allowed = []
    if official_url and is_safe_public_url(official_url):
        host = _host(official_url)
        if host:
            allowed = [host]
    tools = [{"type":"web_search", "search_context_size":"high"}]
    if allowed:
        tools[0]["filters"] = {"allowed_domains": allowed}
    prompt = f"""
You are an admissions research assistant inside an education platform.
Research the OFFICIAL university website for this target:
Country: {country}
University: {university}
Programme/course: {program}
Study level: {level}
Target entry year: {year}
Known official URL: {official_url or 'not provided'}

Search deeply across official admissions pages, programme pages, FAQs, PDFs, international admissions pages, scholarship pages and contact pages.
Find programme-specific information whenever possible, not just general university admissions.

Return ONLY valid JSON with this exact top-level shape:
{{
  "official_site": string_or_null,
  "programme": {{"name": string_or_null, "found": true_or_false, "language": string_or_null, "source_url": string_or_null}},
  "academic_requirements": [{{"requirement": string, "minimum": string_or_null, "source_url": string}}],
  "entrance_exams": [{{"exam": string, "required": true_or_false_or_null, "minimum_score": string_or_null, "details": string_or_null, "source_url": string}}],
  "english_tests": [{{"exam": string, "minimum_score": string_or_null, "waiver_or_notes": string_or_null, "source_url": string}}],
  "deadlines": [{{"label": string, "date": string_or_null, "cycle": string_or_null, "source_url": string}}],
  "documents": [{{"item": string, "required": true_or_false_or_null, "details": string_or_null, "source_url": string}}],
  "scholarships": [{{"name": string, "coverage_or_eligibility": string_or_null, "source_url": string}}],
  "contacts": {{"emails": [string], "phones": [string], "contact_page": string_or_null}},
  "not_found": [string],
  "notes": [string]
}}

Rules:
- Use official university sources for admissions facts.
- Never invent a minimum score, deadline, document, exam or scholarship.
- If an exact numeric score is not published, use null and explain in notes/not_found.
- Prefer information for {year}; if that cycle is not yet published, use the latest official cycle and clearly say so in the cycle/notes field.
- Every factual requirement/exam/deadline/document/scholarship item must include its specific official source_url.
- Distinguish required exams from optional/accepted exams and from competitive guidance.
- Search for SAT, ACT, IELTS, TOEFL, PTE, Duolingo, IB, A-levels, national exams and programme-specific tests where relevant.
- Return no prose outside the JSON.
"""
    try:
        client = OpenAI(api_key=key, timeout=120.0)
        response = client.responses.create(model=_openai_model(), tools=tools, input=prompt)
        data = _extract_json_object(response.output_text or "")
        if not isinstance(data, dict):
            return None
        data["research_mode"] = "deep_web_search"
        return data
    except Exception:
        return None

def _source_button(label, url, key):
    if url and is_safe_public_url(url):
        st.link_button(label + " ↗", url, key=key)

def render_deep_research(data):
    if not data:
        return
    st.markdown("### " + ui("Programme found", "Найденная программа"))
    pr = data.get("programme") or {}
    if pr.get("found"):
        st.write("**" + lx(pr.get("name") or "Programme") + "**")
        if pr.get("language"):
            st.write(ui("Language of instruction", "Язык обучения") + ": " + lx(pr.get("language")))
        _source_button(ui("Official programme page", "Официальная страница программы"), pr.get("source_url"), "deep_program")
    else:
        st.info(ui("The exact programme page was not confirmed. General university admissions information is shown below where available.", "Точную страницу программы подтвердить не удалось. Ниже показана общая информация о поступлении в университет, если она найдена."))

    sections = [
        ("Academic requirements", "Академические требования", "academic_requirements", "requirement", "minimum"),
        ("Entrance exams", "Вступительные экзамены", "entrance_exams", "exam", "minimum_score"),
        ("English-language tests", "Экзамены по английскому языку", "english_tests", "exam", "minimum_score"),
        ("Application deadlines", "Сроки подачи", "deadlines", "label", "date"),
        ("Application documents", "Документы для поступления", "documents", "item", "details"),
        ("Scholarships / financial aid", "Стипендии / финансовая помощь", "scholarships", "name", "coverage_or_eligibility"),
    ]
    for en_title, ru_title, keyname, main_key, detail_key in sections:
        rows = data.get(keyname) or []
        st.markdown("### " + ui(en_title, ru_title))
        if not rows:
            st.caption(ui("No verified item was found in this category.", "В этой категории подтверждённая информация не найдена."))
            continue
        for i, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            main = row.get(main_key) or row.get("details") or row.get("label") or "—"
            detail = row.get(detail_key)
            if keyname == "entrance_exams" and row.get("required") is not None:
                req = ui("Required", "Обязателен") if row.get("required") else ui("Accepted / not confirmed as required", "Принимается / не подтверждён как обязательный")
                detail = (str(detail) + " · " if detail else "") + req
            if keyname == "documents" and row.get("required") is not None:
                req = ui("Required", "Обязательный") if row.get("required") else ui("Optional / not confirmed as required", "Необязательный / обязательность не подтверждена")
                detail = (str(detail) + " · " if detail else "") + req
            st.markdown(f"**{lx(str(main))}**" + (f" — {lx(str(detail))}" if detail else ""))
            extra = row.get("details") or row.get("waiver_or_notes") or row.get("cycle")
            if extra and str(extra) != str(detail):
                st.write(lx(str(extra)))
            _source_button(ui("Official source", "Официальный источник"), row.get("source_url"), f"deep_{keyname}_{i}")

    not_found = data.get("not_found") or []
    if not_found:
        st.markdown("### " + ui("What could not be verified", "Что не удалось подтвердить"))
        for item in not_found:
            st.write("• " + lx(str(item)))

    contacts = data.get("contacts") or {}
    if contacts.get("emails") or contacts.get("phones") or contacts.get("contact_page"):
        st.markdown("### " + ui("Official admissions contacts", "Официальные контакты приёмной комиссии"))
        for email in contacts.get("emails") or []:
            st.write(f"• `{email}`")
        for phone in contacts.get("phones") or []:
            st.write(f"• `{phone}`")
        _source_button(ui("Contact page", "Страница контактов"), contacts.get("contact_page"), "deep_contact")

def _same_official_domain(url_a, url_b):
    try:
        a = (urlparse(url_a).hostname or "").lower().removeprefix("www.")
        b = (urlparse(url_b).hostname or "").lower().removeprefix("www.")
        return bool(a and b and (a == b or a.endswith("." + b) or b.endswith("." + a)))
    except Exception:
        return False

_NON_OFFICIAL_HOSTS = {
    "wikipedia.org", "facebook.com", "instagram.com", "linkedin.com", "youtube.com",
    "studyportals.com", "bachelorsportal.com", "mastersportal.com", "topuniversities.com",
    "usnews.com", "timeshighereducation.com", "reddit.com", "x.com", "twitter.com",
}

_UNIVERSITY_ENTITY_HINTS = (
    "university", "college", "institute", "academy", "higher education", "school of",
    "университет", "институт", "академ", "жоғары оқу", "университеті", "universitet",
    "universidad", "université", "universität", "üniversite",
)
_BAD_UNIVERSITY_HOST_HINTS = (
    "akorda", "president", "parliament", "government", "ministry", "senate", "legal", "law.gov",
)

def _host(url):
    try:
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""

def _looks_nonofficial(url):
    h = _host(url)
    return any(h == x or h.endswith("." + x) for x in _NON_OFFICIAL_HOSTS)

def _looks_like_education_entity(label="", description=""):
    text = f"{label} {description}".lower()
    if any(x in text for x in ["president of", "politician", "head of state", "businessman", "person"]):
        return False
    return any(hint in text for hint in _UNIVERSITY_ENTITY_HINTS)

def _university_site_plausibility(url, title="", university=""):
    if not url or not is_safe_public_url(url) or _looks_nonofficial(url):
        return -999
    h = _host(url)
    text = f"{title} {h}".lower()
    score = 0
    if any(bad in h for bad in _BAD_UNIVERSITY_HOST_HINTS):
        score -= 12
    if h.endswith(".edu") or ".edu." in h or ".ac." in h:
        score += 7
    if any(x in text for x in ["university", "univers", "college", "institute", "academy"]):
        score += 5
    if any(x in text for x in ["admission", "undergraduate", "bachelor", "apply"]):
        score += 3
    tokens = [x for x in re.findall(r"[A-Za-zÀ-ÿА-Яа-я0-9]+", (university or "").lower()) if len(x) >= 4]
    score += sum(4 for tok in tokens if tok in text)
    return score

@st.cache_data(ttl=86400, show_spinner=False)
def discover_official_site_wikidata(university, country=""):
    university = (university or "").strip()
    country = (country or "").strip()
    if not university:
        return None
    endpoint = "https://www.wikidata.org/w/api.php"
    headers = {"User-Agent": "OpportunityNavigator/1.3 educational-admissions-research"}
    queries = [f"{university} university", f"{university} университет"]
    if country and country != "Global / not specified":
        queries.insert(0, f"{university} university {country}")
    seen = set()
    candidates = []
    for query in queries:
        for lang in ("en", "ru"):
            try:
                r = requests.get(endpoint, params={
                    "action":"wbsearchentities", "search":query, "language":lang,
                    "format":"json", "limit":8, "type":"item",
                }, timeout=8, headers=headers)
                r.raise_for_status()
                items = r.json().get("search", [])
            except Exception:
                continue
            for rank, item in enumerate(items):
                qid = item.get("id")
                if not qid or qid in seen:
                    continue
                seen.add(qid)
                label = item.get("label") or ""
                description = item.get("description") or ""
                if not _looks_like_education_entity(label, description):
                    continue
                try:
                    d = requests.get(endpoint, params={
                        "action":"wbgetentities", "ids":qid, "props":"claims",
                        "format":"json",
                    }, timeout=8, headers=headers)
                    d.raise_for_status()
                    claims = d.json().get("entities", {}).get(qid, {}).get("claims", {})
                    for claim in claims.get("P856", []):
                        val = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
                        if not isinstance(val, str):
                            continue
                        sc = _university_site_plausibility(val, label, university) - rank * 0.25
                        if sc >= 3:
                            candidates.append((sc, val))
                except Exception:
                    continue
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return None

def _parse_jina_json(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    data = payload.get("data", payload.get("results", payload.get("items", [])))
    if isinstance(data, dict):
        data = data.get("data", data.get("results", data.get("items", [])))
    return data if isinstance(data, list) else []

@st.cache_data(ttl=3600, show_spinner=False)
def jina_search(query):
    """Global web search fallback. Jina Search can search across countries/languages."""
    if not query or not query.strip():
        return []
    headers = {
        "Accept":"application/json",
        "User-Agent":"OpportunityNavigator/1.0 educational-admissions-research",
    }
    urls = [
        ("https://s.jina.ai/", {"q": query}),
        ("https://s.jina.ai/" + quote_plus(query), None),
    ]
    for endpoint, params in urls:
        try:
            r = requests.get(endpoint, params=params, timeout=18, headers=headers)
            r.raise_for_status()
            ctype = r.headers.get("content-type", "")
            if "json" in ctype:
                items = _parse_jina_json(r.json())
                out = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url") or item.get("link")
                    if not url or not is_safe_public_url(url):
                        continue
                    out.append({
                        "title": item.get("title") or url,
                        "url": url,
                        "content": item.get("content") or item.get("description") or item.get("text") or "",
                    })
                if out:
                    return out[:8]
            # Plain-text fallback for Reader-style output.
            text = r.text or ""
            blocks = re.split(r"\n(?=Title:|URL Source:)", text)
            found = []
            current = {"title":"", "url":"", "content":""}
            for block in blocks:
                mt = re.search(r"Title:\s*(.+)", block)
                mu = re.search(r"URL Source:\s*(https?://\S+)", block)
                if mu:
                    current = {
                        "title": mt.group(1).strip() if mt else mu.group(1),
                        "url": mu.group(1).strip(),
                        "content": block[-8000:],
                    }
                    if is_safe_public_url(current["url"]):
                        found.append(current)
            if found:
                return found[:8]
        except Exception:
            continue
    return []

@st.cache_data(ttl=3600, show_spinner=False)
def jina_read(url):
    """Read difficult/JS-heavy pages through Jina Reader."""
    if not is_safe_public_url(url):
        return None
    endpoint = "https://r.jina.ai/" + url
    headers = {
        "Accept":"application/json",
        "User-Agent":"OpportunityNavigator/1.0 educational-admissions-research",
        "X-Timeout":"15",
    }
    try:
        r = requests.get(endpoint, timeout=22, headers=headers)
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "json" in ctype:
            payload = r.json()
            data = payload.get("data", payload) if isinstance(payload, dict) else {}
            content = data.get("content") if isinstance(data, dict) else None
            title = data.get("title") if isinstance(data, dict) else None
            final_url = data.get("url") if isinstance(data, dict) else url
            if content:
                return {"title": title or final_url, "url": final_url or url, "text": content}
        text = r.text or ""
        if len(text.strip()) > 100:
            title_match = re.search(r"^Title:\s*(.+)$", text, flags=re.M)
            return {"title": title_match.group(1).strip() if title_match else url, "url": url, "text": text}
    except Exception:
        return None
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_page_html(url):
    if not is_safe_public_url(url):
        raise ValueError("Only public http/https pages are allowed.")
    r = requests.get(url, timeout=10, allow_redirects=True, headers={
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    })
    r.raise_for_status()
    if "text/html" not in r.headers.get("content-type", ""):
        return None, r.url
    return BeautifulSoup(r.text, "html.parser"), r.url

@st.cache_data(ttl=3600, show_spinner=False)
def read_page_universal(url):
    """Direct read first; Jina Reader fallback when the official site blocks Streamlit."""
    if not is_safe_public_url(url):
        return None
    try:
        soup, final_url = fetch_page_html(url)
        if soup is not None:
            title = soup.title.get_text(" ", strip=True) if soup.title else final_url
            for tag in soup(["script","style","noscript","svg"]):
                tag.decompose()
            text = "\n".join(soup.stripped_strings)
            if len(text.strip()) >= 120:
                return {"title": title[:200], "url": final_url, "text": text[:180000], "via":"direct"}
    except Exception:
        pass
    page = jina_read(url)
    if page:
        page["text"] = (page.get("text") or "")[:180000]
        page["via"] = "reader"
        return page
    return None

def _candidate_link_score(label, href, program=""):
    s = (label + " " + href).lower()
    keywords = {
        "admission":7, "admissions":7, "undergraduate":7, "apply":5, "application":5,
        "entry-requirement":7, "requirements":7, "eligibility":6, "international":4,
        "english":4, "language":3, "ielts":6, "toefl":6, "scholarship":5,
        "financial-aid":5, "tuition":3, "deadline":4, "programme":4, "program":4,
        "course":3, "bachelor":4, "documents":4, "portfolio":3,
    }
    score = sum(weight for key, weight in keywords.items() if key in s)
    for token in re.findall(r"[A-Za-zÀ-ÿА-Яа-я0-9]+", (program or "").lower()):
        if len(token) >= 5 and token in s:
            score += 2
    return score

def _official_candidate_score(result, university, country=""):
    url = result.get("url", "")
    title = result.get("title", "")
    score = _university_site_plausibility(url, title, university)
    text = f"{title} {url}".lower()
    if country and country.lower() in text:
        score += 2
    return score

def discover_official_site_global(university, country="", program="", user_url=""):
    if user_url and is_safe_public_url(user_url):
        return user_url
    wd = discover_official_site_wikidata(university, country)
    if wd:
        return wd
    queries = [
        f'"{university}" university official website "{country}"',
        f'"{university}" official admissions "{program}"',
        f'"{university}" undergraduate admissions official',
    ]
    candidates = []
    for q_idx, q in enumerate(queries):
        for rank, result in enumerate(jina_search(q)):
            sc = _official_candidate_score(result, university, country)
            sc += max(0, 4 - rank) - q_idx * 0.25
            if sc >= 3:
                candidates.append((sc, result["url"]))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return None

def _admissions_relevance(title, url, text="", program=""):
    blob = f"{title} {url} {text[:1200]}".lower()
    positive = {
        "admission":7, "apply":5, "undergraduate":6, "bachelor":5, "entry requirement":7,
        "eligibility":5, "international student":5, "ielts":6, "toefl":6, "sat":5, "act":4,
        "duolingo":4, "pte":4, "scholarship":4, "deadline":4, "application":4,
        "program":2, "programme":2, "curriculum":2, "tuition":2,
    }
    negative = ["news", "press", "legal act", "decree", "president", "parliament", "newsroom", "media release"]
    score = sum(w for k, w in positive.items() if k in blob)
    score -= sum(8 for k in negative if k in blob)
    for token in re.findall(r"[A-Za-zÀ-ÿА-Яа-я0-9]+", (program or "").lower()):
        if len(token) >= 5 and token in blob:
            score += 2
    return score

def collect_official_candidate_pages(seed_url, university="", country="", program="", max_pages=12):
    """Multi-source admissions research:
    direct crawl -> same-domain Jina Search -> Jina Reader.
    """
    if not seed_url or not is_safe_public_url(seed_url):
        return []
    pages, seen = [], set()
    seed_host = _host(seed_url)

    def add_page(url, content_hint=""):
        if not url or url in seen or not is_safe_public_url(url):
            return
        # For discovered university research, keep pages on the same official host/subdomains.
        if seed_host and not _same_official_domain(url, seed_url):
            return
        seen.add(url)
        page = read_page_universal(url)
        if page and len((page.get("text") or "").strip()) >= 100:
            # Root page is allowed; subpages must look relevant to admissions/program research.
            rel = _admissions_relevance(page.get("title", ""), page.get("url", url), page.get("text", ""), program)
            if url.rstrip("/") == seed_url.rstrip("/") or rel >= 1:
                pages.append(page)

    add_page(seed_url)

    # Directly try common admissions paths.
    parsed = urlparse(seed_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    for path in [
        "/admissions", "/admissions/undergraduate", "/undergraduate", "/apply",
        "/international", "/international-students", "/scholarships", "/financial-aid",
        "/tuition", "/requirements", "/contact", "/contact-us", "/contacts",
        "/admissions/contact", "/international-office", "/international/contact",
    ]:
        if len(pages) >= max_pages:
            break
        add_page(root + path)

    # Search the official domain. This works even when the site blocks Streamlit's IP.
    search_queries = [
        f'site:{seed_host} "{program}" admissions requirements undergraduate',
        f'site:{seed_host} "{program}" entrance exam requirements',
        f'site:{seed_host} undergraduate admissions IELTS TOEFL PTE Duolingo',
        f'site:{seed_host} undergraduate admissions SAT ACT IB A-level',
        f'site:{seed_host} international applicants admission requirements PDF',
        f'site:{seed_host} scholarship financial aid international students',
        f'site:{seed_host} application deadline documents transcript recommendation portfolio',
        f'site:{seed_host} admissions contact email phone international office',
        f'site:{seed_host} contact us admissions international students',
    ]
    for q in search_queries:
        if len(pages) >= max_pages:
            break
        for result in jina_search(q):
            if len(pages) >= max_pages:
                break
            url = result.get("url")
            if url and _same_official_domain(url, seed_url):
                content = result.get("content") or ""
                rel = _admissions_relevance(result.get("title") or "", url, content, program)
                if rel < 1:
                    continue
                # Search results often already contain full content; use it immediately.
                if url not in seen and len(content.strip()) >= 200:
                    seen.add(url)
                    pages.append({
                        "title": result.get("title") or url,
                        "url": url,
                        "text": content[:180000],
                        "via":"search",
                    })
                elif url not in seen:
                    add_page(url)

    return pages[:max_pages]

def _valid_exam_score(exam, raw):
    raw = str(raw).strip()
    if len(raw) > 1 and raw.startswith("0") and not raw.startswith("0."):
        return False
    try:
        val = float(raw)
    except Exception:
        return False
    if 1900 <= val <= 2100:
        return False
    if exam == "IELTS":
        return 0 <= val <= 9 and abs(val * 2 - round(val * 2)) < 1e-9
    if exam == "TOEFL":
        return val.is_integer() and 0 <= val <= 120
    if exam == "SAT":
        return val.is_integer() and 200 <= val <= 1600 and int(val) % 10 == 0
    if exam == "ACT":
        return val.is_integer() and 1 <= val <= 36
    if exam == "PTE":
        return val.is_integer() and 10 <= val <= 90
    if exam == "Duolingo":
        return val.is_integer() and 10 <= val <= 160 and int(val) % 5 == 0
    if exam == "Cambridge":
        return val.is_integer() and 80 <= val <= 230
    if exam in {"YDS", "YÖKDİL"}:
        return val.is_integer() and 0 <= val <= 100
    if exam == "IB":
        return val.is_integer() and 0 <= val <= 45
    return False

def extract_exam_score_records(pages):
    aliases = {
        "IELTS":["ielts"], "TOEFL":["toefl", "toefl ibt"], "SAT":["sat"],
        "ACT":["act"], "PTE":["pte", "pearson test of english"],
        "Duolingo":["duolingo", "det"], "Cambridge":["cambridge", "cae", "cpe"],
        "YDS":["yds"], "YÖKDİL":["yökdil", "yokdil"], "IB":["international baccalaureate", "ib diploma", "ib"],
    }
    score_words = (
        "score", "minimum", "required", "requirement", "at least", "overall", "total",
        "math", "composite", "band", "points", "not less than", "admission", "eligible",
        "threshold", "must have", "accepted with", "minimum score",
    )
    records, seen = [], set()
    for page in pages or []:
        raw_text = page.get("text", "") or ""
        # URLs and long identifiers are a common source of false scores.
        raw_text = re.sub(r"https?://\S+", " ", raw_text)
        raw_text = re.sub(r"\b(?:id|article|document|news)[=/:-]?\d{3,}\b", " ", raw_text, flags=re.I)
        text = re.sub(r"\s+", " ", raw_text)
        low_text = text.lower()
        for exam, names in aliases.items():
            for alias in names:
                for match in re.finditer(rf"(?<![A-Za-z]){re.escape(alias)}(?![A-Za-z])", low_text, flags=re.I):
                    a = max(0, match.start() - 100)
                    b = min(len(text), match.end() + 180)
                    context = text[a:b].strip(" -–—:;,.|")
                    low = context.lower()
                    direct_pattern = re.search(rf"{re.escape(alias)}\s*(?:score|total|math|overall|band)?\s*[:=\-]?\s*\d", low, flags=re.I)
                    if not direct_pattern and not any(word in low for word in score_words):
                        continue
                    nums = []
                    for num_match in re.finditer(r"(?<!\d)(\d{1,4}(?:\.\d+)?)(?!\d)", context):
                        candidate = num_match.group(1)
                        if _valid_exam_score(exam, candidate):
                            # Prefer numbers near the exam name or a score keyword.
                            dist = abs((a + num_match.start()) - match.start())
                            local = context[max(0, num_match.start()-45):num_match.end()+45].lower()
                            if dist <= 150 and (any(w in local for w in score_words) or direct_pattern):
                                if candidate not in nums:
                                    nums.append(candidate)
                    if not nums:
                        continue
                    requirement_language = any(k in low for k in [
                        "minimum", "required", "requirement", "at least", "must have",
                        "overall score", "minimum score", "not less than", "threshold",
                    ])
                    key = (exam, tuple(nums[:4]), page.get("url"))
                    if key in seen:
                        continue
                    seen.add(key)
                    records.append({
                        "exam": exam,
                        "scores": nums[:4],
                        "sentence": context[:420],
                        "url": page.get("url"),
                        "title": page.get("title"),
                        "status": "requirement" if requirement_language else "published_score",
                    })
    return records[:20]


def _clean_email(value):
    value = (value or "").strip().strip(".,;:()[]{}<>")
    if not re.match(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", value, flags=re.I):
        return None
    low = value.lower()
    if any(x in low for x in ["example.com", "sentry.io", "wixpress.com", "cloudflare.com"]):
        return None
    return value

def _clean_phone(value):
    value = re.sub(r"\s+", " ", (value or "").strip())
    digits = re.sub(r"\D", "", value)
    if not (7 <= len(digits) <= 15):
        return None
    # Avoid obvious dates / IDs.
    if len(set(digits)) <= 2:
        return None
    return value.strip(" .,:;")

def _contact_priority(text):
    low = (text or "").lower()
    score = 0
    for k, w in {
        "admission":8, "admissions":8, "international":6, "undergraduate":5,
        "student":3, "apply":3, "enrol":3, "enroll":3, "office":2,
        "contact":2, "registrar":2,
    }.items():
        if k in low:
            score += w
    return score

def extract_official_contacts(pages, official_site=""):
    """Extract public organizational contact details only from official-domain pages."""
    official_host = _host(official_site)
    email_candidates = []
    phone_candidates = []
    contact_pages = []

    for page in pages or []:
        url = page.get("url") or ""
        if official_site and not _same_official_domain(url, official_site):
            continue
        title = page.get("title") or ""
        text = page.get("text") or ""
        context_score = _contact_priority(title + " " + url + " " + text[:2500])

        if any(k in (title + " " + url).lower() for k in [
            "contact", "admission", "international", "apply", "enrol", "enroll"
        ]):
            contact_pages.append({"title": title or url, "url": url, "score": context_score})

        # Emails.
        for raw in re.findall(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", text, flags=re.I):
            email = _clean_email(raw)
            if not email:
                continue
            domain_score = 0
            if official_host:
                email_domain = email.split("@")[-1].lower()
                if email_domain == official_host or official_host.endswith("." + email_domain) or email_domain.endswith("." + official_host):
                    domain_score = 8
            local = email.split("@")[0].lower()
            role_score = sum(w for k, w in {
                "admission":10, "apply":6, "international":7, "student":3,
                "info":2, "registrar":3, "enrol":4, "enroll":4,
            }.items() if k in local)
            email_candidates.append({
                "value": email, "url": url, "title": title,
                "score": context_score + domain_score + role_score,
            })

        # International phone-like strings. We require +, parentheses, or separators
        # to reduce accidental extraction of dates and scores.
        for raw in re.findall(r"(?:\+\d{1,3}[\s().\-]*)?(?:\(?\d{2,4}\)?[\s.\-]*){2,5}\d{2,4}", text):
            if not any(ch in raw for ch in ["+", "(", ")", "-", " "]):
                continue
            phone = _clean_phone(raw)
            if phone:
                phone_candidates.append({
                    "value": phone, "url": url, "title": title,
                    "score": context_score,
                })

    def dedupe_rank(items, limit):
        best = {}
        for item in items:
            key = item["value"].lower()
            if key not in best or item["score"] > best[key]["score"]:
                best[key] = item
        return sorted(best.values(), key=lambda x: x["score"], reverse=True)[:limit]

    # Deduplicate contact-page URLs.
    page_best = {}
    for p in contact_pages:
        if p["url"] not in page_best or p["score"] > page_best[p["url"]]["score"]:
            page_best[p["url"]] = p

    return {
        "emails": dedupe_rank(email_candidates, 5),
        "phones": dedupe_rank(phone_candidates, 5),
        "contact_pages": sorted(page_best.values(), key=lambda x: x["score"], reverse=True)[:5],
    }

@st.cache_data(ttl=3600, show_spinner=False)
def discover_contacts_via_search(official_site, university="", country=""):
    """Fallback contact discovery when content pages cannot be read directly."""
    if not official_site or not is_safe_public_url(official_site):
        return {"emails": [], "phones": [], "contact_pages": []}
    host = _host(official_site)
    pages = []
    for q in [
        f"site:{host} admissions contact email phone",
        f"site:{host} international admissions contact",
        f"site:{host} undergraduate admissions contact us",
    ]:
        for r in jina_search(q):
            url = r.get("url")
            if not url or not _same_official_domain(url, official_site):
                continue
            pages.append({
                "title": r.get("title") or url,
                "url": url,
                "text": r.get("content") or "",
            })
    return extract_official_contacts(pages, official_site)

def merge_contact_sets(primary, secondary):
    primary = primary or {"emails": [], "phones": [], "contact_pages": []}
    secondary = secondary or {"emails": [], "phones": [], "contact_pages": []}
    merged = {}
    for key in ["emails", "phones", "contact_pages"]:
        items = []
        seen = set()
        for item in (primary.get(key, []) + secondary.get(key, [])):
            identity = item.get("value") if key != "contact_pages" else item.get("url")
            if not identity:
                continue
            norm = str(identity).lower()
            if norm in seen:
                continue
            seen.add(norm)
            items.append(item)
        merged[key] = items[:5]
    return merged

def admissions_question_templates(plan, missing_topic="admission requirements"):
    university = (plan.get("university") or "your university").strip()
    program = (plan.get("program") or "the programme").strip()
    year = plan.get("year") or ""
    topic = missing_topic or "admission requirements"
    english = (
        f"Hello, I am planning to apply to {program} at {university} for {year}. "
        f"Could you please confirm the current {topic} for an international undergraduate applicant, "
        f"including any required exams, minimum scores, documents and deadlines? Thank you."
    )
    return {
        "english": english,
        "localized": lx(english),
    }

def build_official_research(pages):
    categories = {
        "Course & entry requirements": [],
        "Exams & language scores": [],
        "Deadlines": [],
        "Application documents / essays": [],
        "Scholarships / financial aid": [],
    }
    seen = {k:set() for k in categories}
    for page in pages:
        mentions = extract_admission_mentions(page.get("text", ""))
        mapping = {
            "Academic requirements":"Course & entry requirements",
            "Exams / scores":"Exams & language scores",
            "Deadlines":"Deadlines",
            "Application writing":"Application documents / essays",
            "Scholarships / aid":"Scholarships / financial aid",
        }
        for src_label, vals in mentions.items():
            dst = mapping.get(src_label)
            if not dst:
                continue
            for val in vals:
                norm = re.sub(r"\s+", " ", val).strip()
                if not norm or norm in seen[dst]:
                    continue
                seen[dst].add(norm)
                categories[dst].append({
                    "text": norm[:900], "url": page.get("url"), "title": page.get("title")
                })
    return categories

# -------------------- Pages --------------------
page = st.session_state.page

if page == "Home":
    st.markdown(f"""
    <div class="hero">
      <div class="eyebrow">{t('home_eyebrow')}</div>
      <h1>{t('home_title')}</h1>
      <p>{t('home_sub')}</p>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='feature-card'><div class='label'>{t('learn')}</div><h3>{t('tutor_hub')}</h3><p class='muted'>{t('learn_desc')}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='feature-card'><div class='label'>{t('navigate')}</div><h3>{t('personal_pathway')}</h3><p class='muted'>{t('navigate_desc')}</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='feature-card'><div class='label'>{t('connect_safely')}</div><h3>{t('support_community')}</h3><p class='muted'>{t('connect_desc')}</p></div>", unsafe_allow_html=True)
    st.write("")
    b1,b2,b3 = st.columns(3)
    with b1:
        btn_nav(t("continue_path") if profile() else t("build_profile"), "My Pathway" if profile() else "Profile", "home_main", primary=True)
    with b2:
        btn_nav(t("explore_learning"), "Learning Hub", "home_learn")
    with b3:
        btn_nav(t("plan_university"), "University Planner", "home_uni")
    st.markdown("### " + t("one_platform"))
    st.write(t("one_platform_desc"))

elif page == "Profile":
    st.title(t("profile_title"))
    st.caption(t("profile_hint"))
    old = profile()
    with st.form("profile_form"):
        c1,c2 = st.columns(2)
        with c1:
            age = st.slider(t("age"), 12, 19, int(old.get("age",15)))
            country_default = old.get("country","Global / not specified")
            country = st.selectbox(t("country_region"), COUNTRIES, index=COUNTRIES.index(country_default) if country_default in COUNTRIES else 0, format_func=country_display)
            lang_default = old.get("language","English")
            language = st.selectbox(t("preferred_language"), LANGUAGES, index=LANGUAGES.index(lang_default) if lang_default in LANGUAGES else 0, format_func=language_display)
            other_languages = st.multiselect(t("other_languages"), LANGUAGES, default=old.get("other_languages",[]), format_func=language_display)
        with c2:
            goals = st.multiselect(t("goals"), GOALS, default=old.get("goals",["Understand mathematics"]), format_func=lx)
            barriers = st.multiselect(t("barriers"), BARRIERS, default=old.get("barriers",["Lack of guidance"]), format_func=lx)
            support = st.selectbox(t("preferred_support"), SUPPORT_PREFS, index=SUPPORT_PREFS.index(old.get("support","A mix of both")) if old.get("support","A mix of both") in SUPPORT_PREFS else 2, format_func=lx)
            access = st.multiselect(t("access_needs"), ACCESS_NEEDS, default=old.get("access",["Free only","Works on a phone"]), format_func=lx)
        current_need = st.text_input(t("current_need"), value=old.get("current_need",""), placeholder=(ui("Example: I do not understand graphs and I also need a university preparation plan.", "Например: я не понимаю графики и мне нужен план поступления в университет.")))
        submitted = st.form_submit_button(t("save_profile"), type="primary", use_container_width=True)
    if submitted:
        st.session_state.profile = {
            "age":age, "country":country, "language":language, "other_languages":other_languages,
            "goals":goals or ["Improve school grades"], "barriers":barriers or ["Lack of guidance"],
            "support":support, "access":access, "current_need":current_need,
        }
        sync_persistence()
        st.success(t("profile_saved"))
    if profile() and st.button(t("open_pathway"), type="primary"):
        nav_to("My Pathway")

elif page == "My Pathway":
    st.title(t("my_pathway"))
    p = profile()
    if not p:
        st.info(t("create_profile_first"))
        btn_nav(t("create_profile"), "Profile", "path_create", primary=True)
    else:
        st.markdown(f"<div class='notice'><b>{t('today')}:</b> {t('focus_next')} <b>{lx(main_goal())}</b>.</div>", unsafe_allow_html=True)
        m1,m2,m3,m4 = st.columns(4)
        m1.metric(t("completed_modules"), len(st.session_state.completed_modules))
        m2.metric(t("saved_opportunities"), len(st.session_state.saved_opportunities))
        m3.metric(t("support_requests"), st.session_state.support_request_count)
        m4.metric(t("saved_actions"), len(st.session_state.saved_actions))
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
        st.subheader(t("todays_path"))
        for i,(target,desc) in enumerate(steps[:6], start=1):
            display_target = t(PAGE_LABEL_KEY.get(target, PAGE_LABEL_KEY.get("Home", "nav_home"))) if target in PAGE_LABEL_KEY else lx(target)
            display_desc = lx(desc)
            if interface_lang()=="ru":
                desc_map = {
                    "Do one focused tutoring session and ask at least one follow-up question.":"Проведите одно короткое занятие с AI-репетитором и задайте хотя бы один дополнительный вопрос.",
                    "Complete a short math lesson. Extra practice appears automatically after mistakes.":"Пройдите короткий урок по математике. После ошибок система автоматически добавит практику.",
                    "Complete one short lesson aligned to your current goal.":"Пройдите один короткий урок, связанный с вашей текущей целью.",
                    "Create a structured request for an academic mentor or support route.":"Создайте структурированный запрос на помощь наставника или другой безопасный маршрут поддержки.",
                    "Build a target-university research board and portfolio evidence list.":"Соберите проверенный план по целевому университету и список доказательств для портфолио.",
                    "Review personalized opportunity cards and save one realistic next option.":"Просмотрите персональные возможности и сохраните один реалистичный следующий вариант.",
                }
                display_desc = desc_map.get(desc, display_desc)
                if target == "Motivation":
                    display_desc = f"Прочитайте историю, связанную с трудностью «{lx(p['barriers'][0])}», и сохраните одно конкретное действие."
            st.markdown(f"<div class='path-step'><b>{i}. {display_target}</b><br><span class='muted'>{display_desc}</span></div>", unsafe_allow_html=True)
            if st.button(t("go_to", target=display_target), key=f"path_{i}_{target}"):
                nav_to(target)
        if st.session_state.saved_actions:
            st.subheader(t("actions_saved"))
            for a in st.session_state.saved_actions[-5:]:
                st.write("•", a)

elif page == "AI Tutor":
    st.title(t("tutor_title"))
    st.write(t("tutor_desc") + (ui(" The portfolio prototype uses structured logic rather than a live generative model.", " Прототип использует структурированную логику, а не живую генеративную модель.")))
    with st.expander(t("technical_note")):
        st.write(ui("A production version would add a safeguarded LLM/RAG layer, source grounding, age-appropriateness checks and answer-quality evaluation.", "В рабочей версии можно добавить защищённый LLM/RAG-слой, привязку к источникам, проверку соответствия возрасту и оценку качества ответов."))
    c1,c2 = st.columns(2)
    with c1:
        subject = st.selectbox(t("subject"), list(SUBJECT_TOPICS.keys()), key="tutor_subject", format_func=lx)
        topic_options = SUBJECT_TOPICS[subject]
        topic = st.selectbox(t("topic"), topic_options, key=f"topic_{subject}", format_func=lx)
        if topic == "Other":
            topic = st.text_input(t("write_topic"), key="custom_topic")
        stuck = st.text_area(t("what_unclear"), placeholder=(ui("Example: I don't understand why 2x + 3 = 11 means x = 4.", "Например: я не понимаю, почему из 2x + 3 = 11 получается x = 4.")))
        tried = st.text_area(t("what_tried"), placeholder=(ui("Example: I tried subtracting 3 but I do not understand why we do it on both sides.", "Например: я пробовал(а) вычесть 3, но не понимаю, почему это нужно делать с обеими частями.")))
    with c2:
        help_style = st.selectbox(t("how_help"), ["Explain it simply","Guide me with hints","Show an example"], format_func=lx)
        confidence = st.slider(t("confidence"), 1, 5, 2)
        st.caption(ui("The prototype uses this to choose a gentler or more direct starting point."))
    b1,b2 = st.columns([2,1])
    if b1.button(t("start_session"), type="primary", use_container_width=True):
        if not (topic or "").strip():
            st.warning(ui("Choose or write a topic first."))
        elif not stuck.strip():
            st.warning(ui("Write the exact point that is unclear so the explanation can start there."))
        else:
            base, focus = tutor_payload(subject, topic, stuck, help_style)
            st.session_state.tutor_session = {
                "subject":subject, "topic":topic, "stuck":stuck, "tried":tried,
                "help_style":help_style, "confidence":confidence, "base":base,
                "history":[{"role":"assistant","text":focus}],
            }
            st.rerun()
    if b2.button(t("clear_session"), use_container_width=True):
        st.session_state.tutor_session = None
        st.rerun()

    s = st.session_state.tutor_session
    if s:
        base = s["base"]
        st.markdown("### " + t("locate_stuck"))
        st.markdown(f"<div class='card'><b>{t('topic')}:</b> {lx(s['subject'])} → {lx(s['topic'])}<br><br>{base['diagnosis']}</div>", unsafe_allow_html=True)
        st.markdown("### " + t("explanation_follow"))
        for msg in s.get("history",[]):
            if msg["role"] == "user":
                st.chat_message("user").write(msg["text"])
            else:
                st.chat_message("assistant").write(msg["text"])
        x1,x2,x3 = st.columns(3)
        if x1.button(t("explain_simpler"), key="tutor_simpler"):
            s["history"].append({"role":"assistant","text":base.get("simple", "Let's make the first step smaller.")})
            st.rerun()
        if x2.button(t("give_hint"), key="tutor_hint"):
            s["history"].append({"role":"assistant","text":base.get("hint", "What is the first operation you can undo?")})
            st.rerun()
        if x3.button(t("show_example"), key="tutor_example"):
            s["history"].append({"role":"assistant","text":base.get("example", "Try a smaller example with the same rule.")})
            st.rerun()
        with st.form("tutor_followup_form", clear_on_submit=True):
            follow = st.text_input(t("ask_same"), placeholder=(ui("Example: Why do we subtract 3 from both sides?", "Например: почему мы вычитаем 3 из обеих частей?")))
            ask_follow = st.form_submit_button(t("ask_follow"))
        if ask_follow and follow.strip():
            s["history"].append({"role":"user","text":follow.strip()})
            reply = tutor_followup_response(s["subject"], s["topic"], follow, base)
            s["history"].append({"role":"assistant","text":reply})
            st.rerun()

        st.markdown("### " + t("check_understanding"))
        st.write(base["check"])
        ans = st.text_input(t("your_answer"), key="tutor_check_answer")
        if st.button(t("check_answer"), key="tutor_check"):
            if base["answer"] is None:
                st.info(base["answer_explanation"])
            elif normalize_answer(ans) == normalize_answer(base["answer"]):
                st.success(ui("Correct.", "Верно."))
                st.info(ui("Why: ") + base["answer_explanation"])
            else:
                st.error(ui("Not yet. Read the explanation, then try again or ask a follow-up question above."))
                st.info(ui("Explanation: ") + base["answer_explanation"])
        st.caption(ui("You can continue asking follow-up questions without restarting the session."))

elif page == "Learning Hub":
    st.title(t("learning_title"))
    st.write(t("learning_desc"))
    subjects = ["All"] + sorted({m["subject"] for m in MODULES.values()})
    filt = st.selectbox(t("filter_subject"), subjects, format_func=lx)
    available = [name for name,m in MODULES.items() if filt == "All" or m["subject"] == filt]
    title = st.selectbox(t("choose_lesson"), available, format_func=lx)
    module = MODULES[title]
    lp = get_lesson_state(title)
    bank = full_question_bank(module)
    st.markdown(f"<div class='card'><b>{lx(title)}</b> · {module['minutes']} {ui('min', 'мин')}<br><span class='muted'>{lx(module['intro'])}</span></div>", unsafe_allow_html=True)

    if lp.get("completed"):
        total_seen = max(1, len(lp.get("queue", [])))
        mistakes = int(lp.get("incorrect_attempts", 0))
        st.success(ui(f"Lesson completed. You worked through {total_seen} question(s).", f"Урок завершён. Вы прошли {total_seen} вопрос(а/ов)."))
        if mistakes:
            st.info(ui(f"Adaptive practice added {lp.get('adaptive_added', 0)} extra question(s) after {mistakes} incorrect attempt(s).", f"Адаптивная практика добавила {lp.get('adaptive_added', 0)} дополнительных вопрос(а/ов) после {mistakes} ошибочных попыток."))
        if st.button(t("restart_lesson")):
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
        st.caption(ui(f"Question {pos+1} of {len(lp['queue'])} · mistakes so far: {lp['incorrect_attempts']}", f"Вопрос {pos+1} из {len(lp['queue'])} · ошибок пока: {lp['incorrect_attempts']}"))
        st.markdown(f"## {lx(q['q'])}")
        choice = st.radio(t("choose_answer"), q["options"], key=f"lesson_{title}_{q_index}_{pos}", index=None, format_func=lx)
        if st.button(t("check_answer"), type="primary", key=f"check_{title}_{q_index}_{pos}"):
            if choice is None:
                st.warning(ui("Choose an answer first.", "Сначала выберите ответ."))
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
            st.error(ui("Not yet — use the explanation, then try the same question again.", "Пока нет — прочитайте объяснение и попробуйте тот же вопрос ещё раз."))
            st.info((ui("Explanation: ", "Объяснение: ")) + lx(q["explanation"]))
            if lp["incorrect_attempts"] >= 2:
                st.caption(ui("The lesson will add extra practice before completion because this topic needs more repetition.", "Перед завершением урок добавит дополнительную практику, потому что этой теме нужно больше повторения."))
        elif result == "correct":
            st.success(ui("Correct.", "Верно."))
            st.info((ui("Why: ", "Почему: ")) + lx(q["explanation"]))
            if st.button(t("next_question"), key=f"next_{title}_{q_index}_{pos}"):
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
            st.caption(ui(f"Adaptive practice active: {lp['adaptive_added']} extra question(s) have been added based on mistakes.", f"Адаптивная практика: добавлено {lp['adaptive_added']} дополнительных вопрос(а/ов) на основе ошибок."))

elif page == "Motivation":
    st.title(t("motivation_title"))
    st.write(t("motivation_desc"))
    p = profile()
    barrier_options = BARRIERS
    default_barrier = p.get("barriers",["Lack of guidance"])[0] if p.get("barriers") else "Lack of guidance"
    barrier = st.selectbox(t("barrier_story"), barrier_options, index=barrier_options.index(default_barrier) if default_barrier in barrier_options else 0, format_func=lx)
    matched = [s for s in STORIES if barrier in s["barriers"]] or STORIES
    story_names = [s["person"] for s in matched]
    selected_name = st.selectbox(t("choose_story"), story_names)
    s = next(x for x in matched if x["person"] == selected_name)
    _sr = RU_STORIES.get(s["person"], {}) if interface_lang()=="ru" else {}
    if interface_lang()=="ru":
        _title = _sr.get("title", s["title"]); _starting = _sr.get("starting", s["starting"]); _turning = _sr.get("turning", s["turning"]); _lesson = _sr.get("lesson", s["lesson"]); _action = _sr.get("action", s["action"])
    else:
        _title = lx(s["title"]); _starting = lx(s["starting"]); _turning = lx(s["turning"]); _lesson = lx(s["lesson"]); _action = lx(s["action"])
    st.markdown(
        f"<div class='story'><h2>{s['person']} — {_title}</h2>"
        f"<p><b>{ui('Starting point.', 'Отправная точка.')}</b> {_starting}</p>"
        f"<p><b>{ui('Turning point.', 'Поворотный момент.')}</b> {_turning}</p>"
        f"<p><b>{ui('What this shows.', 'Что это показывает.')}</b> {_lesson}</p>"
        f"<p><b>{ui('Do one thing now.', 'Сделайте одно действие сейчас.')}</b> {_action}</p></div>",
        unsafe_allow_html=True
    )
    st.link_button(t("open_source"), s["source_url"])
    action = st.text_area(t("own_action"), value=_action)
    if st.button(t("save_action"), type="primary"):
        if action.strip() and action.strip() not in st.session_state.saved_actions:
            st.session_state.saved_actions.append(action.strip())
            sync_persistence()
        st.success(t("saved_path"))

elif page == "Human Support":
    st.title(t("support_title"))
    st.write(t("support_desc"))
    p = profile()
    with st.form("support_form"):
        kind = st.selectbox(t("support_kind"), ["Academic mentor","Tutor","University application mentor","School support / safeguarding route"], format_func=lx)
        lang = st.selectbox(t("support_language"), LANGUAGES, index=LANGUAGES.index(p.get("language","English")) if p.get("language","English") in LANGUAGES else 0, format_func=language_display)
        detail = st.text_area(t("support_detail"), placeholder=(ui("Example: I need help understanding graphs and planning weekly practice.", "Например: мне нужна помощь с графиками и планом занятий на неделю.")))
        consent = st.checkbox(t("support_consent"))
        submit = st.form_submit_button(t("create_support"), type="primary")
    if submit:
        if not consent:
            st.error(ui("Confirm the safeguarding notice first."))
        elif not detail.strip():
            st.error(ui("Add a short description of the support you need."))
        else:
            req_id = f"SUP-{random.randint(10000,99999)}"
            st.session_state.support_requests.append({"id":req_id,"kind":kind,"language":lang,"detail":detail,"created":datetime.utcnow().isoformat()})
            st.session_state.support_request_count += 1
            sync_persistence()
            st.success(ui(f"Request {req_id} created in the prototype.", f"Запрос {req_id} создан в прототипе."))
    if st.session_state.support_requests:
        st.subheader(ui("Requests created in this session", "Запросы, созданные в этой сессии"))
        for r in reversed(st.session_state.support_requests[-5:]):
            st.write(f"• {r['id']} · {lx(r['kind'])} · {language_display(r['language'])} · {ui('status: demo request created', 'статус: демо-запрос создан')}")
    st.caption(ui(f"Persistent request counter: {st.session_state.support_request_count}", f"Сохранённый счётчик запросов: {st.session_state.support_request_count}"))

elif page == "Community":
    st.title(t("community_title"))
    st.write(t("community_desc"))
    topics = ["All","Math","English","Coding","Study skills","Applications","Motivation"]
    room = st.selectbox(t("topic_room"), topics, format_func=lx)
    shown = [p for p in COMMUNITY_POSTS if room == "All" or p[1] == room]
    for name,topic,text in shown:
        _post_text = RU_COMMUNITY_POSTS.get(text, text) if interface_lang()=="ru" else lx(text)
        _verified = ui("Verified peer tip in prototype dataset", "Проверенный совет из демонстрационного набора")
        st.markdown(f"<div class='card'><b>{name}</b> · <span class='muted'>{lx(topic)}</span><p>{_post_text}</p><span class='tiny'>{_verified}</span></div>", unsafe_allow_html=True)
        st.write("")
    st.subheader(t("ask_community"))
    with st.form("community_form"):
        topic = st.selectbox(t("topic"), topics[1:], format_func=lx)
        question = st.text_area(t("your_question"), placeholder=(ui("Do not include your real name, phone number, email, address, school name or social-media handle.", "Не указывайте настоящее имя, телефон, email, адрес, название школы или аккаунт в соцсетях.")))
        send = st.form_submit_button(t("send_moderation"))
    if send:
        findings = pii_findings(question)
        if findings:
            st.error(ui("Not submitted. Remove personal contact information before sending: ") + ", ".join(findings) + ".")
        elif len(question.strip()) < 8:
            st.error(ui("Write a little more so moderators can understand the question."))
        else:
            st.session_state.community_submissions.append({"topic":topic,"question":question.strip(),"status":"pending moderation"})
            st.success(ui("Submitted for moderation. It is not published automatically."))
    if st.session_state.community_submissions:
        st.caption(ui(f"Pending moderation in this session: {len(st.session_state.community_submissions)}", f"Ожидают модерации в этой сессии: {len(st.session_state.community_submissions)}"))

elif page == "Opportunities":
    st.title(t("opportunities_title"))
    st.write(ui("This section separates actions you can do inside Opportunity Navigator from real external providers. External links are optional and secondary, but they open directly when you choose to verify or apply.", "Этот раздел отделяет действия внутри Opportunity Navigator от реальных внешних программ. Внешние ссылки используются только для проверки информации или подачи заявки."))
    st.subheader(t("next_actions"))
    st.markdown(f"<div class='path-step'><b>{ui('Build an application evidence portfolio', 'Соберите доказательства для портфолио')}</b><br><span class='muted'>{ui('Organize projects, research, volunteering and measurable results.', 'Систематизируйте проекты, исследования, волонтёрство и измеримые результаты.')}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='path-step'><b>{ui('Build an opportunity shortlist', 'Составьте короткий список возможностей')}</b><br><span class='muted'>{ui('Save realistic options, compare eligibility and choose one application task for this week.', 'Сохраните реалистичные варианты, сравните требования и выберите одно действие на эту неделю.')}</span></div>", unsafe_allow_html=True)
    if st.button(ui("Open University Planner")):
        nav_to("University Planner")
    st.subheader(t("opportunities_for_you"))
    st.caption(ui("Provider records are examples for the prototype. Always verify the current cycle, deadline and local eligibility on the official page."))
    cats = ["All"] + sorted({o["category"] for o in PROVIDER_OPPORTUNITIES})
    cat = st.selectbox(t("category"), cats, format_func=lx)
    p = profile()
    ranked = []
    for o in PROVIDER_OPPORTUNITIES:
        if cat != "All" and o["category"] != cat:
            continue
        sc,reasons = score_opportunity(o,p)
        ranked.append((sc,reasons,o))
    ranked.sort(key=lambda x:x[0], reverse=True)
    for sc,reasons,o in ranked:
        o = localized_opportunity(o)
        age_label = ui(f"Ages {o['age_min']}–{o['age_max']}", f"Возраст {o['age_min']}–{o['age_max']}")
        pills = "".join([f"<span class='pill'>{x}</span>" for x in [o['category'],o['cost'],age_label]])
        st.markdown(f"### {o['name']}", unsafe_allow_html=True)
        st.markdown(pills, unsafe_allow_html=True)
        st.write(o["summary"])
        if interface_lang()=="ru":
            reason_map = {"fits your age":"подходит по возрасту", "available globally / in your region":"доступно глобально / в вашем регионе", "matches your goal":"соответствует вашей цели", "free":"бесплатно", "language match":"подходит по языку"}
            reason_text = ", ".join(reason_map.get(r,r) for r in reasons) if reasons else "нужно дополнительно сравнить с вашим профилем"
            st.write("**Почему подходит:** " + reason_text)
            st.write("**Кому подходит:** " + o["eligibility"])
        else:
            reason_text = ", ".join(lx(r) for r in reasons) if reasons else ui("review manually against your profile", "сравните с вашим профилем")
            st.write("**" + ui("Why this matches", "Почему подходит") + ":** " + reason_text)
            st.write("**" + ui("Eligibility", "Кому подходит") + ":** " + lx(o["eligibility"]))
        with st.expander(ui("Inside-platform preparation checklist", "Чек-лист подготовки внутри платформы")):
            for item in o["checklist"]:
                st.checkbox(item, key=f"check_{o['id']}_{item}")
        c1,c2 = st.columns(2)
        saved = o["id"] in st.session_state.saved_opportunities
        if c1.button(t("saved") if saved else t("save_opportunity"), key=f"save_{o['id']}", disabled=saved, use_container_width=True):
            st.session_state.saved_opportunities.add(o["id"]); sync_persistence(); st.rerun()
        with c2:
            st.link_button(t("official_provider"), o["url"], use_container_width=True)
        st.divider()

elif page == "University Planner":
    st.title(t("university_title"))
    st.write(t("university_desc"))
    old = st.session_state.admissions_plan or {}
    with st.form("admissions_target"):
        c1,c2 = st.columns(2)
        with c1:
            target_country = st.selectbox(
                t("target_country"), COUNTRIES,
                index=COUNTRIES.index(old.get("country","Global / not specified")) if old.get("country","Global / not specified") in COUNTRIES else 0,
                format_func=country_display
            )
            university = st.text_input(
                t("target_university"), value=old.get("university",""),
                placeholder=(ui("Example: MBZUAI or Istanbul Aydin University", "Например: MBZUAI или Университет Айдын"))
            )
            program = st.text_input(
                t("course_program"), value=old.get("program",""),
                placeholder=(ui("Example: Industrial Engineering", "Например: Промышленная инженерия"))
            )
        with c2:
            levels = ["Bachelor's / undergraduate","Foundation / pathway","Other"]
            old_level = old.get("level", levels[0])
            level = st.selectbox(t("study_level"), levels, index=levels.index(old_level) if old_level in levels else 0, format_func=lx)
            year = st.number_input(
                t("entry_year"), min_value=datetime.utcnow().year,
                max_value=datetime.utcnow().year+8,
                value=int(old.get("year", datetime.utcnow().year+2))
            )
            scholarship = st.checkbox(t("need_aid"), value=bool(old.get("scholarship",True)))
        official_url = st.text_input(
            t("official_url"),
            value=old.get("official_url",""),
            placeholder=(ui("You can leave this blank for a supported university.", "Для поддерживаемого университета можно оставить пустым."))
        )
        save_plan = st.form_submit_button(t("build_plan"), type="primary")
    if save_plan:
        st.session_state.admissions_plan = {
            "country":target_country,"university":university,"program":program,"level":level,
            "year":int(year),"scholarship":scholarship,"official_url":official_url,
        }
        sync_persistence()
        st.success(t("plan_saved"))

    plan = st.session_state.admissions_plan
    if plan:
        curated = curated_admissions_profile(plan)

        # -------------------- Structured verified profile --------------------
        if curated:
            curated = localized_curated(curated)
            profile_key = curated.get("_key", "curated")
            st.success(ui(
                f"Verified structured profile found: {curated['university']} — {curated['program']}. Official information checked {curated['verified_date']}.",
                f"Найдена проверенная структурированная карточка: {curated['university']} — {curated['program']}. Информация проверена {curated['verified_date']}."
            ))

            st.subheader(ui("1. Course & entry requirements", "1. Требования к программе и поступлению"))
            st.caption(ui("Requirements are shown inside the platform; official pages remain linked as evidence and for future re-checking.", "Платформа показывает требования внутри приложения; официальные страницы остаются источниками для проверки."))
            for row in curated["academic"]:
                st.markdown(
                    f"<div class='card'><b>{row['label']}</b> {status_badge(row['status'])}<br><span class='muted'>{row['value']}</span></div>",
                    unsafe_allow_html=True,
                )
                st.write("")

            st.subheader(ui("2. Exams & published scores", "2. Экзамены и опубликованные баллы"))
            st.write(ui("If a current official source does not publish an exact minimum, the planner says so instead of inventing a number.", "Если актуальный официальный источник не публикует точный минимальный балл, платформа так и пишет — она не придумывает число."))
            for row in curated["tests"]:
                source_url = curated["sources"].get(row["source"], next(iter(curated["sources"].values())))
                requirement_label = ui("Requirement", "Статус")
                score_label = ui("Published score", "Опубликованный балл")
                st.markdown(
                    f"<div class='card'><b>{row['name']}</b><br><b>{requirement_label}:</b> {row['required']}<br><b>{score_label}:</b> {row['score']}<br><span class='muted'>{row['note']}</span></div>",
                    unsafe_allow_html=True,
                )
                st.link_button(ui("Official source ↗", "Официальный источник ↗"), source_url, key=f"curated_test_{profile_key}_{row['name']}")
                st.write("")

            if curated.get("screening_topics"):
                exam_title = ui("What is on the screening exam?", "Что входит в screening exam?")
                with st.expander(exam_title, expanded=True):
                    for group, topics in curated["screening_topics"].items():
                        st.markdown(f"**{lx(group)}:** " + ", ".join(lx(x) for x in topics))

            st.subheader(ui("3. Key dates", "3. Ключевые даты"))
            for label, value in curated["dates"]:
                st.write(f"**{label}:** {value}")

            st.subheader(ui("4. Application documents & selection steps", "4. Документы и этапы отбора"))
            for label, value in curated["documents"]:
                st.write(f"**{label}:** {value}")

            st.subheader(ui("5. Fees & financial aid", "5. Стоимость и финансовая помощь"))
            for label, value in curated["fees_aid"]:
                st.write(f"**{lx(label)}:** {lx(value)}")

            st.subheader(ui("6. Preparation areas / courses", "6. Что стоит укрепить до поступления"))
            if profile_key == "iau_industrial_engineering_2027":
                st.caption(ui("These preparation areas are based on the published curriculum and official materials; they are not presented as separate admission prerequisites.", "Эти направления подготовки основаны на опубликованной структуре программы и официальных материалах, но не выдаются за отдельные admission prerequisites."))
            elif profile_key == "mbzuai_bsc_ai_business_2027":
                st.caption(ui("These courses/areas align with preparation recommended on MBZUAI's current undergraduate pages.", "Эти курсы/направления соответствуют подготовке, рекомендованной на текущих страницах MBZUAI."))
            for course in curated["recommended_courses"]:
                st.write("•", lx(course))

            st.subheader(ui("7. Your gap analysis", "7. Анализ пробелов"))
            st.write(ui("Add what you already have. The planner compares it with published requirements and turns missing items into next actions.", "Введите то, что у вас уже есть. Платформа сравнит это с опубликованными требованиями и покажет следующие шаги."))

            if profile_key == "mbzuai_bsc_ai_business_2027":
                with st.form("mbzuai_gap_form"):
                    c1,c2 = st.columns(2)
                    with c1:
                        school_avg = st.number_input(ui("Your current / predicted overall school average (%)", "Текущий / прогнозируемый средний школьный балл (%)"), min_value=0.0, max_value=100.0, value=0.0, step=0.5)
                        math_avg = st.number_input(ui("Your current / predicted mathematics result (%)", "Текущий / прогнозируемый результат по математике (%)"), min_value=0.0, max_value=100.0, value=0.0, step=0.5)
                        english_choices = ["Not decided","IELTS Academic","TOEFL iBT","PTE Academic","Cambridge C1 Advanced","Cambridge C2 Proficiency","Duolingo English Test","I believe I qualify for an exemption"]
                        english_exam = st.selectbox(ui("English test you plan to use", "Экзамен по английскому"), english_choices, format_func=lambda x: {"Not decided":"Не выбрано","I believe I qualify for an exemption":"Думаю, у меня есть освобождение"}.get(x,x) if interface_lang()=="ru" else lx(x))
                    with c2:
                        english_score = st.text_input(ui("Your current English-test score", "Ваш текущий балл по английскому экзамену"), placeholder="6.0")
                        sat_math = st.text_input(ui("SAT Math score (optional)", "SAT Math (необязательно)"), placeholder="720")
                        sat_total = st.text_input(ui("SAT total score (optional)", "SAT total (необязательно)"), placeholder="1350")
                    screening_status = st.selectbox(ui("Screening-exam status", "Статус screening exam"), ["Not taken yet","Preparing","Completed","I may qualify for a waiver"], format_func=lambda x: {"Not taken yet":"Ещё не сдавал(а)","Preparing":"Готовлюсь","Completed":"Пройден","I may qualify for a waiver":"Возможно, подхожу под освобождение"}.get(x,x) if interface_lang()=="ru" else lx(x))
                    save_gap = st.form_submit_button(ui("Build my next-step analysis", "Построить анализ следующих шагов"), type="primary")
                if save_gap:
                    gaps, wins = [], []
                    if school_avg > 0:
                        (wins if school_avg >= 90 else gaps).append(("Средний школьный балл достигает опубликованного ориентира 90%." if school_avg >= 90 else "Средний школьный балл ниже опубликованного ориентира 90%; стоит укрепить академические результаты и проверить эквивалентность вашей школьной системы.") if interface_lang()=="ru" else ("Overall school average currently meets the published 90% baseline." if school_avg >= 90 else "Overall school average is below the published 90% baseline; focus on academic improvement and verify curriculum equivalency."))
                    else:
                        gaps.append(ui("Overall school average has not been entered yet.", "Средний школьный балл пока не введён."))
                    if math_avg > 0:
                        if math_avg >= 90:
                            wins.append(ui("Mathematics result is strong relative to MBZUAI's stated competitive profile guidance.", "Результат по математике выглядит сильным относительно опубликованного профиля."))
                        else:
                            gaps.append(ui("Mathematics should be strengthened; MBZUAI emphasizes strong mathematics performance and advanced math in the final two school years.", "Математику стоит укрепить: MBZUAI подчёркивает сильные результаты и продвинутую математику в последних классах."))
                    else:
                        gaps.append(ui("Mathematics result has not been entered yet.", "Результат по математике пока не введён."))
                    if english_exam == "IELTS Academic" and english_score.strip():
                        try:
                            (wins if float(english_score) >= 6.5 else gaps).append(("IELTS достигает опубликованного минимума 6.5." if float(english_score)>=6.5 else "IELTS ниже опубликованного минимума 6.5.") if interface_lang()=="ru" else ("IELTS score meets the published 6.5 minimum." if float(english_score)>=6.5 else "IELTS is below the published 6.5 minimum."))
                        except Exception:
                            gaps.append(ui("IELTS score could not be interpreted; enter a numeric score such as 6.5.", "Введите IELTS числом, например 6.5."))
                    elif english_exam == "Not decided":
                        gaps.append(ui("Choose an English-proficiency route or confirm whether an exemption applies.", "Выберите путь подтверждения английского или проверьте право на освобождение."))
                    elif english_exam != "I believe I qualify for an exemption":
                        gaps.append((f"Сравните текущий результат {english_exam} с опубликованным минимумом выше." if interface_lang()=="ru" else f"Check your current {english_exam} score against the exact published minimum shown above."))
                    if sat_math.strip() and sat_total.strip():
                        try:
                            if int(float(sat_math)) >= 760 and int(float(sat_total)) >= 1400:
                                wins.append(ui("Your entered SAT scores meet the published screening-exam waiver thresholds.", "Введённые SAT достигают опубликованных порогов для waiver screening exam."))
                            else:
                                gaps.append(ui("The entered SAT scores do not meet both published waiver thresholds: Math 760 and total 1400.", "Введённые SAT не достигают обоих порогов waiver: Math 760 и total 1400."))
                        except Exception:
                            gaps.append(ui("SAT scores should be numeric.", "SAT нужно вводить числами."))
                    st.markdown("#### ✅ " + (ui("Already strong", "Уже выглядит сильным")))
                    for item in wins: st.write("•", item)
                    st.markdown("#### 🎯 " + (ui("Next steps", "Следующие шаги")))
                    for item in gaps: st.write("•", item)

            elif profile_key == "iau_industrial_engineering_2027":
                with st.form("iau_gap_form"):
                    c1,c2 = st.columns(2)
                    with c1:
                        school_avg = st.number_input(ui("Current / predicted school average (%)", "Текущий / прогнозируемый средний школьный балл (%)"), min_value=0.0, max_value=100.0, value=0.0, step=0.5)
                        eng_route = st.selectbox(ui("English-proficiency route", "Как вы планируете подтвердить английский?"), ["Not decided","TOEFL iBT","PTE","YÖKDİL / YDS","IAU English Proficiency Exam"])
                    with c2:
                        eng_score = st.text_input(ui("Current score (if available)", "Текущий балл (если уже есть)"))
                        docs_ready = st.multiselect(ui("Documents already ready", "Какие документы уже готовы?"), ["Passport","High-school diploma","High-school transcript"], format_func=lambda x:{"Passport":"Паспорт","High-school diploma":"Школьный диплом / аттестат","High-school transcript":"Школьный transcript"}.get(x,x) if interface_lang()=="ru" else lx(x))
                    save_gap = st.form_submit_button(ui("Build my next-step analysis", "Построить анализ следующих шагов"), type="primary")
                if save_gap:
                    wins, gaps = [], []
                    if school_avg > 0:
                        if school_avg >= 60:
                            wins.append(ui("Your average meets the historical 60% baseline in IAU's 2022 official guideline; re-verify the current 2027 requirement.", "Ваш средний балл достигает исторического ориентира 60% из официального guideline 2022 года; всё равно перепроверьте актуальный минимум для 2027."))
                        else:
                            gaps.append(ui("Average is below the historical 60% baseline in the 2022 guideline; verify the 2027 requirement and strengthen academics.", "Средний балл ниже исторического ориентира 60% из guideline 2022 года; сначала уточните актуальный минимум 2027 и укрепите академические результаты."))
                    else:
                        gaps.append(ui("Enter your current or predicted school average.", "Введите текущий или прогнозируемый школьный средний балл."))
                    if eng_route == "TOEFL iBT" and eng_score.strip():
                        try:
                            score=float(eng_score)
                            if score >= 79: wins.append(ui("TOEFL meets the historical 79 threshold from the 2022 guideline; re-verify for 2027.", "TOEFL достигает исторического порога 79 из guideline 2022 года; перепроверьте для 2027."))
                            else: gaps.append(ui("TOEFL is below the historical 79 threshold; verify the current requirement and continue preparation.", "TOEFL ниже исторического порога 79; перепроверьте актуальное требование и продолжите подготовку."))
                        except Exception: gaps.append(ui("Enter TOEFL as a number.", "Введите TOEFL числом."))
                    elif eng_route == "PTE" and eng_score.strip():
                        try:
                            score=float(eng_score)
                            if score >= 55: wins.append(ui("PTE meets the historical 55 threshold from the 2022 guideline; re-verify for 2027.", "PTE достигает исторического порога 55 из guideline 2022 года; перепроверьте для 2027."))
                            else: gaps.append(ui("PTE is below the historical 55 threshold; verify the current requirement.", "PTE ниже исторического порога 55; перепроверьте актуальное требование."))
                        except Exception: gaps.append(ui("Enter PTE as a number.", "Введите PTE числом."))
                    elif eng_route == "Not decided":
                        gaps.append(ui("Choose an English-proficiency route: an accepted certificate or IAU's internal exam.", "Выберите путь подтверждения английского: принимаемый сертификат или внутренний экзамен IAU."))
                    else:
                        gaps.append(ui("For the selected route, the current undergraduate minimum is not confirmed on the public page used here; re-verify before applying.", "Для выбранного пути текущий undergraduate minimum не подтверждён на используемой публичной странице; перепроверьте его перед подачей."))
                    missing_docs = [x for x in ["Passport","High-school diploma","High-school transcript"] if x not in docs_ready]
                    if not missing_docs: wins.append(ui("Core online-application documents are marked ready.", "Базовый пакет онлайн-заявки отмечен как готовый."))
                    else: gaps.append(("Не готовы: " + ", ".join({"Passport":"паспорт","High-school diploma":"диплом/аттестат","High-school transcript":"transcript"}.get(x,x) for x in missing_docs)) if interface_lang()=="ru" else "Missing: " + ", ".join(missing_docs))
                    st.markdown("#### ✅ " + (ui("Already ready", "Уже готово")))
                    for item in wins: st.write("•", item)
                    st.markdown("#### 🎯 " + (ui("Next steps", "Следующие шаги")))
                    for item in gaps: st.write("•", item)

            st.subheader(ui("8. Preparation pathway", "8. Персональный план подготовки"))
            st.caption(ui("Check off preparation steps; they are saved in demo progress.", "Отмечайте выполненные шаги. Они сохраняются в демо-прогрессе."))
            for idx, course in enumerate(curated["recommended_courses"], start=1):
                key = f"prep_{profile_key}_{idx}"
                checked = key in st.session_state.requirements_checked
                if st.checkbox(course, value=checked, key=f"cb_{key}") != checked:
                    if key in st.session_state.requirements_checked: st.session_state.requirements_checked.remove(key)
                    else: st.session_state.requirements_checked.add(key)
                    sync_persistence(); st.rerun()

            st.subheader(ui("9. Motivation letter builder", "9. Конструктор мотивационного письма"))
            st.write(ui("Build the letter from evidence rather than generic praise.", "Стройте письмо на доказательствах, а не на общих комплиментах университету."))
            why = st.text_area(ui("Why this course?", "Почему эта программа?"), placeholder=(ui("What problem, subject or question keeps your attention?", "Какая проблема, предмет или вопрос удерживает ваше внимание?")), key=f"why_{profile_key}")
            evidence = st.text_area(ui("Best evidence", "Лучшее доказательство"), placeholder=(ui("Describe one project/activity: your role, result, proof and what changed after feedback.", "Опишите один проект/активность: вашу роль, результат, доказательство и что изменилось после обратной связи.")), key=f"evidence_{profile_key}")
            reflection = st.text_area(ui("What did you learn or change?", "Что вы поняли или изменили?"), placeholder=(ui("What assumption changed? What skill became stronger? What would you do differently now?", "Какое предположение изменилось? Какой навык стал сильнее?")), key=f"reflection_{profile_key}")
            future = st.text_area(ui("Why this university and what next?", "Почему этот университет и что дальше?"), placeholder=(ui("Connect specific course features to what you want to learn, research or build next.", "Свяжите конкретные особенности программы с тем, чему хотите научиться, что исследовать или построить.")), key=f"future_{profile_key}")
            if any(x.strip() for x in [why,evidence,reflection,future]):
                if interface_lang()=="ru":
                    draft = (
                        f"Я хочу поступить на программу {curated['program']}, потому что {why.strip()}\n\n"
                        f"Лучшее доказательство моей подготовки — {evidence.strip()}\n\n"
                        f"Этот опыт изменил моё мышление, потому что {reflection.strip()}\n\n"
                        f"{curated['university']} — важный следующий шаг для меня, потому что {future.strip()}"
                    )
                    draft_label = "Структурированный первый черновик"
                    download_label = "Скачать черновик как текст"
                else:
                    draft = (
                        f"I am applying to {curated['program']} because {why.strip()}\n\n"
                        f"The strongest evidence of my preparation is {evidence.strip()}\n\n"
                        f"This experience changed my thinking because {reflection.strip()}\n\n"
                        f"{curated['university']} is a strong next step for me because {future.strip()}"
                    )
                    draft_label = ui("Structured first draft", "Структурированный первый черновик")
                    download_label = ui("Download draft as text", "Скачать черновик как текст")
                st.text_area(draft_label, value=draft, height=260)
                st.download_button(download_label, draft, file_name="motivation_letter_draft.txt", mime="text/plain")

            st.subheader(ui("10. Portfolio evidence tracker", "10. Трекер доказательств для портфолио"))
            st.write(ui("There is no universal required number of achievements. Depth, your personal role, results and proof matter more than a fixed count.", "Нет универсального обязательного количества достижений. Важнее глубина, ваша личная роль, результат и доказательства."))
            st.markdown(ui("**Signals that can strengthen the profile:**", "**Сигналы, которые могут усилить профиль:**"))
            for item in curated["portfolio_signals"]: st.write("•", lx(item))
            with st.form(f"portfolio_add_{profile_key}"):
                p_title = st.text_input(ui("Evidence item", "Элемент портфолио"), placeholder=(ui("Project, research, volunteering, competition, initiative...", "Проект, исследование, волонтёрство, конкурс, инициатива...")))
                p_role = st.text_input(ui("What did you personally do?", "Что именно вы сделали лично?"))
                p_result = st.text_input(ui("Result / impact / measurable outcome", "Результат / влияние / измеримый итог"))
                p_proof = st.text_input(ui("Proof", "Доказательство"), placeholder=(ui("Link, file, certificate, feedback, data, reflection", "Ссылка, файл, сертификат, обратная связь, данные, рефлексия")))
                add = st.form_submit_button(ui("Add evidence item", "Добавить в портфолио"))
            if add and p_title.strip():
                st.session_state.portfolio_items.append({"title":p_title,"role":p_role,"result":p_result,"proof":p_proof})
                st.rerun()
            if st.session_state.portfolio_items:
                st.caption(ui(f"Evidence items in this session: {len(st.session_state.portfolio_items)}. Quality and relevance matter more than reaching a fixed number.", f"Элементов в этой сессии: {len(st.session_state.portfolio_items)}. Качество и релевантность важнее фиксированного числа."))
                for i,item in enumerate(st.session_state.portfolio_items, start=1):
                    role_label = ui("Role", "Роль"); result_label = ui("Result", "Результат"); proof_label = ui("Proof", "Доказательство")
                    st.markdown(f"<div class='card'><b>{i}. {item['title']}</b><br><span class='muted'>{role_label}:</span> {item['role']}<br><span class='muted'>{result_label}:</span> {item['result']}<br><span class='muted'>{proof_label}:</span> {item['proof']}</div>", unsafe_allow_html=True)
                    st.write("")

            st.divider()
            st.caption(ui("Official evidence links", "Официальные источники"))
            source_labels_ru = {"admissions":"Поступление", "program":"Страница программы", "faq":"FAQ", "guideline":"Официальный guideline"}
            source_labels_en = {"admissions":"Admissions", "program":"Program page", "faq":"Admissions FAQ", "guideline":"Official guideline"}
            src_items = list(curated["sources"].items())
            cols = st.columns(min(4, max(1, len(src_items))))
            for idx, (src_key, src_url) in enumerate(src_items):
                if interface_lang()=="ru":
                    label = source_labels_ru.get(src_key, src_key.title()) + " ↗"
                else:
                    label = lx(source_labels_en.get(src_key, src_key.title())) + " ↗"
                cols[idx % len(cols)].link_button(label, src_url, use_container_width=True)

        # -------------------- Generic official-site research fallback --------------------
        else:
            st.subheader(ui("1. ") + t("auto_research"))
            st.info(t("research_fallback"))
            if st.button(t("research_button"), type="primary"):
                st.session_state.pop("automatic_admissions_research_error", None)
                try:
                    with st.spinner(ui("Finding the official university site, programme, exams and admissions requirements...", "Ищу официальный сайт университета, программу, экзамены и требования поступления...")):
                        seed = (plan.get("official_url") or "").strip()
                        if seed and not is_safe_public_url(seed):
                            seed = ""
                        if not seed:
                            seed = discover_official_site_global(
                                plan.get("university", ""), plan.get("country", ""), plan.get("program", ""), ""
                            )

                        deep = None
                        if _openai_api_key():
                            # The deep-search mode can also discover the official website itself
                            # when the lightweight discovery layer could not.
                            deep = deep_research_university_openai(
                                plan.get("country", ""), plan.get("university", ""), plan.get("program", ""),
                                plan.get("level", ""), plan.get("year", ""), seed or ""
                            )
                            if deep and not seed:
                                candidate_site = (deep.get("official_site") or "").strip()
                                if is_safe_public_url(candidate_site):
                                    seed = candidate_site

                        if not seed and not deep:
                            raise RuntimeError("I could not identify the institution's official website automatically.")

                        if deep:
                            st.session_state["automatic_admissions_research"] = {
                                "official_site": deep.get("official_site") or seed,
                                "pages": [], "categories": {}, "exam_scores": [],
                                "contacts": deep.get("contacts") or {}, "deep_research": deep,
                                "checked_at": datetime.utcnow().strftime("%Y-%m-%d"),
                            }
                            pages = None
                        else:
                            pages = collect_official_candidate_pages(
                                seed, plan.get("university", ""), plan.get("country", ""), plan.get("program", ""), max_pages=18
                            )
                        if pages == []:
                            contact_only = discover_contacts_via_search(
                                seed, plan.get("university", ""), plan.get("country", "")
                            )
                            st.session_state["automatic_admissions_research"] = {
                                "official_site": seed,
                                "pages": [],
                                "categories": {},
                                "exam_scores": [],
                                "contacts": contact_only,
                                "checked_at": datetime.utcnow().strftime("%Y-%m-%d"),
                                "contact_only": True,
                            }
                            raise RuntimeError("Official admissions pages could not be read, but contact discovery was attempted.")
                        if pages is not None:
                            contacts = extract_official_contacts(pages, seed)
                            if not contacts.get("emails") and not contacts.get("phones"):
                                contacts = merge_contact_sets(
                                    contacts,
                                    discover_contacts_via_search(seed, plan.get("university", ""), plan.get("country", ""))
                                )
                            result = {
                                "official_site": seed,
                                "pages": [{"title":p["title"], "url":p["url"]} for p in pages],
                                "categories": build_official_research(pages),
                                "exam_scores": extract_exam_score_records(pages),
                                "contacts": contacts,
                                "checked_at": datetime.utcnow().strftime("%Y-%m-%d"),
                            }
                            st.session_state["automatic_admissions_research"] = result
                except Exception as e:
                    st.session_state["automatic_admissions_research_error"] = str(e)

            err = st.session_state.get("automatic_admissions_research_error")
            if err:
                st.warning(ui(
                    "Automatic research is incomplete for this university. The planner tried several retrieval methods and will not invent missing requirements. If contact details were found, they are shown below.",
                    "Автоматический поиск не смог полностью собрать требования этого университета. Планировщик попробовал несколько способов получения данных и не будет придумывать отсутствующую информацию. Если официальные контакты найдены, они показаны ниже."
                ))

            auto = st.session_state.get("automatic_admissions_research", {})
            if auto:
                st.success(ui(
                    f"Official website found. Information checked {auto.get('checked_at','today')}.",
                    f"Официальный сайт найден. Информация проверена {auto.get('checked_at','today')}."
                ))
                st.link_button(ui("Open official university website ↗", "Открыть официальный сайт университета ↗"), auto.get("official_site"), use_container_width=False)

                if auto.get("deep_research"):
                    st.info(ui(
                        "Deep web research checked multiple official admissions pages and PDFs for this university.",
                        "Углублённый веб-поиск проверил несколько официальных страниц поступления и PDF этого университета."
                    ))
                    render_deep_research(auto.get("deep_research"))

                if not auto.get("deep_research"):
                    st.markdown("### " + (ui("Detected exams & published scores", "Найденные экзамены и опубликованные баллы")))
                    exam_rows = auto.get("exam_scores", [])
                    if exam_rows:
                        for i, row in enumerate(exam_rows, start=1):
                            status_text = (
                                ui("Published minimum / requirement", "Опубликованный минимум / требование")
                                if row.get("status") == "requirement"
                                else ui("Published score mentioned", "Опубликованный балл упоминается")
                            )
                            st.markdown(
                                f"<div class='card'><b>{row['exam']}</b><br>"
                                f"<b>{ui('Score', 'Балл')}:</b> {', '.join(row['scores'])}<br>"
                                f"<span>{status_text}</span></div>",
                                unsafe_allow_html=True,
                            )
                            st.link_button(ui("Official source ↗", "Официальный источник ↗"), row["url"], key=f"generic_exam_{i}")
                            st.write("")
                    else:
                        st.warning(ui(
                            "An exact published score was not verified from the official pages that could be read. Opportunity Navigator will not invent one. Use the official admissions contacts below to confirm the missing requirement.",
                            "Точный опубликованный балл не удалось подтвердить на прочитанных официальных страницах. Opportunity Navigator не будет придумывать число. Ниже показаны официальные контакты приёмной комиссии, чтобы уточнить требование."
                        ))

                    for label, rows in auto.get("categories", {}).items():
                        st.markdown(f"### {lx(label)}")
                        if not rows:
                            st.caption(ui("No clear statement was extracted from the official pages read automatically.", "Из автоматически прочитанных официальных страниц не удалось извлечь ясное утверждение."))
                            continue
                        for idx, row in enumerate(rows[:8], start=1):
                            st.write("• " + lx(row["text"]))
                            st.link_button(ui("Source ↗", "Источник ↗"), row["url"], key=f"generic_source_{label}_{idx}")

                    with st.expander(ui("Official pages read by the planner", "Официальные страницы, прочитанные платформой")):
                        for idx, p in enumerate(auto.get("pages", []), start=1):
                            st.write(f"{idx}. {p['title']}")
                            st.link_button(ui("Open page ↗", "Открыть страницу ↗"), p["url"], key=f"generic_page_{idx}")

                    # Useful fallback: official admissions contacts + ready-to-send question.
                    contacts = auto.get("contacts") or {"emails": [], "phones": [], "contact_pages": []}
                    st.markdown("### " + ui("Need clarification? Contact admissions", "Нужно уточнение? Свяжитесь с приёмной комиссией"))
                    st.caption(ui(
                        "If an exam score, document rule or deadline could not be verified automatically, use an official organizational contact rather than guessing.",
                        "Если балл экзамена, документ или дедлайн не удалось подтвердить автоматически, лучше уточнить его через официальный контакт университета, а не угадывать."
                    ))

                    if contacts.get("emails") or contacts.get("phones") or contacts.get("contact_pages"):
                        if contacts.get("emails"):
                            st.markdown("**" + ui("Admissions / university email", "Email приёмной комиссии / университета") + "**")
                            for item in contacts["emails"][:3]:
                                st.write(f"• `{item['value']}`")
                                if item.get("url"):
                                    st.caption(ui("Found on official page:", "Найдено на официальной странице:") + f" {item.get('title') or item['url']}")
                        if contacts.get("phones"):
                            st.markdown("**" + ui("Official phone", "Официальный телефон") + "**")
                            for item in contacts["phones"][:3]:
                                st.write(f"• `{item['value']}`")
                        if contacts.get("contact_pages"):
                            st.markdown("**" + ui("Official contact page", "Официальная страница контактов") + "**")
                            for idx, item in enumerate(contacts["contact_pages"][:3], start=1):
                                st.link_button(
                                    (item.get("title") or ui("Contact page", "Контакты")) + " ↗",
                                    item["url"],
                                    key=f"contact_page_{idx}",
                                )

                        templates = admissions_question_templates(
                            plan,
                            "English-language requirements, entrance exams and minimum scores"
                        )
                        st.markdown("**" + ui("Ready-to-send question", "Готовый вопрос для приёмной комиссии") + "**")
                        if interface_lang() != "en":
                            st.text_area(
                                ui("In your interface language", "На вашем языке"),
                                value=templates["localized"],
                                height=130,
                                key="admissions_question_localized",
                            )
                        st.text_area(
                            ui("English version to send", "Английская версия для отправки"),
                            value=templates["english"],
                            height=130,
                            key="admissions_question_english",
                        )
                    else:
                        st.info(ui(
                            "No public admissions email or phone was extracted automatically. Use the official university website button above and look for Admissions, International Office or Contact Us. The planner did not invent a contact.",
                            "Публичный email или телефон приёмной комиссии автоматически найти не удалось. Используйте кнопку официального сайта выше и разделы Admissions, International Office или Contact Us. Платформа не придумывает контактные данные."
                        ))

            st.subheader(ui("2. ") + t("preparation_areas"))
            st.write(ui("These are inferred preparation areas until the university has a fully curated record. They are not presented as official prerequisites unless the official research above supports them:", "Это предварительные направления подготовки, пока для университета нет полностью проверенной карточки. Они не выдаются за официальные prerequisites без подтверждения источником."))
            for item in program_foundation(plan.get("program","")):
                st.write("•", lx(item))

            st.subheader(ui("3. ") + (ui("Build your evidence while requirements are verified", "Собирайте доказательства, пока требования проверяются")))
            st.write(ui("Use the portfolio tracker below so your application evidence is ready even while the university record is being structured.", "Используйте трекер ниже, чтобы доказательства для заявки были готовы, пока карточка университета дополняется."))
            with st.form("portfolio_add_generic"):
                p_title = st.text_input(ui("Evidence item", "Элемент портфолио"), placeholder=(ui("Project, research, volunteering, competition, initiative...", "Проект, исследование, волонтёрство, конкурс, инициатива...")))
                p_role = st.text_input(ui("What did you personally do?", "Что именно вы сделали лично?"))
                p_result = st.text_input(ui("Result / impact / measurable outcome", "Результат / влияние / измеримый итог"))
                p_proof = st.text_input(ui("Proof", "Доказательство"), placeholder=(ui("Link, file, certificate, feedback, data, reflection", "Ссылка, файл, сертификат, обратная связь, данные, рефлексия")))
                add = st.form_submit_button(ui("Add evidence item", "Добавить элемент"))
            if add and p_title.strip():
                st.session_state.portfolio_items.append({"title":p_title,"role":p_role,"result":p_result,"proof":p_proof})
                st.rerun()
            if st.session_state.portfolio_items:
                for i,item in enumerate(st.session_state.portfolio_items, start=1):
                    st.markdown(
                        f"<div class='card'><b>{i}. {item['title']}</b><br>"
                        f"<span class='muted'>{ui('Role','Роль')}:</span> {item['role']}<br>"
                        f"<span class='muted'>{ui('Result','Результат')}:</span> {item['result']}<br>"
                        f"<span class='muted'>{ui('Proof','Доказательство')}:</span> {item['proof']}</div>",
                        unsafe_allow_html=True,
                    )
                    st.write("")

elif page == "About the Project":
    st.title(t("about_title"))
    st.subheader(ui("What changed after testing", "Что изменилось после тестирования"))
    about_changes_en = """
1. **Language & country:** interface language is separate from country. The selected language is now visible, and core navigation, labels and learner-facing text are translated.
2. **Navigation:** profile → “Open my pathway” works and the current page can be restored after refresh.
3. **AI Tutor:** learners choose subject + topic, describe the exact stuck point and ask repeated follow-up questions.
4. **Adaptive Learning Hub:** lessons start small and mistakes automatically add extra practice.
5. **Motivation:** barrier-matched stories end with a concrete action.
6. **Community safety:** phone numbers, emails and social handles are blocked before moderation submission.
7. **Opportunities:** saved-item counters persist and official provider links open directly.
8. **University Planner:** curated universities use verified structured records; other universities use official-site research, and deployments with an OpenAI API key can use deeper web search across official admissions pages and PDFs.
9. **Persistence:** non-sensitive profile settings and progress survive refresh; export/import is also available.
"""
    about_changes_ru = """
1. **Язык и страна:** язык интерфейса выбирается отдельно от страны. Выбранный язык теперь виден, а основная навигация, подписи и пользовательские тексты переводятся.
2. **Навигация:** профиль → «Открыть мой маршрут» работает, а текущая страница восстанавливается после обновления.
3. **AI-репетитор:** можно выбрать предмет и тему, описать точное затруднение и задавать дополнительные вопросы.
4. **Адаптивный Learning Hub:** урок начинается с небольшого набора, а ошибки автоматически добавляют дополнительную практику.
5. **Мотивация:** истории связаны с барьерами и заканчиваются конкретным действием.
6. **Безопасность Community:** телефоны, email и social handles блокируются до отправки.
7. **Opportunities:** сохранённые возможности считаются, а официальные ссылки открываются напрямую.
8. **University Planner:** для проверенных университетов используются структурированные карточки; для остальных работает поиск по официальным сайтам, а при подключённом OpenAI API key — более глубокий веб-поиск по страницам поступления и PDF.
9. **Сохранение:** несекретные настройки профиля и прогресс сохраняются после обновления; также есть экспорт/импорт.
"""
    st.markdown(ui(about_changes_en, about_changes_ru))

    st.subheader(ui("Product principle", "Принцип продукта"))
    principle = ui(
        "Do not make a teenager assemble the solution alone. Learning, tutoring, motivation, support, admissions planning and opportunity navigation should work as one pathway.",
        "Не заставлять подростка собирать решение по кусочкам. Обучение, репетитор, мотивация, поддержка, поступление и поиск возможностей должны работать как один маршрут."
    )
    st.markdown(f"<div class='notice'><b>{principle}</b></div>", unsafe_allow_html=True)

    st.subheader(ui("What is still a prototype", "Что всё ещё остаётся прототипом"))
    prototype_en = """
- the AI tutor still uses structured teaching logic rather than a fully conversational production tutor;
- live mentor matching is simulated, not connected to a partner network;
- community moderation is demonstrated in-session, not backed by a production database;
- protected, login-only or CAPTCHA-gated university pages can still limit automatic retrieval;
- missing admissions facts are not invented; the planner surfaces official contacts when verification is incomplete;
- production deployment would need authenticated accounts, a database, moderation infrastructure, safeguarding review and production API credentials.
"""
    prototype_ru = """
- AI-репетитор всё ещё использует структурированную учебную логику, а не полноценного production-репетитора;
- реальное сопоставление с наставниками ещё не подключено к партнёрской сети;
- модерация сообщества демонстрационная, без production database;
- защищённые, login-only или CAPTCHA-страницы университетов всё ещё могут ограничивать автоматический поиск;
- отсутствующие требования не придумываются: если проверка неполная, платформа показывает официальные контакты;
- production-версия потребует аккаунтов, базы данных, полноценной модерации, safeguarding review и production API credentials.
"""
    st.markdown(ui(prototype_en, prototype_ru))
