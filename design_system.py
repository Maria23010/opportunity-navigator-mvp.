"""Opportunity Navigator visual layer. CSS only; no application state changes."""
import streamlit as st


def apply_design():
    st.markdown('''<style>
/* Opportunity Navigator / calm contemporary educational UI */
:root {--on-navy:#172b4d;--on-blue:#4566df;--on-edge:#e4eaf4;--on-muted:#64748b;}
[data-testid="stAppViewContainer"] {background:radial-gradient(ellipse 85% 40% at 90% 0%,#eaf1ff 0%,transparent 72%),linear-gradient(165deg,#f8faff,#fff 55%,#f8fbff)!important;}
[data-testid="stAppViewContainer"] .block-container {max-width:1160px;padding-top:2.35rem;padding-bottom:5rem;}
[data-testid="stAppViewContainer"] h1 {font-size:clamp(2rem,3.5vw,2.75rem);font-weight:790;letter-spacing:-.045em;line-height:1.16;color:#1a2e51;}
[data-testid="stAppViewContainer"] h2 {font-weight:760;letter-spacing:-.033em;color:#20385d;}
[data-testid="stAppViewContainer"] h3 {font-weight:730;letter-spacing:-.025em;color:#274064;}
[data-testid="stAppViewContainer"] p {line-height:1.72;}
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {color:#62718b;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#142441 0%,#192c50 64%,#233b67 100%)!important;border-right:1px solid #314568;}
[data-testid="stSidebar"] .site-title {font-size:1.22rem;letter-spacing:-.03em;line-height:1.4;}
[data-testid="stSidebar"] .stButton button {border-radius:13px!important;min-height:44px!important;padding:.65rem .8rem!important;transition:background .18s,transform .18s!important;}
[data-testid="stSidebar"] .stButton button:hover {background:#ffffff20!important;transform:translateX(2px);}
[data-testid="stSidebar"] [data-testid="stExpander"] {border:1px solid #ffffff24;border-radius:14px;}
[data-testid="stAppViewContainer"] [data-testid="stVerticalBlockBorderWrapper"] > div {border-radius:20px!important;}
[data-testid="stAppViewContainer"] [data-testid="stMetric"] {border:1px solid var(--on-edge);background:#fff;border-radius:18px;padding:1rem;box-shadow:0 4px 20px #1b3a7210;}
[data-testid="stAppViewContainer"] [data-testid="stMetricValue"] {color:#233f7b;font-weight:780;}
[data-testid="stAppViewContainer"] div[data-baseweb="select"] > div,
[data-testid="stAppViewContainer"] div[data-baseweb="input"] > div,
[data-testid="stAppViewContainer"] textarea {border-radius:13px!important;border-color:#d8e1ef!important;background:#fff!important;min-height:45px;}
[data-testid="stAppViewContainer"] :is(input,textarea):focus-visible {outline:2px solid #7b95f0!important;outline-offset:1px;}
[data-testid="stAppViewContainer"] :is(.stButton button,.stDownloadButton button,.stLinkButton a) {border-radius:13px!important;min-height:44px;box-shadow:none;transition:transform .16s,box-shadow .16s,border-color .16s;}
[data-testid="stAppViewContainer"] :is(.stButton button,.stDownloadButton button,.stLinkButton a):hover {transform:translateY(-1px);box-shadow:0 8px 20px #23457918;}
[data-testid="stAppViewContainer"] button[kind="primary"] {background:#4164df!important;border-color:#4164df!important;color:#fff!important;}
[data-testid="stAppViewContainer"] button[kind="primary"]:hover {background:#3154d3!important;border-color:#3154d3!important;}
[data-testid="stAppViewContainer"] [data-testid="stTabs"] [data-baseweb="tab-list"] {gap:.3rem;border-bottom:1px solid #e2e9f4;flex-wrap:wrap;}
[data-testid="stAppViewContainer"] [data-testid="stTabs"] [role="tab"] {border-radius:11px 11px 0 0;padding:.7rem 1rem;font-weight:650;}
[data-testid="stAppViewContainer"] [data-testid="stExpander"] {border:1px solid #e0e8f3;border-radius:16px;background:#ffffffc9;overflow:hidden;}
[data-testid="stAppViewContainer"] [data-testid="stAlert"] {border-radius:15px;}
[data-testid="stChatMessage"] {border:1px solid #e3eaf5!important;border-radius:18px!important;background:#fff!important;box-shadow:0 3px 14px #1c40750a;padding:1rem!important;}
[data-testid="stAppViewContainer"] .hero {border-radius:26px;box-shadow:0 15px 35px #2858b52b;}
[data-testid="stAppViewContainer"] a {text-underline-offset:3px;}
[data-testid="stAppViewContainer"] :is(button,a,input,textarea,[role="tab"]):focus-visible {outline:3px solid #8da4f5;outline-offset:2px;}
@media(max-width:800px) { [data-testid="stAppViewContainer"] .block-container {padding:1.15rem .9rem 3rem;} [data-testid="stAppViewContainer"] .hero {padding:1.5rem!important;border-radius:19px;} [data-testid="stAppViewContainer"] .hero h1 {font-size:2rem!important;} }
@media(prefers-reduced-motion:reduce) {*,*:before,*:after {transition:none!important;animation:none!important;scroll-behavior:auto!important;} }
</style>''', unsafe_allow_html=True)


def apply_home_refresh():
    """Readable editorial home screen; no changes to app logic."""
    st.markdown('''<style>
    [data-testid="stAppViewContainer"] .hero {background:#eef3ff!important;border:1px solid #dbe5fb!important;box-shadow:none!important;padding:32px 36px!important;border-radius:20px!important;margin-bottom:20px!important;}
    [data-testid="stAppViewContainer"] .hero .eyebrow {color:#4664a4!important;opacity:1!important;letter-spacing:.07em!important;font-size:.70rem!important;margin-bottom:10px!important;}
    [data-testid="stAppViewContainer"] .hero h1 {color:#182b4a!important;font-size:clamp(1.8rem,2.7vw,2.6rem)!important;line-height:1.2!important;letter-spacing:-.035em!important;max-width:850px!important;margin-bottom:14px!important;}
    [data-testid="stAppViewContainer"] .hero p {color:#415572!important;font-size:1rem!important;line-height:1.65!important;opacity:1!important;max-width:760px!important;margin:0!important;}
    [data-testid="stAppViewContainer"] .feature-card {background:#fff!important;border:1px solid #e0e6f0!important;border-radius:18px!important;padding:23px!important;min-height:220px!important;box-shadow:0 6px 18px rgba(21,45,88,.035)!important;}
    [data-testid="stAppViewContainer"] .feature-card .label {color:#5374aa!important;letter-spacing:.055em!important;font-size:.69rem!important;}
    [data-testid="stAppViewContainer"] .feature-card h3 {color:#1d3151!important;font-size:1.26rem!important;line-height:1.32!important;margin:12px 0!important;}
    [data-testid="stAppViewContainer"] .feature-card p {color:#50627c!important;font-size:.94rem!important;line-height:1.55!important;}
    [data-testid="stSidebar"] .stButton button {font-size:.91rem!important;min-height:40px!important;}
    @media(max-width:850px){[data-testid="stAppViewContainer"] .hero{padding:22px!important;}[data-testid="stAppViewContainer"] .feature-card{min-height:unset!important;}}
    </style>''',unsafe_allow_html=True)
