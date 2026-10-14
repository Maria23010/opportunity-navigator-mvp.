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



# Stable room IDs are never translated. Language changes affect labels, not room identity.
ROOM_IDS = ("math", "english", "coding", "study", "admissions", "motivation", "science", "creative")

ROOM_TRANSLATIONS = {
    "ru": {
        "math": ("🧮 Математика", "Олимпиады, задачи и лайфхаки по учёбе", [
            "Ребята, кто тоже иногда застревает на олимпиадных задачах?",
            "Я стараюсь сначала решить простую версию, а уже потом сложную. Это помогает не бросать.",
            "Классная идея! Может, поделимся нашими способами подготовки к контрольной?"],
            "Я тоже учусь решать задачи постепенно. А что помогает вам не сдаваться?"),
        "english": ("🌎 Английский язык", "Разговорная практика, слова и экзамены", [
            "Я стесняюсь разговаривать на английском, даже когда знаю слова.",
            "У меня так же было! Мне помогло тренироваться по пять минут с простыми фразами.",
            "А кто-нибудь пробовал смотреть сериалы с английскими субтитрами?"],
            "Я пробую понемногу каждый день. Может, поделимся любимыми способами практики?"),
        "coding": ("💻 Программирование", "Python, сайты, игры и первые проекты", [
            "Кто-то сейчас делает свой первый проект на Python?",
            "Я делаю маленькую викторину. Очень радуюсь, когда код наконец запускается!",
            "Мне помогает сохранять каждую рабочую версию и не бояться ошибок."],
            "Здорово, что у каждого свой проект! Расскажите, что вы пробуете создать."),
        "study": ("📚 Учёба и привычки", "Домашние задания, организация времени, мотивация", [
            "У кого тоже бывает, что заданий много и непонятно, с чего начинать?",
            "Я сначала записываю три главные задачи, а потом делаю короткий перерыв.",
            "Мне нравится учиться вместе по расписанию, даже если мы занимаемся разными предметами."],
            "Я тоже составляю небольшой план. А как вы организуете своё время?"),
        "admissions": ("🎓 Университеты и гранты", "Мечты, планы поступления и личный опыт подготовки", [
            "Кто-нибудь уже выбирает страну, где хотел бы учиться?",
            "Я пока сравниваю программы и требования — оказалось, они очень разные.",
            "Мне интересно, как вы решаете, какой университет подходит именно вам."],
            "Я тоже изучаю варианты. Было бы здорово обменяться полезными источниками!"),
        "motivation": ("💛 Поддержка и мотивация", "Добрые слова, маленькие победы и взаимная поддержка", [
            "Сегодня мне удалось сделать то, что я долго откладывал. Даже немного горжусь!",
            "Это здорово! У меня сегодня получилась задача, над которой я сидела два дня.",
            "Давайте делиться хотя бы одной небольшой победой за неделю."],
            "Спасибо за поддержку! Напишите о своей маленькой победе — это вдохновляет."),
        "science": ("🔬 Наука и открытия", "Эксперименты, физика, биология и интересные факты", [
            "Какое научное открытие удивило вас за последнее время?",
            "Я недавно узнал, как космические аппараты используют гравитацию для разгона.",
            "А меня больше всего увлекают эксперименты по биологии!"],
            "Мне интересно узнать, что вас вдохновляет в науке."),
        "creative": ("🎨 Творчество и идеи", "Рисование, музыка, тексты, кино и проекты", [
            "Иногда мне сложно показывать другим свои рисунки.",
            "Я тоже переживала. Мне помогло начать с маленьких работ и добрых отзывов.",
            "Давайте поделимся идеями для проектов, которые можно сделать за выходные!"],
            "Мне нравится, что у всех разные идеи. Чем вы сейчас увлекаетесь?"),
    },
    "en": {
        "math": ("🧮 Mathematics", "Olympiads, problem solving and study tips", ["Does anyone else get stuck on math olympiad problems?", "I start with a simpler version of the problem before trying the hard one.", "Great idea! Should we share how we prepare for tests?"], "I'm learning to solve problems step by step, too. What keeps you motivated?"),
        "english": ("🌎 English", "Speaking, vocabulary and exams", ["I'm nervous speaking English even when I know the words.", "Same here! Five minutes of simple practice helped me.", "Has anyone tried watching shows with English subtitles?"], "A little daily practice works for me. What do you like?"),
        "coding": ("💻 Coding", "Python, websites, games and beginner projects", ["Is anyone building their first Python project?", "I'm making a small quiz; it's so satisfying when my code works!", "Saving small working versions helps me handle bugs."], "It's fun to see everyone's projects. What are you making?"),
        "study": ("📚 Study habits", "Homework, time management and routines", ["Sometimes I have so much homework I don't know where to start.", "I write down my top three tasks and then take a short break.", "I like shared study time even if everyone studies different things."], "I also make short plans. What works for you?"),
        "admissions": ("🎓 Universities and scholarships", "Goals, admissions plans and experiences", ["Is anyone choosing which country they'd like to study in?", "I'm comparing courses and requirements; they're really different.", "How do you decide which university is right for you?"], "I'm researching options too. Let's exchange useful sources!"),
        "motivation": ("💛 Encouragement", "Small wins, kindness and peer support", ["Today I finally did something I'd been putting off!", "Well done! I solved a problem I'd been working on for two days.", "Let's each share one small win this week."], "Thanks for the encouragement. Tell us about a small win!"),
        "science": ("🔬 Science", "Experiments, physics, biology and discoveries", ["What's a science fact that surprised you recently?", "I learned how probes use gravity to gain speed.", "I love biology experiments!"], "What inspires you about science?"),
        "creative": ("🎨 Art and creativity", "Drawing, music, writing and projects", ["I sometimes feel shy sharing my drawings.", "I felt the same; starting with small projects helped.", "Let's trade ideas for fun weekend projects!"], "Everyone has different ideas. What are you working on?"),
    },
    "ar": {
        "math": ("🧮 الرياضيات", "الأولمبياد والمسائل ونصائح الدراسة", ["هل يجد أحدكم مسائل أولمبياد الرياضيات صعبة أحياناً؟", "أبدأ بمسألة أبسط ثم أنتقل إلى الأصعب.", "فكرة جميلة! ما طرقكم للتحضير للاختبارات؟"], "أتعلم حل المسائل خطوة خطوة أيضاً. ما الذي يشجعكم؟"),
        "english": ("🌎 اللغة الإنجليزية", "التحدث والمفردات والاختبارات", ["أخجل من التحدث بالإنجليزية رغم أنني أعرف الكلمات.", "كنت كذلك! ساعدتني خمس دقائق من التدريب يومياً.", "هل جرب أحدكم مشاهدة الأفلام بترجمة إنجليزية؟"], "أحاول التدريب قليلاً كل يوم. ماذا تفضلون؟"),
        "coding": ("💻 البرمجة", "بايثون والمواقع والألعاب والمشاريع", ["هل يعمل أحدكم على أول مشروع بلغة بايثون؟", "أصنع اختباراً صغيراً وأفرح عندما يعمل الكود!", "يساعدني حفظ النسخ التي تعمل قبل تعديلها."], "يسعدني التعرف على مشاريعكم! ماذا تصنعون؟"),
        "study": ("📚 الدراسة وتنظيم الوقت", "الواجبات والعادات وإدارة الوقت", ["أحياناً تكون واجباتي كثيرة ولا أعرف من أين أبدأ.", "أكتب أهم ثلاث مهام ثم أستريح قليلاً.", "أحب أن ندرس في الوقت نفسه حتى لو كانت موادنا مختلفة."], "أنا أيضاً أضع خطة قصيرة. ما طريقتكم؟"),
        "admissions": ("🎓 الجامعات والمنح", "الأهداف وخطط القبول والخبرات", ["هل اختار أحدكم البلد الذي يريد الدراسة فيه؟", "أقارن بين البرامج وشروط القبول؛ إنها مختلفة كثيراً.", "كيف تختارون الجامعة المناسبة لكم؟"], "أنا أبحث أيضاً عن خيارات. لنتبادل المصادر المفيدة!"),
        "motivation": ("💛 التشجيع والدعم", "الإنجازات الصغيرة والتشجيع المتبادل", ["أنجزت اليوم شيئاً كنت أؤجله منذ فترة!", "رائع! نجحت في حل مسألة بعد محاولات كثيرة.", "فلنشارك إنجازاً صغيراً هذا الأسبوع."], "شكراً للتشجيع! شاركونا إنجازاً صغيراً."),
        "science": ("🔬 العلوم", "التجارب والفيزياء والأحياء والاكتشافات", ["ما حقيقة علمية أدهشتكم مؤخراً؟", "تعلمت كيف تستفيد المركبات الفضائية من الجاذبية لزيادة سرعتها.", "أنا أحب تجارب الأحياء!"], "ما أكثر شيء يلهمكم في العلوم؟"),
        "creative": ("🎨 الفن والإبداع", "الرسم والموسيقى والكتابة والمشاريع", ["أخجل أحياناً من عرض رسوماتي على الآخرين.", "كنت كذلك، وبدأت بمشاريع صغيرة.", "فلنتبادل أفكاراً لمشاريع نهاية الأسبوع!"], "لكل شخص أفكار جميلة. ماذا تصنعون الآن؟"),
    },
    "kk": {
        "math": ("🧮 Математика", "Олимпиадалар, есептер және оқу кеңестері", ["Олимпиада есептері сіздерге де кейде қиын бола ма?", "Мен алдымен жеңілдеу нұсқасын шешемін.", "Жақсы ой! Бақылауға қалай дайындалатынымызды бөлісейік."], "Мен де біртіндеп үйреніп жүрмін. Сізге не көмектеседі?"),
        "english": ("🌎 Ағылшын тілі", "Сөйлеу, сөздік және емтихан", ["Ағылшынша сөйлеуге ұяламын, сөздерді білсем де.", "Мен де солай болдым. Күніне бес минут жаттығу көмектесті.", "Ағылшынша субтитрмен фильм көріп жүрсіздер ме?"], "Күнде аздап жаттығамын. Ал сіз ше?"),
        "coding": ("💻 Бағдарламалау", "Python, сайттар, ойындар және алғашқы жобалар", ["Алғашқы Python жобасын жасап жатқандар бар ма?", "Мен шағын викторина жасап жатырмын, код жұмыс істесе қуанамын!", "Қателерден қорықпауға жұмыс істейтін нұсқаларды сақтау көмектеседі."], "Керемет! Қандай жобамен айналысып жүрсіздер?"),
        "study": ("📚 Оқу және уақыт", "Үй тапсырмасы мен оқу әдеттері", ["Үй тапсырмасы көп кезде неден бастарымды білмеймін.", "Мен ең маңызды үш істі жазып аламын.", "Бәріміз әртүрлі пән оқысақ та, бірге оқу уақыты көмектеседі."], "Мен де шағын жоспар құрамын. Сіздің тәсіліңіз қандай?"),
        "admissions": ("🎓 Университеттер мен гранттар", "Мақсаттар және түсуге дайындық", ["Қай елде оқығысы келетінін таңдағандар бар ма?", "Мен бағдарламалар мен талаптарды салыстырып жүрмін.", "Өзіңізге лайықты университетті қалай таңдайсыз?"], "Мен де ізденіп жүрмін. Пайдалы дереккөздермен бөлісейік!"),
        "motivation": ("💛 Қолдау және шабыт", "Кішкентай жеңістер мен бір-бірін қолдау", ["Бүгін көптен кейінге қалдырған ісімді бітірдім!", "Жарайсың! Мен де екі күнде бір есепті шештім.", "Осы аптадағы бір кішкентай жеңісімізді бөлісейік!"], "Қолдауыңызға рақмет! Шағын жеңістеріңізді айтыңыздар."),
        "science": ("🔬 Ғылым", "Тәжірибелер, физика, биология және жаңалықтар", ["Сіздерді соңғы кезде қандай ғылыми жаңалық таңғалдырды?", "Мен ғарыш аппараттарының тартылыс күшін пайдаланатынын білдім.", "Мен биология тәжірибелерін жақсы көремін!"], "Ғылымда сізді не шабыттандырады?"),
        "creative": ("🎨 Өнер және шығармашылық", "Сурет, музыка, мәтін және жобалар", ["Кейде суреттерімді басқаларға көрсетуге ұяламын.", "Мен де солай болдым, шағын жұмыстардан бастадым.", "Демалысқа қандай шығармашылық жобалар ойлап таптыңыздар?"], "Әр адамның идеясы ерекше. Қазір немен айналысасыз?"),
    },
}

ROOM_UI = {
    "ru": {"choose": "Выберите чат по интересам", "back": "← Все чаты", "description": "Здесь общаются не с AI-репетитором: это пример будущих тематических комнат для школьников.",
           "room": "Комната", "age": "Возрастная группа · демо", "age_help": "В прототипе возраст не проверяется. В реальном сервисе понадобится безопасное разделение участников по возрасту.",
           "room_tag": "Тематический чат", "sample_members": "Условные участники · демонстрационный диалог", "you": "Вы · только эта сессия",
           "write": "Написать в чат", "placeholder": "Поделитесь идеей, опытом или поддержкой...", "send": "Отправить в демо-чат", "sent": "Сообщение появилось только в вашей демонстрационной переписке. Другие люди его не получали.",
           "example_button": "Показать пример отклика участника", "sample_reply": "Пример сообщения участника · демо", "reply_title": "В чате «{room}» появилось новое сообщение", "thread": "Переписка", "room_info": "Все участники ниже вымышленные. Здесь можно увидеть пример дружеского общения и написать своё сообщение.",
           "rules": "Обсуждайте учёбу и интересы, уважайте других. Не публикуйте адреса, фамилии, номера телефонов, ссылки на свои аккаунты или другие личные данные.",
           "not_published": "Возможность настоящего общения школьников появится только после подключения проверенных аккаунтов, модерации и жалоб.",
           "saved_posts": "Ваши демо-сообщения в комнатах", "open_room": "Открыть чат", "empty_room": "Пока вы не написали ни одного сообщения в демонстрационные комнаты.",
           "past_questions": "Старые демо-вопросы (архив)", "bad": "Напишите сообщение от 2 до 350 символов без личных контактов и ссылок.", "refresh_note": "История хранится только в этой сессии и может пропасть после её завершения.",
           "reply_prompt": "Нажмите кнопку ниже, чтобы увидеть заранее подготовленный пример отклика. Он не создаётся другим пользователем."},
    "en": {"choose": "Choose an interest-based chat", "back": "← All chats", "description": "Not another AI tutor: these rooms show how students could talk to peers in a future moderated community.",
           "room": "Room", "age": "Age group · demo", "age_help": "Age is not verified in this prototype. Real rooms would require age-appropriate access safeguards.",
           "room_tag": "Interest-based chat", "sample_members": "Fictional peers · sample conversation", "you": "You · this session only",
           "write": "Message the room", "placeholder": "Share an idea, experience or encouragement...", "send": "Send to demo chat", "sent": "Only added to your demonstration. No other person received it.",
           "example_button": "Show a sample peer reply", "sample_reply": "Sample peer response · demo", "reply_title": "New message in “{room}”", "thread": "Conversation", "room_info": "All peers shown below are fictional. Explore a friendly conversation and write your own message.",
           "rules": "Be kind and discuss studies or interests. Do not share names, addresses, phone numbers, profile links or other personal information.",
           "not_published": "Real student-to-student conversations will need verified accounts, moderation and reporting tools.",
           "saved_posts": "Your room demo messages", "open_room": "Open room", "empty_room": "You haven't written in the demo rooms yet.",
           "past_questions": "Old demo questions (archive)", "bad": "Write 2–350 characters without contact details or links.", "refresh_note": "Messages only stay in this session and can disappear when the session ends.",
           "reply_prompt": "Click below for a scripted sample response. It is not generated by another user."},
    "ar": {"choose": "اختر غرفة دردشة حسب اهتماماتك", "back": "← جميع الغرف", "description": "هذه الغرف ليست مدرساً بالذكاء الاصطناعي بل تصور لمجتمع آمن بين الطلاب في المستقبل.",
           "room": "الغرفة", "age": "الفئة العمرية · تجريبي", "age_help": "لا يتم التحقق من العمر في هذا النموذج. سيتطلب التواصل الحقيقي إجراءات حماية ملائمة للعمر.",
           "room_tag": "دردشة حسب الاهتمامات", "sample_members": "مشاركون خياليون · محادثة توضيحية", "you": "أنت · في هذه الجلسة فقط",
           "write": "اكتب في الغرفة", "placeholder": "شارك فكرة أو تجربة أو كلمات تشجيع...", "send": "إرسال في الدردشة التجريبية", "sent": "أضيفت الرسالة إلى العرض التجريبي فقط، ولم يتلقها أي شخص آخر.",
           "example_button": "عرض رد توضيحي من مشارك", "sample_reply": "رد مشارك نموذجي · تجريبي", "reply_title": "رسالة جديدة في غرفة «{room}»", "thread": "المحادثة", "room_info": "جميع المشاركين أدناه خياليون. يمكنك تجربة حوار ودّي وكتابة رسالة.",
           "rules": "احترم الآخرين وناقش الدراسة والاهتمامات. لا تنشر بياناتك الشخصية أو روابط حساباتك.",
           "not_published": "تتطلب المحادثات الحقيقية حسابات موثقة وإشرافاً وإمكانية الإبلاغ.",
           "saved_posts": "رسائلك في الغرف التجريبية", "open_room": "فتح الغرفة", "empty_room": "لم تكتب رسائل في الغرف التجريبية بعد.",
           "past_questions": "الأسئلة التجريبية القديمة (الأرشيف)", "bad": "اكتب رسالة من حرفين إلى 350 حرفاً دون بيانات اتصال أو روابط.", "refresh_note": "الرسائل محفوظة في هذه الجلسة فقط وقد تختفي عند انتهائها.",
           "reply_prompt": "اضغط لعرض رد مكتوب مسبقاً، وليس رسالة من شخص حقيقي."},
    "kk": {"choose": "Қызығушылық бойынша чатты таңдаңыз", "back": "← Барлық чаттар", "description": "Бұл AI-репетитор емес: болашақта оқушылар бір-бірімен сөйлесе алатын тақырыптық бөлмелердің үлгісі.",
           "room": "Бөлме", "age": "Жас тобы · демо", "age_help": "Бұл прототипте жас тексерілмейді. Нақты қызметте жас бойынша қауіпсіздік тексеруі қажет.",
           "room_tag": "Тақырыптық чат", "sample_members": "Ойдан шығарылған қатысушылар · үлгі әңгіме", "you": "Сіз · тек осы сессия",
           "write": "Чатқа жазу", "placeholder": "Ойыңызды, тәжірибеңізді не қолдауыңызды бөлісіңіз...", "send": "Демо-чатқа жіберу", "sent": "Хабарлама тек осы демода қосылды. Оны басқа адам алған жоқ.",
           "example_button": "Қатысушы жауабының үлгісін көру", "sample_reply": "Қатысушының үлгі жауабы · демо", "reply_title": "«{room}» чатында жаңа хабарлама", "thread": "Әңгіме", "room_info": "Төмендегі қатысушылардың барлығы ойдан шығарылған. Әңгіме үлгісін көріп, өз хабарламаңызды жазыңыз.",
           "rules": "Басқаларды құрметтеңіз. Жеке деректерді, мекенжайды, телефонды және аккаунт сілтемелерін жазбаңыз.",
           "not_published": "Нақты оқушылармен сөйлесу үшін тексерілген аккаунттар, модерация және шағым беру мүмкіндігі қажет.",
           "saved_posts": "Бөлмелердегі демо-хабарламаларыңыз", "open_room": "Чатты ашу", "empty_room": "Әзірге демо-бөлмелерге хабарлама жазбадыңыз.",
           "past_questions": "Бұрынғы демо-сұрақтар (мұрағат)", "bad": "Байланыс деректері мен сілтемелерсіз 2–350 таңба жазыңыз.", "refresh_note": "Хабарламалар тек осы сессияда сақталады және кейін жоғалуы мүмкін.",
           "reply_prompt": "Басқа адам жібермеген дайын үлгі жауапты көру үшін басыңыз."},
}


def room_language(language):
    return language if language in ROOM_TRANSLATIONS else "en"


def room_text(language, key):
    lang = room_language(language)
    return ROOM_UI[lang].get(key, ROOM_UI["en"].get(key, key))


def room_info(language, room_id):
    return ROOM_TRANSLATIONS[room_language(language)][room_id]


def room_name(language, room_id):
    return room_info(language, room_id)[0]


def room_post_key(room_id, age):
    return f"{room_id}:{age}"


def safe_chat_message(text):
    # This is only a local demo guard. Never substitute it for live human moderation.
    if not 2 <= len(text.strip()) <= 350:
        return False
    return not _invalid("Demo message: " + text.strip())


def _init():
    for key, value in {
        "beta_support": [], "beta_questions": [], "beta_alerts": [],
        "beta_access": False, "beta_room_posts": {}, "beta_room_selection": None, "beta_room_age": "15–17",
    }.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (list, dict)) else value


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
    if code == "n_room_reply":
        rid = note.get("ref", "")
        if rid in ROOM_IDS:
            name = room_name(language, rid)
            return room_text(language, "reply_title").format(room=name)
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
    """Topic-based sample chat rooms; strictly session-local, no cross-user contact."""
    _init()
    st.title(f"💬 {loc(language, 'community_title')}")
    _banner(language)
    st.write(room_text(language, "description"))
    st.caption(room_text(language, "not_published"))

    chosen = st.session_state.get("beta_room_selection")
    if chosen not in ROOM_IDS:
        chosen = None
    if chosen is None:
        st.subheader(room_text(language, "choose"))
        cols = st.columns(2)
        for i, room_id in enumerate(ROOM_IDS):
            title, description, _, _ = room_info(language, room_id)
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.caption(description)
                    if st.button(room_text(language, "open_room"),
                                 key=f"beta_open_room_{room_id}",
                                 use_container_width=True):
                        st.session_state.beta_room_selection = room_id
                        st.rerun()
        if st.session_state.beta_questions:
            with st.expander(room_text(language, "past_questions")):
                topics = loc(language, "topics")
                for item in st.session_state.beta_questions:
                    topic_id = int(item.get("topic", 0))
                    title_old = topics[topic_id] if 0 <= topic_id < len(topics) else "—"
                    st.write(f"**{title_old} · {item.get('id', '')}**")
                    st.write(item.get("question", ""))
        invite_panel(language)
        return

    if st.button(room_text(language, "back"), key="beta_room_back"):
        st.session_state.beta_room_selection = None
        st.rerun()
    age = st.selectbox(room_text(language, "age"), ["12–14", "15–17"],
                       key="beta_room_age", help=room_text(language, "age_help"))
    title, description, example_lines, simulated_reply = room_info(language, chosen)
    st.markdown(f"### {title}")
    st.caption(f"{room_text(language, 'room_tag')} · {age} · {description}")
    st.info(room_text(language, "room_info"))
    st.caption(room_text(language, "sample_members"))

    for num, statement in enumerate(example_lines, start=1):
        with st.chat_message("assistant", avatar="💬"):
            participant = {"ru": "Участник", "en": "Participant", "ar": "مشارك", "kk": "Қатысушы"}.get(language, "Participant")
            st.markdown(f"**{loc(language, 'demo')} · {participant}_{100 + num}**")
            st.write(statement)

    saved_key = room_post_key(chosen, age)
    messages = st.session_state.beta_room_posts.get(saved_key, [])
    for post in messages:
        if post["who"] == "you":
            with st.chat_message("user", avatar="🙂"):
                st.caption(room_text(language, "you"))
                st.write(post["text"])
        else:
            with st.chat_message("assistant", avatar="💬"):
                st.caption(room_text(language, "sample_reply"))
                st.write(simulated_reply)

    st.caption(room_text(language, "rules"))
    with st.form(f"beta_chat_form_{chosen}_{age}", clear_on_submit=True):
        message = st.text_input(room_text(language, "write"),
                                placeholder=room_text(language, "placeholder"), max_chars=350)
        submitted = st.form_submit_button(room_text(language, "send"),
                                          type="primary", disabled=not _can_interact())
    if submitted:
        if not safe_chat_message(message):
            st.error(room_text(language, "bad"))
        else:
            st.session_state.beta_room_posts.setdefault(saved_key, []).append({"who": "you", "text": message.strip()})
            st.session_state.beta_room_posts[saved_key] = st.session_state.beta_room_posts[saved_key][-40:]
            st.rerun()

    # Never generate an unsolicited "peer" response to a free-form message.
    # It is explicitly a scripted demo, not a human reply or an AI tutor response.
    if messages and messages[-1]["who"] == "you":
        st.caption(room_text(language, "reply_prompt"))
        if st.button(room_text(language, "example_button"),
                     key=f"beta_chat_scripted_reply_{chosen}_{age}", disabled=not _can_interact()):
            st.session_state.beta_room_posts[saved_key].append({"who": "sample", "text": "scripted"})
            _notify("n_room_reply", chosen)
            st.rerun()
    st.caption(room_text(language, "refresh_note"))

    # Preserve questions from the earlier demo without showing the old question form.
    if st.session_state.beta_questions:
        with st.expander(room_text(language, "past_questions")):
            topics = loc(language, "topics")
            for item in st.session_state.beta_questions:
                topic_id = int(item.get("topic", 0))
                title_old = topics[topic_id] if 0 <= topic_id < len(topics) else "—"
                st.write(f"**{title_old} · {item.get('id', '')}**")
                st.write(item.get("question", ""))
                if item.get("status") == "answered":
                    st.caption(loc(language, "sample_community_answer"))
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
        st.markdown(f"**{room_text(language, 'saved_posts')}**")
        active = []
        for room_id in ROOM_IDS:
            count = sum(sum(1 for post in posts if post.get("who") == "you")
                        for key, posts in st.session_state.beta_room_posts.items()
                        if key.startswith(room_id + ":"))
            if count:
                active.append((room_id, count))
        if not active:
            st.caption(room_text(language, "empty_room"))
        for room_id, count in active:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{room_name(language, room_id)}** · {count}")
            with c2:
                if st.button(room_text(language, "open_room"), key=f"inbox_room_{room_id}"):
                    st.session_state.beta_room_selection = room_id
                    go_page("Community")
        if st.session_state.beta_questions:
            st.markdown(f"**{room_text(language, 'past_questions')}**")
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
