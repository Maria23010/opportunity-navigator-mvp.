"""Invite-only pilot UX for Opportunity Navigator.

IMPORTANT: This module is a session-local, clearly labeled interactive demonstration.
No message is sent to another person or persisted in shared storage. Do not enable
real minor-to-minor or minor-to-adult messaging without authentication, durable
storage, verified moderation, reporting and appropriate child-safety processes.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timezone

import streamlit as st


COPY = {
    "ru": {
        "notifications": "Уведомления", "inbox": "Мои сообщения", "empty": "Пока новых уведомлений нет.",
        "no_real": "Демонстрационный режим: настоящие сообщения другим людям не отправляются.",
        "demo": "Демо", "closed": "Закрытый тест", "beta": "Тестовый доступ",
        "invite": "Код приглашения", "unlock": "Войти в тестовый режим", "invite_ok": "Тестовый доступ открыт для этой сессии.",
        "invite_bad": "Код приглашения не подошёл.",
        "test_not_configured": "Код для приглашённых тестировщиков пока не настроен владельцем платформы. Интерактивное демо доступно ниже.",
        "demo_intro": "Можно попробовать создание запроса, ответы и уведомления. Это пример работы будущего сервиса, а не переписка с реальными людьми.",
        "support_title": "Поддержка человека", "support_info": "Оставьте учебный запрос и посмотрите, как выглядело бы сопровождение от проверенного наставника.",
        "kind": "Какая помощь нужна?", "language": "На каком языке?", "request": "Опишите, с чем нужна помощь", "submit": "Создать демонстрационный запрос",
        "kind_options": ["Учебный наставник", "Репетитор", "Помощь с поступлением", "Школьная поддержка"],
        "created": "Запрос сохранён в этой сессии. Реальному человеку он не отправлен.",
        "contact": "Не указывайте фамилию, школу, адрес, телефон, почту или аккаунты в соцсетях.",
        "validation": "Напишите не менее 12 символов и уберите личные контакты и ссылки.",
        "my_requests": "Мои учебные запросы", "status_new": "Сохранён (демо)", "status_replied": "Есть отклик (демо)",
        "simulate": "Показать пример отклика наставника", "mentor_title": "Демо-наставник · учебный пример",
        "mentor_reply": "Спасибо за вопрос! Попробуем начать с одного маленького шага. Напиши, какую тему ты уже понимаешь, и где именно возникла трудность. Затем разберём один похожий пример.",
        "respond": "Пример переписки", "sample_reply": "Спасибо! Я попробую решить один похожий пример.",
        "community_title": "Сообщество", "community_info": "Тематические вопросы и ответы с проверкой перед публикацией. Сейчас показан учебный сценарий.",
        "rooms": "Темы", "topics": ["Все", "Математика", "Английский", "Программирование", "Учёба", "Поступление", "Мотивация"],
        "sample_questions": [
            ("Математика", "Как тренироваться перед олимпиадой, если задачи кажутся слишком сложными?", "Начни с задач прошлых лет и разбирай по одной ошибке за раз."),
            ("Английский", "Как улучшить английский, если я боюсь разговаривать?", "Попробуй сначала короткие голосовые заметки для себя и маленькие диалоги."),
            ("Поступление", "Как сравнить два университета?", "Составь таблицу: программа, язык, экзамены, стоимость и официальные сроки."),
        ],
        "example": "Пример обсуждения", "reply": "Пример ответа", "ask": "Задать вопрос", "subject": "Выберите тему", "question": "Ваш вопрос", "submit_question": "Сохранить вопрос (демо)",
        "question_created": "Вопрос добавлен в личный список демонстрационной сессии. Он не опубликован для других пользователей.",
        "my_questions": "Мои вопросы", "pending": "Ожидает демонстрационной проверки", "approved": "Проверено в демо", "answered": "На вопрос ответили (демо)",
        "moderate": "Показать пример модерации", "demo_answer": "Показать пример ответа сообщества",
        "sample_community_answer": "Полезно разбить задачу на шаги, тренироваться понемногу каждый день и спрашивать уточнения. Если вопрос касается поступления, проверяй требования на официальном сайте.",
        "all_messages": "Центр сообщений", "support_tab": "Помощь наставника", "community_tab": "Ответы сообщества", "notifications_tab": "Уведомления",
        "go_support": "Открыть поддержку", "go_community": "Открыть сообщество", "nothing": "Когда вы создадите демо-запрос или вопрос, он появится здесь.",
        "pilot_caption": "Будущая закрытая бета: приглашённые участники, подтверждённые модераторы, сохранённые вопросы и настоящие уведомления. Сейчас обмена сообщениями между пользователями нет.",
        "n_support": "Ваш запрос на учебную помощь сохранён", "n_mentor": "На ваш запрос о помощи поступил отклик",
        "n_tutor": "На ваш запрос о репетиторе поступил отклик",
        "n_question": "Ваш вопрос в сообществе сохранён", "n_moderated": "Ваш вопрос прошёл проверку", "n_answer": "На ваш вопрос в сообществе появился ответ",
        "security": "При опасности или серьёзном эмоциональном кризисе обратитесь к безопасному взрослому или в местную службу помощи: этот демо-раздел не принимает экстренные обращения.",
    },
    "en": {
        "notifications": "Notifications", "inbox": "My messages", "empty": "No new notifications yet.",
        "no_real": "Demo mode: no messages are sent to real people.", "demo": "Demo", "closed": "Closed pilot", "beta": "Pilot access",
        "invite": "Invitation code", "unlock": "Enter pilot", "invite_ok": "Pilot access enabled for this session.", "invite_bad": "Invitation code was not accepted.",
        "test_not_configured": "An invitation code hasn't been configured yet. You can still explore the interactive demo.",
        "demo_intro": "Try sample requests, responses and notifications. This demonstrates a future service; it is not a conversation with real people.",
        "support_title": "Human support", "support_info": "Create a sample study request and see how a verified mentor could respond.",
        "kind": "What kind of support?", "language": "Preferred language", "request": "Describe what you need help with", "submit": "Create sample request",
        "kind_options": ["Academic mentor", "Tutor", "University admissions", "School support"],
        "created": "Saved in this session. The request was not sent to a person.", "contact": "Do not share your surname, school, address, telephone, email or social handles.",
        "validation": "Write at least 12 characters and remove all personal contact details and links.",
        "my_requests": "My study requests", "status_new": "Saved (demo)", "status_replied": "Reply available (demo)",
        "simulate": "Show a mentor's sample reply", "mentor_title": "Sample mentor · demonstration",
        "mentor_reply": "Thanks for asking! Let's begin with one small step. Tell me what you already understand and where you get stuck. Then work through a similar example.",
        "respond": "Sample conversation", "sample_reply": "Thanks! I'll try one similar example.",
        "community_title": "Community", "community_info": "Topic-based questions and answers with review before publication. This is an interactive demonstration.",
        "rooms": "Topics", "topics": ["All", "Math", "English", "Coding", "Study skills", "Admissions", "Motivation"],
        "sample_questions": [
            ("Math", "How can I prepare for an olympiad when problems feel too difficult?", "Start with previous years' problems, and review one mistake at a time."),
            ("English", "How can I improve English if I'm afraid to speak?", "Start with short voice notes to yourself and mini conversations."),
            ("Admissions", "How should I compare two universities?", "Use a table: course, language, exams, cost and official deadlines."),
        ],
        "example": "Sample discussion", "reply": "Sample answer", "ask": "Ask a question", "subject": "Choose topic", "question": "Your question", "submit_question": "Save question (demo)",
        "question_created": "Your question was saved in this demo session. It has not been published to others.",
        "my_questions": "My questions", "pending": "Awaiting sample review", "approved": "Reviewed in demo", "answered": "A reply is available (demo)",
        "moderate": "Show sample moderation", "demo_answer": "Show sample community answer",
        "sample_community_answer": "Try splitting the challenge into small steps and practicing consistently. Ask clarifying questions, and check official sources for admissions details.",
        "all_messages": "Message center", "support_tab": "Mentor support", "community_tab": "Community replies", "notifications_tab": "Notifications",
        "go_support": "Open support", "go_community": "Open community", "nothing": "Your demo requests and questions will appear here.",
        "pilot_caption": "Future private pilot: invited participants, verified moderators, stored questions and real notifications. Cross-user messaging is not enabled yet.",
        "n_support": "Your study support request was saved", "n_mentor": "Your support request received a response",
        "n_tutor": "Your tutoring request received a response",
        "n_question": "Your community question was saved", "n_moderated": "Your question passed review", "n_answer": "Someone replied to your community question",
        "security": "If you are in danger or experiencing an urgent emotional crisis, contact a trusted adult or local support service; this demo is not an emergency service.",
    },
    "ar": {
        "notifications": "الإشعارات", "inbox": "رسائلي", "empty": "لا توجد إشعارات جديدة.", "no_real": "الوضع التجريبي: لا تُرسل الرسائل إلى أشخاص حقيقيين.",
        "demo": "تجريبي", "closed": "اختبار مغلق", "beta": "الدخول التجريبي", "invite": "رمز الدعوة", "unlock": "دخول الاختبار", "invite_ok": "تم تفعيل الدخول للاختبار في هذه الجلسة.", "invite_bad": "رمز الدعوة غير صحيح.",
        "test_not_configured": "لم يتم إعداد رمز الدعوة بعد. يمكنك تجربة العرض التفاعلي.",
        "demo_intro": "جرّب الطلبات والردود والإشعارات النموذجية. هذه محاكاة لخدمة مستقبلية وليست محادثة حقيقية.",
        "support_title": "دعم من شخص", "support_info": "أنشئ طلب مساعدة دراسية تجريبياً وشاهد مثالاً على رد المرشد.",
        "kind": "نوع المساعدة", "language": "اللغة المفضلة", "request": "بماذا تحتاج إلى مساعدة؟", "submit": "إنشاء طلب تجريبي",
        "kind_options": ["مرشد دراسي", "مدرس خصوصي", "مساعدة في القبول الجامعي", "دعم مدرسي"],
        "created": "تم الحفظ في هذه الجلسة، ولم يتم إرسال الطلب إلى أي شخص.", "contact": "لا تكتب اسم العائلة أو المدرسة أو العنوان أو الهاتف أو البريد أو حسابات التواصل.",
        "validation": "اكتب 12 حرفاً على الأقل واحذف معلومات الاتصال والروابط.", "my_requests": "طلباتي الدراسية", "status_new": "محفوظ (تجريبي)", "status_replied": "يوجد رد (تجريبي)",
        "simulate": "عرض رد نموذجي من المرشد", "mentor_title": "مرشد نموذجي · عرض توضيحي",
        "mentor_reply": "شكراً لسؤالك! لنبدأ بخطوة صغيرة. ما الذي تفهمه بالفعل وأين تواجه الصعوبة؟ ثم نراجع مثالاً مشابهاً.",
        "respond": "محادثة نموذجية", "sample_reply": "شكراً، سأجرب مثالاً مشابهاً.",
        "community_title": "المجتمع", "community_info": "أسئلة وأجوبة حسب المواضيع تخضع للمراجعة قبل النشر. هذا عرض تفاعلي فقط.",
        "rooms": "المواضيع", "topics": ["الكل", "الرياضيات", "الإنجليزية", "البرمجة", "مهارات الدراسة", "القبول الجامعي", "التحفيز"],
        "sample_questions": [("الرياضيات", "كيف أستعد للأولمبياد عندما تكون المسائل صعبة؟", "ابدأ بمسائل السنوات السابقة وراجع خطأ واحداً كل مرة."), ("الإنجليزية", "كيف أطور الإنجليزية إذا كنت أخاف التحدث؟", "ابدأ بتسجيلات صوتية قصيرة لنفسك."), ("القبول الجامعي", "كيف أقارن بين جامعتين؟", "قارن البرنامج واللغة والاختبارات والتكاليف والمواعيد الرسمية.")],
        "example": "مناقشة نموذجية", "reply": "إجابة نموذجية", "ask": "طرح سؤال", "subject": "اختر الموضوع", "question": "سؤالك", "submit_question": "حفظ السؤال (تجريبي)",
        "question_created": "تم حفظ السؤال في هذه الجلسة التجريبية، ولم يُنشر للآخرين.",
        "my_questions": "أسئلتي", "pending": "بانتظار مراجعة تجريبية", "approved": "تمت مراجعته في العرض", "answered": "وصل رد على السؤال (تجريبي)",
        "moderate": "عرض مثال المراجعة", "demo_answer": "عرض إجابة مجتمعية نموذجية", "sample_community_answer": "قسّم المهمة إلى خطوات صغيرة وتدرّب باستمرار. تحقق من المصادر الرسمية لشروط القبول.",
        "all_messages": "مركز الرسائل", "support_tab": "دعم المرشد", "community_tab": "ردود المجتمع", "notifications_tab": "الإشعارات",
        "go_support": "فتح الدعم", "go_community": "فتح المجتمع", "nothing": "ستظهر طلباتك وأسئلتك التجريبية هنا.",
        "pilot_caption": "اختبار خاص مستقبلاً: مشاركون مدعوون ومشرفون موثوقون وأسئلة محفوظة وإشعارات حقيقية. لا توجد مراسلة فعلية بين المستخدمين الآن.",
        "n_support": "تم حفظ طلب المساعدة الدراسية", "n_mentor": "وصل رد على طلب المساعدة الخاص بك",
        "n_tutor": "وصل رد على طلب المدرّس الخصوصي",
        "n_question": "تم حفظ سؤالك في المجتمع", "n_moderated": "اجتاز سؤالك المراجعة", "n_answer": "وصل رد على سؤالك في المجتمع",
        "security": "عند الخطر أو الأزمات النفسية العاجلة، تواصل مع شخص بالغ موثوق أو خدمة محلية. العرض التجريبي ليس خدمة طوارئ.",
    },
    "kk": {
        "notifications": "Хабарламалар", "inbox": "Менің хабарламаларым", "empty": "Әзірге жаңа хабарлама жоқ.", "no_real": "Демо: хабарламалар нақты адамдарға жіберілмейді.",
        "demo": "Демо", "closed": "Жабық сынақ", "beta": "Сынаққа кіру", "invite": "Шақыру коды", "unlock": "Сынаққа кіру", "invite_ok": "Осы сессияда сынаққа кіруге болады.", "invite_bad": "Код дұрыс емес.",
        "test_not_configured": "Шақыру коды әлі орнатылмаған. Интерактивті демоны көруге болады.",
        "demo_intro": "Сұраулар, жауаптар және хабарламалар үлгісін көріңіз. Бұл нақты адамдармен хат алмасу емес.",
        "support_title": "Адам көмегі", "support_info": "Оқу көмегіне сұраныс жасап, тәлімгер жауабының үлгісін көріңіз.",
        "kind": "Қандай көмек керек?", "language": "Қолайлы тіл", "request": "Қандай көмектің қажет екенін жазыңыз", "submit": "Демо сұрау жасау",
        "kind_options": ["Оқу тәлімгері", "Репетитор", "Университетке түсу", "Мектептік қолдау"],
        "created": "Осы сессияда сақталды. Нақты адамға жіберілмеді.", "contact": "Тегіңізді, мектебіңізді, мекенжайыңызды, телефонды не әлеуметтік желі аккаунтын жазбаңыз.",
        "validation": "Кемінде 12 таңба жазыңыз, жеке байланыс деректері мен сілтемелерді алып тастаңыз.",
        "my_requests": "Оқу сұрауларым", "status_new": "Сақталды (демо)", "status_replied": "Жауап бар (демо)",
        "simulate": "Тәлімгер жауабының үлгісін көру", "mentor_title": "Демо тәлімгер · үлгі", "mentor_reply": "Сұрағыңызға рақмет! Алдымен нені білетініңізді және қай жерде қиналғаныңызды анықтайық. Сосын бір ұқсас мысалды талдайық.",
        "respond": "Үлгі әңгіме", "sample_reply": "Рақмет, ұқсас мысалды шығарып көремін.",
        "community_title": "Қауымдастық", "community_info": "Сұрақтар жарияланар алдында тексеріледі. Қазір интерактивті демо көрсетілген.",
        "rooms": "Тақырыптар", "topics": ["Барлығы", "Математика", "Ағылшын", "Бағдарламалау", "Оқу", "Түсу", "Мотивация"],
        "sample_questions": [("Математика", "Қиын есептер болса, олимпиадаға қалай дайындаламын?", "Өткен жылғы есептерден бастап, қателерді бір-бірлеп талдаңыз."), ("Ағылшын", "Сөйлесуге қорықсам, ағылшын тілін қалай жақсартамын?", "Алдымен өзіңізге қысқа аудио жазып көріңіз."), ("Түсу", "Екі университетті қалай салыстырамын?", "Бағдарлама, тіл, емтихан, шығын және мерзімдерді салыстырыңыз.")],
        "example": "Үлгі талқылау", "reply": "Жауап үлгісі", "ask": "Сұрақ қою", "subject": "Тақырыпты таңдаңыз", "question": "Сұрағыңыз", "submit_question": "Сақтау (демо)",
        "question_created": "Сұрақ осы демо-сессияда сақталды, өзгелерге жарияланған жоқ.",
        "my_questions": "Сұрақтарым", "pending": "Демо тексеруді күтуде", "approved": "Демода тексерілді", "answered": "Сұраққа жауап келді (демо)",
        "moderate": "Тексеру үлгісін көрсету", "demo_answer": "Қауымдастық жауабының үлгісі", "sample_community_answer": "Тапсырманы шағын бөліктерге бөліп, үнемі жаттығыңыз. Түсу талаптарын ресми дереккөзден қараңыз.",
        "all_messages": "Хабарламалар орталығы", "support_tab": "Тәлімгер көмегі", "community_tab": "Қауымдастық жауаптары", "notifications_tab": "Хабарламалар",
        "go_support": "Көмекке өту", "go_community": "Қауымдастыққа өту", "nothing": "Демо-сұраулар мен сұрақтар осы жерде көрінеді.",
        "pilot_caption": "Болашақ жабық сынақ: шақырылған қатысушылар, тексерілген модераторлар, сақталатын сұрақтар және шынайы хабарламалар. Қазір пайдаланушылар арасында хабар алмасу жоқ.",
        "n_support": "Оқу көмегіне сұрауыңыз сақталды", "n_mentor": "Көмек сұрауыңызға жауап келді",
        "n_tutor": "Репетитор көмегіне сұрауыңызға жауап келді",
        "n_question": "Қауымдастықтағы сұрағыңыз сақталды", "n_moderated": "Сұрағыңыз тексеруден өтті", "n_answer": "Қауымдастықтағы сұрағыңызға жауап келді",
        "security": "Қауіп немесе ауыр эмоционалдық дағдарыс кезінде сенімді ересекке не жергілікті көмек қызметіне хабарласыңыз. Бұл демо шұғыл көмек емес.",
    },
}


def loc(language: str, key: str):
    return COPY.get(language, COPY["en"]).get(key, COPY["en"].get(key, key))


def _init():
    for key, value in {
        "beta_support": [], "beta_questions": [], "beta_alerts": [],
        "beta_access": False,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, list) else value


def _new_id(prefix):
    return f"{prefix}-{secrets.token_hex(3).upper()}"


def _notify(code, ref):
    st.session_state.beta_alerts.insert(0, {
        "id": _new_id("N"), "code": code, "ref": ref,
        "when": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "read": False,
    })
    st.session_state.beta_alerts[:] = st.session_state.beta_alerts[:30]


def _invalid(text):
    if len(text.strip()) < 12 or len(text) > 700:
        return True
    patterns = [
        r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
        r"(?<!\d)(?:\+?\d[\d \-.()]{6,}\d)(?!\d)",
        r"https?://|www\.",
        r"(?<!\w)@[\w.]{2,}",
        r"(?i)\b(?:instagram|telegram|snapchat|whatsapp|discord|tiktok)\s*[:=@]?[\w.]{2,}",
    ]
    return any(re.search(p, text) for p in patterns)


def _invite_code_hash():
    try:
        secret = st.secrets.get("BETA_INVITE_CODE_SHA256", "")
        return str(secret).strip().lower()
    except Exception:
        return ""


def _can_interact():
    """Demo stays readable; configured invited pilot gates the interactive forms."""
    return not _invite_code_hash() or st.session_state.get("beta_access", False)


def invite_panel(language):
    _init()
    with st.expander(f"🔒 {loc(language, 'closed')}", expanded=False):
        st.caption(loc(language, "pilot_caption"))
        expected_hash = _invite_code_hash()
        if not expected_hash:
            st.info(loc(language, "test_not_configured"))
            return
        if st.session_state.beta_access:
            st.success(loc(language, "invite_ok"))
            return
        with st.form("beta_invite_form"):
            value = st.text_input(loc(language, "invite"), type="password", max_chars=100)
            if st.form_submit_button(loc(language, "unlock")):
                matched = hmac.compare_digest(hashlib.sha256(value.encode()).hexdigest(), expected_hash)
                if matched and value:
                    st.session_state.beta_access = True
                    st.success(loc(language, "invite_ok"))
                    st.rerun()
                else:
                    st.error(loc(language, "invite_bad"))



def _notification_title(language, note):
    """Make alert wording user-friendly while retaining the demo disclosure."""
    code = note.get("code", "")
    if code == "n_mentor":
        support = next((x for x in st.session_state.beta_support
                        if x.get("id") == note.get("ref")), None)
        if support and support.get("kind") == 1:
            code = "n_tutor"
    return loc(language, code)


def notification_button(language, go_page):
    _init()
    unread = sum(not x["read"] for x in st.session_state.beta_alerts)
    left, right = st.columns([8, 2])
    with right:
        with st.popover(f"🔔 {loc(language, 'notifications')} ({unread})", use_container_width=True):
            if st.session_state.beta_alerts:
                for note in st.session_state.beta_alerts[:5]:
                    st.write(f"**{_notification_title(language, note)}**")
                    st.caption(f"{loc(language, 'demo')} · {note['when']}")
                if st.button(loc(language, "inbox"), key="beta_nav_inbox", use_container_width=True):
                    for note in st.session_state.beta_alerts:
                        note["read"] = True
                    go_page("Messages")
            else:
                st.caption(loc(language, "empty"))


def _banner(language):
    st.info(f"**{loc(language, 'demo')}** · {loc(language, 'no_real')}")


def render_support(language, sync_callback=None):
    _init()
    st.title(f"🤝 {loc(language, 'support_title')}")
    _banner(language)
    st.write(loc(language, "support_info"))
    st.caption(loc(language, "contact"))
    with st.form("pilot_support_form", clear_on_submit=True):
        kind_labels = loc(language, "kind_options")
        kind_idx = st.selectbox(loc(language, "kind"), list(range(4)), format_func=lambda i: kind_labels[i])
        preferred = st.selectbox(loc(language, "language"), ["Русский", "English", "Қазақша", "العربية", "Other"])
        text = st.text_area(loc(language, "request"), max_chars=700)
        sent = st.form_submit_button(loc(language, "submit"), type="primary", disabled=not _can_interact())
    if sent:
        if _invalid(text):
            st.error(loc(language, "validation"))
        else:
            item = {"id": _new_id("SUP"), "kind": kind_idx, "language": preferred,
                    "text": text.strip(), "status": "new", "chat": []}
            st.session_state.beta_support.insert(0, item)
            st.session_state.support_request_count = int(st.session_state.get("support_request_count", 0)) + 1
            if sync_callback is not None:
                sync_callback()
            _notify("n_support", item["id"])
            st.success(loc(language, "created"))
    if st.session_state.beta_support:
        st.subheader(loc(language, "my_requests"))
        for item in st.session_state.beta_support:
            with st.expander(f"{item['id']} · {kind_labels[item['kind']]} · {loc(language, 'status_replied' if item['status'] == 'replied' else 'status_new')}"):
                st.write(item["text"])
                if item["status"] == "new":
                    if st.button(loc(language, "simulate"), key=f"support_sim_{item['id']}"):
                        item["status"] = "replied"
                        item["chat"] = ["mentor"]
                        _notify("n_mentor", item["id"])
                        st.rerun()
                else:
                    st.markdown(f"**{loc(language, 'mentor_title')}**")
                    st.write(loc(language, "mentor_reply"))
                    if "learner" not in item["chat"] and st.button(loc(language, "sample_reply"), key=f"sample_reply_{item['id']}"):
                        item["chat"].append("learner")
                        st.rerun()
                    if "learner" in item["chat"]:
                        st.write("💬 " + loc(language, "sample_reply"))
    st.caption(loc(language, "security"))
    invite_panel(language)


def render_community(language):
    _init()
    st.title(f"💬 {loc(language, 'community_title')}")
    _banner(language)
    st.write(loc(language, "community_info"))
    topics = loc(language, "topics")
    choice = st.selectbox(loc(language, "rooms"), list(range(7)), format_func=lambda i: topics[i], key="beta_filter_topics")
    for subject, question, answer in loc(language, "sample_questions"):
        if choice and topics[choice] != subject:
            continue
        with st.container(border=True):
            st.caption(f"{loc(language, 'example')} · {subject}")
            st.write("**" + question + "**")
            st.write(f"{loc(language, 'reply')}: {answer}")
    st.subheader(loc(language, "ask"))
    st.caption(loc(language, "contact"))
    with st.form("pilot_question_form", clear_on_submit=True):
        idx = st.selectbox(loc(language, "subject"), list(range(1, 7)), format_func=lambda i: topics[i])
        text = st.text_area(loc(language, "question"), max_chars=700)
        submitted = st.form_submit_button(loc(language, "submit_question"), type="primary", disabled=not _can_interact())
    if submitted:
        if _invalid(text):
            st.error(loc(language, "validation"))
        else:
            item = {"id": _new_id("Q"), "topic": idx, "question": text.strip(), "status": "pending"}
            st.session_state.beta_questions.insert(0, item)
            _notify("n_question", item["id"])
            st.success(loc(language, "question_created"))
    if st.session_state.beta_questions:
        st.subheader(loc(language, "my_questions"))
        for item in st.session_state.beta_questions:
            label = "pending" if item["status"] == "pending" else "approved" if item["status"] == "approved" else "answered"
            with st.expander(f"{item['id']} · {topics[item['topic']]} · {loc(language, label)}"):
                st.write(item["question"])
                if item["status"] == "pending" and st.button(loc(language, "moderate"), key=f"approve_{item['id']}"):
                    item["status"] = "approved"
                    _notify("n_moderated", item["id"])
                    st.rerun()
                elif item["status"] == "approved" and st.button(loc(language, "demo_answer"), key=f"answer_{item['id']}"):
                    item["status"] = "answered"
                    _notify("n_answer", item["id"])
                    st.rerun()
                elif item["status"] == "answered":
                    st.markdown("**" + loc(language, "reply") + "**")
                    st.write(loc(language, "sample_community_answer"))
    st.caption(loc(language, "security"))
    invite_panel(language)


def render_inbox(language, go_page):
    _init()
    st.title(f"✉️ {loc(language, 'all_messages')}")
    _banner(language)
    tabs = st.tabs([loc(language, "notifications_tab"), loc(language, "support_tab"), loc(language, "community_tab")])
    with tabs[0]:
        for note in st.session_state.beta_alerts:
            st.write(f"🔔 **{_notification_title(language, note)}**")
            st.caption(f"{loc(language, 'demo')} · {note['ref']} · {note['when']}")
            note["read"] = True
        if not st.session_state.beta_alerts:
            st.info(loc(language, "empty"))
    with tabs[1]:
        if not st.session_state.beta_support:
            st.caption(loc(language, "nothing"))
        else:
            for item in st.session_state.beta_support:
                st.write(f"**{item['id']}** · {loc(language, 'status_replied' if item['status'] == 'replied' else 'status_new')}")
                st.caption(item["text"])
        if st.button(loc(language, "go_support"), key="inbox_nav_support"):
            go_page("Human Support")
    with tabs[2]:
        if not st.session_state.beta_questions:
            st.caption(loc(language, "nothing"))
        else:
            for item in st.session_state.beta_questions:
                label = "pending" if item["status"] == "pending" else "approved" if item["status"] == "approved" else "answered"
                st.write(f"**{item['id']}** · {loc(language, label)}")
                st.caption(item["question"])
        if st.button(loc(language, "go_community"), key="inbox_nav_community"):
            go_page("Community")
    st.caption(loc(language, "pilot_caption"))
    invite_panel(language)
