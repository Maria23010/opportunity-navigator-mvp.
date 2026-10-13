"""Motivation collection for Opportunity Navigator.

This module reads 10 small country-independent JSON files from motivation_stories/.
The app's catalog, translations, universities and other pages are not modified.
No external API is required to read Russian biographies or to use the filters.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json
import random

DATA_DIR = Path(__file__).resolve().parent / "motivation_stories"
EXPECTED_FILES = 10
EXPECTED_STORIES = 100


@lru_cache(maxsize=1)
def load_motivation_stories():
    """Return the full collection with explicit diagnostics for missing/corrupted shards."""
    files = sorted(DATA_DIR.glob("stories_??.json"))
    records = []
    issues = []
    if len(files) != EXPECTED_FILES:
        issues.append(f"Ожидалось {EXPECTED_FILES} файлов в motivation_stories, найдено {len(files)}")
    for path in files:
        try:
            with path.open(encoding="utf-8") as f:
                block = json.load(f)
            for item in block.get("stories", []):
                required = {"id", "person", "group", "barriers", "start_ru", "path_ru", "detail_ru", "result_ru", "lesson_ru", "action_ru", "source_url"}
                missing = required - item.keys()
                if missing:
                    issues.append(f"{path.name}: запись {item.get('id','?')} без полей {sorted(missing)}")
                    continue
                records.append(item)
        except (OSError, ValueError, TypeError) as exc:
            issues.append(f"{path.name}: {type(exc).__name__}: {exc}")
    people = [r["person"] for r in records]
    if len(set(people)) != len(people):
        issues.append("Есть повторяющиеся имена людей")
    if len(records) != EXPECTED_STORIES:
        issues.append(f"Загружено {len(records)} историй вместо {EXPECTED_STORIES}")
    return records, issues


_LABELS = {
    "ru": {
        "title": "Мотивация: 100 историй реальных людей",
        "intro": "Трудности не делают ребёнка слабее, а успех не обязан быть знаменитым. Выберите близкую ситуацию, прочитайте историю и возьмите один посильный шаг.",
        "count": "Историй в библиотеке", "barrier": "С какими трудностями познакомиться?", "all_barriers": "Любые трудности",
        "category": "Сфера", "all_categories": "Все сферы", "search": "Поиск по имени, теме или тексту", "search_hint": "Например: медицина, спорт, математика…",
        "choose": "Выберите человека", "random": "🎲 Случайная история", "found": "Подходящих историй: {n}",
        "starting": "С чего начался путь", "steps": "Что человек делал", "detail": "Важные подробности", "result": "К чему это привело", "lesson": "Что можно понять из этой истории",
        "action": "Один небольшой шаг для себя", "source": "Прочитать биографический источник ↗", "save_label": "Моё действие на ближайшее время",
        "save": "Сохранить в «Мой маршрут»", "saved": "Действие сохранено в «Мой маршрут».", "empty": "По этим фильтрам ничего не найдено. Измените запрос или категорию.",
        "translation": "Описание автоматически переводится на выбранный язык при доступности службы перевода. Если она недоступна, показывается русский оригинал.",
        "note": "Истории основаны на биографических сведениях; педагогические выводы и задания составлены для школьников. Это не цитаты героев и не обещание повторить их успех.",
        "science": "Наука и технологии", "society": "Общество и права", "arts": "Искусство и литература", "sports": "Спорт",
    },
    "en": {
        "title": "Motivation: 100 real people's stories", "intro": "Facing barriers does not make you less capable, and success need not mean fame. Find a situation you relate to and choose one manageable action.",
        "count": "Stories in the library", "barrier": "Choose a challenge", "all_barriers": "Any challenge", "category": "Topic", "all_categories": "All topics",
        "search": "Search by person, subject or story", "search_hint": "For example: medicine, sport, mathematics…", "choose": "Choose a person", "random": "🎲 Surprise me",
        "found": "Matching stories: {n}", "starting": "Where it began", "steps": "What they did", "detail": "A closer look", "result": "What happened", "lesson": "What we can learn",
        "action": "One small step to try", "source": "Read biography / source ↗", "save_label": "My next action", "save": "Save to My Pathway", "saved": "Saved to My Pathway.",
        "empty": "No matching stories. Try another topic or search.", "translation": "Full story text is automatically translated if translation is available. Otherwise the original Russian text is shown.",
        "note": "Based on biographical information; educational lessons and actions were written for learners. They are not quotations or promises of comparable success.",
        "science": "Science and technology", "society": "Society and rights", "arts": "Arts and literature", "sports": "Sports",
    },
    "ar": {
        "title": "التحفيز: ١٠٠ قصة حقيقية", "intro": "مواجهة الصعوبات لا تعني ضعف القدرات، والنجاح لا يشترط الشهرة. اختر قصة تناسب تجربتك وخطوة صغيرة يمكنك القيام بها.",
        "count": "عدد القصص", "barrier": "اختر نوع التحدّي", "all_barriers": "جميع التحديات", "category": "المجال", "all_categories": "جميع المجالات",
        "search": "ابحث بالاسم أو المجال أو النص", "search_hint": "مثلاً: الطب، الرياضة، الرياضيات…", "choose": "اختر الشخصية", "random": "🎲 قصة عشوائية",
        "found": "القصص المطابقة: {n}", "starting": "كيف بدأت القصة", "steps": "ما الخطوات التي اتخذها الشخص", "detail": "تفاصيل مهمة", "result": "إلى ماذا أدّت", "lesson": "ما الذي يمكن أن نتعلمه", "action": "خطوة بسيطة لك",
        "source": "اقرأ السيرة أو المصدر ↗", "save_label": "خطوتي التالية", "save": "حفظ في مساري", "saved": "تم الحفظ في مساري.",
        "empty": "لا توجد قصص مطابقة. غيّر الفلتر أو البحث.", "translation": "تُترجم القصص تلقائيًا عند توفّر خدمة الترجمة، وإلا يظهر النص الروسي الأصلي.",
        "note": "القصص تستند إلى معلومات عن السيرة الذاتية. الدروس والأنشطة تعليمية وليست اقتباسات أو وعودًا بتحقيق النجاح نفسه.",
        "science": "العلوم والتكنولوجيا", "society": "المجتمع والحقوق", "arts": "الفنون والآداب", "sports": "الرياضة",
    },
}


def render_motivation_library(lang="ru", translate=None, barrier_formatter=None, sync_callback=None):
    """Draw Motivation page. Translate callback has signature (text, language_code)."""
    import streamlit as st

    labels = _LABELS.get(lang, _LABELS["en"])
    biographies, problems = load_motivation_stories()
    st.title(labels["title"])
    st.write(labels["intro"])
    st.caption(f"{labels['count']}: {len(biographies)}")
    if problems:
        st.error("; ".join(problems))
    if not biographies:
        return

    def local(text):
        if lang == "ru" or not translate or not text:
            return text
        try:
            out = translate(text, lang)
            return out if isinstance(out, str) and out.strip() else text
        except Exception:
            return text

    barriers = sorted({barrier for b in biographies for barrier in b["barriers"]})
    groups = ["science", "society", "arts", "sports"]
    c1, c2 = st.columns(2)
    with c1:
        obstacle = st.selectbox(labels["barrier"], [""] + barriers, format_func=lambda v: (barrier_formatter(v) if v and barrier_formatter else v) if v else labels["all_barriers"], key="motivation_100_barrier")
    with c2:
        group = st.selectbox(labels["category"], [""] + groups, format_func=lambda v: labels[v] if v else labels["all_categories"], key="motivation_100_group")
    phrase = st.text_input(labels["search"], placeholder=labels["search_hint"], key="motivation_100_search").casefold().strip()
    matched = [s for s in biographies if (not obstacle or obstacle in s["barriers"]) and (not group or group == s["group"]) and (not phrase or phrase in " ".join([s["person"], s.get("topic_ru", ""), s.get("person_ar", ""), s["start_ru"], s["path_ru"], s["result_ru"]]).casefold())]
    st.caption(labels["found"].format(n=len(matched)))
    if not matched:
        st.info(labels["empty"])
        return
    if st.button(labels["random"], key="motivation_100_random"):
        st.session_state["motivation_100_pick"] = random.choice(matched)["id"]
    by_id = {s["id"]: s for s in matched}
    chosen_id = st.session_state.get("motivation_100_pick")
    idx = next((i for i, s in enumerate(matched) if s["id"] == chosen_id), 0)
    chosen = st.selectbox(labels["choose"], list(by_id), index=idx, format_func=lambda sid: f"{by_id[sid]['person_ar'] if lang == 'ar' else by_id[sid]['person']} — {labels[by_id[sid]['group']]}")
    story = by_id[chosen]
    st.session_state["motivation_100_pick"] = chosen
    st.markdown(f"### {story.get('person_ar') if lang == 'ar' else story['person']}")
    st.caption(f"{labels[story['group']]} · {local(story['topic_ru'])}")
    for label_key, data_key in [("starting", "start_ru"), ("steps", "path_ru"), ("detail", "detail_ru"), ("result", "result_ru"), ("lesson", "lesson_ru"), ("action", "action_ru")]:
        st.markdown(f"**{labels[label_key]}**")
        st.write(local(story[data_key]))
    st.link_button(labels["source"], story["source_url"])
    st.caption(labels["note"])
    if lang != "ru":
        st.caption(labels["translation"])
    action = st.text_area(labels["save_label"], value=local(story["action_ru"]), key=f"motivation_action_{story['id']}_{lang}")
    if st.button(labels["save"], type="primary", key="motivation_100_save"):
        if action.strip():
            saved = st.session_state.setdefault("saved_actions", [])
            if action.strip() not in saved:
                saved.append(action.strip())
                if sync_callback:
                    sync_callback()
            st.success(labels["saved"])
