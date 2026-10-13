"""Stable catalog localization: internal identifiers stay independent of display labels.

Arabic/English labels are available offline. Other interface languages use the
existing cached translation service, which may be unavailable without a network.
"""
COUNTRY_EN = {
'AU':'Australia','AZ':'Azerbaijan','BN':'Brunei','GB':'United Kingdom',
'HU':'Hungary','HK':'Hong Kong (China)','IT':'Italy','CA':'Canada','QA':'Qatar',
'CN':'China','RU':'Russia','RO':'Romania','SG':'Singapore','US':'United States',
'TR':'Türkiye','KR':'South Korea','JP':'Japan','AE':'United Arab Emirates','KZ':'Kazakhstan'}
COUNTRY_AR = {
'AU':'أستراليا','AZ':'أذربيجان','BN':'بروناي','GB':'المملكة المتحدة',
'HU':'المجر','HK':'هونغ كونغ (الصين)','IT':'إيطاليا','CA':'كندا','QA':'قطر',
'CN':'الصين','RU':'روسيا','RO':'رومانيا','SG':'سنغافورة','US':'الولايات المتحدة',
'TR':'تركيا','KR':'كوريا الجنوبية','JP':'اليابان','AE':'الإمارات العربية المتحدة','KZ':'كازاخستان'}
FIELD_EN = {
'industrial':'Industrial engineering','mechanical':'Mechanical engineering',
'manufacturing':'Manufacturing and automation','computer':'Computer science and programming',
'data':'Data science and artificial intelligence','electrical':'Electrical and electronic engineering',
'civil':'Civil engineering','architecture':'Architecture','art':'Fine arts','design':'Design',
'media':'Film and media','music':'Music','theatre':'Theatre','economics':'Economics',
'business':'Business and management','finance':'Finance','psychology':'Psychology',
'biology':'Biology','chemistry':'Chemistry','physics':'Physics','math':'Mathematics',
'medicine':'Medicine','nursing':'Nursing','law':'Law','education':'Education',
'history':'History','languages':'Languages and literature',
'politics':'Political science and international relations','environment':'Environmental and Earth sciences',
'engineering':'Engineering — all disciplines','aerospace':'Aviation and aerospace',
'chemical_eng':'Chemical engineering','materials':'Materials science',
'biomedical':'Biomedical engineering','automotive':'Automotive engineering',
'agriculture':'Agriculture','veterinary':'Veterinary medicine','dentistry':'Dentistry',
'pharmacy':'Pharmacy','tourism':'Tourism and hospitality','journalism':'Journalism',
'sociology':'Sociology','social_work':'Social work','philosophy':'Philosophy',
'logistics':'Logistics','statistics':'Statistics'}
FIELD_AR = {
'industrial':'الهندسة الصناعية','mechanical':'الهندسة الميكانيكية',
'manufacturing':'التصنيع والأتمتة','computer':'علوم الحاسوب والبرمجة',
'data':'علوم البيانات والذكاء الاصطناعي','electrical':'الهندسة الكهربائية والإلكترونية',
'civil':'الهندسة المدنية','architecture':'العمارة','art':'الفنون الجميلة','design':'التصميم',
'media':'السينما والإعلام','music':'الموسيقى','theatre':'المسرح','economics':'الاقتصاد',
'business':'إدارة الأعمال','finance':'التمويل','psychology':'علم النفس',
'biology':'علم الأحياء','chemistry':'الكيمياء','physics':'الفيزياء','math':'الرياضيات',
'medicine':'الطب','nursing':'التمريض','law':'القانون','education':'التربية والتعليم',
'history':'التاريخ','languages':'اللغات والآداب',
'politics':'العلوم السياسية والعلاقات الدولية','environment':'البيئة وعلوم الأرض',
'engineering':'الهندسة — جميع التخصصات','aerospace':'الطيران والفضاء',
'chemical_eng':'الهندسة الكيميائية','materials':'علم المواد',
'biomedical':'الهندسة الطبية الحيوية','automotive':'هندسة السيارات',
'agriculture':'الزراعة','veterinary':'الطب البيطري','dentistry':'طب الأسنان',
'pharmacy':'الصيدلة','tourism':'السياحة والضيافة','journalism':'الصحافة',
'sociology':'علم الاجتماع','social_work':'الخدمة الاجتماعية','philosophy':'الفلسفة',
'logistics':'الخدمات اللوجستية','statistics':'الإحصاء'}
# Russian source text -> English, Arabic display text. Stable/cached offline for UI.
LABELS = {
'Университеты и гранты':('Universities and scholarships','الجامعات والمنح الدراسية'),
'Первая степень после школы: университет, программа и условия финансирования.':('First degree after school: university, program and financial aid.','المرحلة الجامعية الأولى بعد المدرسة: الجامعة والبرنامج والتمويل.'),
'Подтверждённое существование гранта не гарантирует его получение. Условия зависят от гражданства, аттестата, специальности и года поступления.':('A scholarship being available does not guarantee an award. Eligibility depends on citizenship, qualifications, program and intake year.','وجود منحة لا يضمن الحصول عليها. تعتمد الشروط على الجنسية والشهادة والتخصص وسنة القبول.'),
'Страна или территория обучения':('Country or territory of study','بلد أو منطقة الدراسة'),
'Все страны в базе':('All countries in the database','جميع البلدان في قاعدة البيانات'),
'Направление бакалавриата':('Bachelor’s degree field','تخصص البكالوريوس'),
'Все направления':('All fields','جميع التخصصات'),
'Или уточните направление / название вуза (необязательно)':('Or specify a field / university name (optional)','أو أدخل التخصص أو اسم الجامعة (اختياري)'),
'Например: промышленная инженерия, искусство, Bilkent':('For example: industrial engineering, arts, Bilkent','مثال: الهندسة الصناعية، الفنون، Bilkent'),
'Ручной запрос имеет приоритет над выбранным направлением.':('Your typed search takes priority over the selected field.','البحث المكتوب له الأولوية على التخصص المحدد.'),
'Это не число подтверждённых мест на набор 2027 года.':('This is not the number of available places for the 2027 intake.','هذا ليس عدد المقاعد المؤكدة للقبول عام 2027.'),
'Поступление в выбранную страну: документы, экзамены и гранты':('Admissions in this country: documents, exams and scholarships','القبول في هذا البلد: المستندات والاختبارات والمنح'),
'Пути поступления:':('Admission routes:','مسارات القبول:'),
'Документы:':('Documents:','المستندات:'),
'Экзамены:':('Exams:','الاختبارات:'),
'Гранты:':('Scholarships:','المنح:'),
'Покрытие расходов':('Financial coverage','تغطية التكاليف'),
'Все университеты (включая без подтверждённого гранта)':('All universities (including those without a confirmed scholarship)','جميع الجامعات (بما فيها التي لا توجد لها منحة مؤكدة)'),
'Гранты на основные расходы / помощь по нуждаемости':('Scholarships for major expenses / need-based aid','منح تغطي النفقات الأساسية / دعم حسب الحاجة المالية'),
'Тип записи':('Result type','نوع النتيجة'),
'Всё':('All','الكل'),
'Университеты':('Universities','الجامعات'),
'Колледжи с бакалаврскими программами':('Colleges offering bachelor’s degrees','الكليات التي تقدم برامج البكالوريوس'),
'Государственные программы':('Government programs','البرامج الحكومية'),
'Сначала показываем точное направление, затем смежные программы с отдельной отметкой. Новые записи без проверки программы отмечены особо.':('Exact matches appear first, followed by separately marked related fields. New unverified programs are marked.','تظهر التخصصات المطابقة أولاً، ثم التخصصات القريبة مع تمييزها. وتُميز البرامج غير المتحقق منها.'),
'Подобрать университеты':('Find universities','البحث عن الجامعات'),
'Укажите параметры и нажмите «Подобрать университеты».':('Choose your filters and click “Find universities”.','حدد خيارات البحث ثم اضغط «البحث عن الجامعات».'),
'Поиск также по переводу:':('Also searching translated query:','البحث باستخدام الترجمة أيضاً:'),
'Возможно, вы имели в виду:':('Did you mean:','هل تقصد:'),
'Исправьте запрос и повторите поиск.':('Edit the query and search again.','عدّل البحث وحاول مرة أخرى.'),
'По этому запросу пока нет подходящих программ в выбранной стране и при данных фильтрах. Мы не подставляем несоответствующий курс ради заполнения результата.':('No matching programs for this country and filters yet. We do not substitute unrelated degrees.','لا توجد برامج مطابقة لهذا البلد وخيارات البحث حتى الآن. لن نعرض برامج غير مناسبة لمجرد ملء النتائج.'),
'Где это направление есть в других странах (проверить правила приёма)':('Other countries offering this field (verify admissions requirements)','بلدان أخرى يتوفر فيها هذا التخصص (تحقق من شروط القبول)'),
'Эти вузы не находятся в выбранной стране. Для поиска по ним смените страну в фильтре.':('These universities are outside your chosen country. Change the country filter to explore them.','هذه الجامعات خارج البلد المختار. غيّر البلد للاطلاع عليها.'),
'Ниже также есть смежные направления. Они отмечены отдельно и могут отличаться учебным планом.':('Related fields are also included below, marked separately. Their curricula may differ.','تظهر أيضاً تخصصات قريبة أدناه مع تمييزها، وقد تختلف خططها الدراسية.'),
'Найдено:':('Found:','النتائج:'),
'точных/по названию:':('exact/name matches:','مطابق أو بحسب الاسم:'),
'смежных:':('related:','تخصصات قريبة:'),
'1. Выберите университет':('1. Choose a university','١. اختر الجامعة'),
'Предварительный вариант: название программы, набор 2027 года и требования надо подтвердить у вуза.':('Preliminary match: confirm degree, 2027 intake and requirements with the university.','نتيجة أولية: يرجى التحقق من البرنامج والقبول لعام 2027 والشروط لدى الجامعة.'),
'Смежное направление:':('Related field:','تخصص قريب:'),
'Совпадение по названию вуза:':('University name match:','تطابق اسم الجامعة:'),
'Подходящие программы:':('Matching programs:','البرامج المناسبة:'),
'Вариант из базы по выбранной стране и типу финансирования.':('Result from the database for your chosen country and aid type.','نتيجة من قاعدة البيانات للبلد ونوع التمويل المختارين.'),
'Посмотреть требования':('View requirements','عرض شروط القبول'),
'2. Требования выбранного вуза':('2. University admission requirements','٢. شروط القبول في الجامعة'),
'Вы выбрали смежное направление. Сравните учебный план с вашим первоначальным запросом.':('You selected a related field. Compare its curriculum with your original goal.','لقد اخترت تخصصاً قريباً. قارن خطته الدراسية بهدفك الأصلي.'),
'Данные добавлены для поиска университетов. Точная программа бакалавриата, наличие мест и правила набора 2027 года ещё требуют официальной проверки.':('This entry is for discovery. The exact degree, vacancies and 2027 requirements need official verification.','أُضيفت هذه النتيجة للاستكشاف، ويجب التحقق رسمياً من البرنامج والمقاعد وشروط 2027.'),
'Показать и другие программы университета':('Show other university programs','عرض برامج أخرى في الجامعة'),
'Программа — требования могут отличаться':('Program — requirements can differ','البرنامج — قد تختلف الشروط'),
'Цикл в источнике / статус проверки:':('Intake cycle / verification status:','دورة القبول / حالة التحقق:'),
'Выбранная программа:':('Selected program:','البرنامج المختار:'),
'язык:':('language:','لغة الدراسة:'),
'Открыть официальный каталог / источник программы':('Open official degree page / source','فتح صفحة البرنامج الرسمية / المصدر'),
'Это общая карточка. Подробные требования отдельных специальностей ещё не внесены.':('This is a general profile. Program-specific requirements are not yet available.','هذه معلومات عامة، ولم تُضف بعد شروط القبول الخاصة بكل برنامج.'),
'Экзамены и оценки':('Exams and grades','الاختبارات والدرجات'),
'Грант и расходы':('Scholarships and costs','المنح والتكاليف'),
'Сроки и источники':('Deadlines and sources','المواعيد والمصادر'),
'Школьные оценки / GPA':('School grades / GPA','الدرجات المدرسية / المعدل'),
'Экзамены и минимальные баллы':('Exams and minimum scores','الاختبارات والحد الأدنى للدرجات'),
'Баллы относятся только к указанному маршруту, году и виду теста. Минимум для подачи не равен конкурсному проходному баллу. «ИЛИ» означает альтернативу, а не сумму экзаменов.':('Scores apply only to the specified route, cycle and test. Minimum eligibility is not the final competitive cutoff. “OR” means a permitted alternative.','تخص الدرجات مسار القبول والسنة ونوع الاختبار المحدد. الحد الأدنى ليس درجة القبول التنافسية النهائية. «أو» تعني خياراً بديلاً.'),
'Для этой программы численные пороги пока не подтверждены. Вместо вымышленного балла показаны известные предметы и условия.':('Numeric minimum scores have not yet been verified. Known subjects and requirements are shown instead of inventing scores.','لم يتم التحقق من الحد الأدنى الرقمي لهذه الدراسة. نعرض المواد والشروط المعروفة بدلاً من افتراض درجات.'),
'Экзамены ещё не проверены. Пустой список не означает, что сдавать ничего не нужно.':('Exams not verified. An empty list does not mean no tests are required.','لم يتم التحقق من الاختبارات. القائمة الفارغة لا تعني عدم وجود اختبارات مطلوبة.'),
'Кому доступен этот вариант':('Who is eligible','من يحق له التقديم'),
'Что ещё нужно уточнить':('What still needs verification','ما الذي يحتاج إلى تحقق'),
'Оценки для конкурса гранта:':('Grades for scholarship selection:','الدرجات المطلوبة للمنافسة على المنحة:'),
'Поступление и получение гранта — отдельные решения. Финансирование нужно подтвердить письмом о присуждении.':('Admission and scholarship awards are separate decisions. Funding must be confirmed in an award letter.','القبول والمنحة قراران منفصلان. يجب تأكيد التمويل بخطاب رسمي.'),
'Сохранение гранта после поступления':('Keeping the scholarship after admission','شروط استمرار المنحة بعد القبول'),
'Сроки нужного набора пока не подтверждены в базе.':('Deadlines for this intake are not yet verified.','لم يتم التحقق من مواعيد التقديم لهذه الدورة.'),
'Прошедшие даты не переносятся на следующий год автоматически. Проверяйте срок и часовой пояс у организатора.':('Past deadlines do not roll forward automatically. Verify the deadline and time zone with the university.','المواعيد السابقة لا تنتقل تلقائياً إلى العام التالي. تحقق من الموعد والمنطقة الزمنية لدى الجامعة.'),
'Ограниченная проверка:':('Limited verification:','تحقق محدود:'),
'Скачать карточку с требованиями':('Download requirements report','تنزيل تقرير شروط القبول'),
'Охват базы и обновление':('Database coverage and updates','تغطية قاعدة البيانات والتحديثات'),
'Если страны нет в списке, она ещё не проверена. Это не вывод об отсутствии финансирования.':('A missing country has not yet been reviewed; this does not mean there is no funding.','إذا لم يظهر بلد، فلم تتم مراجعته بعد، ولا يعني ذلك عدم وجود تمويل.'),
'Скачать всю базу JSON':('Download full JSON database','تنزيل قاعدة البيانات الكاملة JSON'),
'Обязателен':('Required','إلزامي'),'Один из перечисленных':('Choose one','اختر واحداً'),
'Допустимая альтернатива':('Alternative','بديل مقبول'),'Необязателен':('Optional','اختياري'),
'При указанных условиях':('Conditional','حسب الشروط'),'Альтернатива при условиях':('Conditional alternative','بديل مشروط'),
'Рекомендован':('Recommended','موصى به'),'Ориентир, не минимум':('Reference, not minimum','للاسترشاد وليس الحد الأدنى'),
'Не указан / см. условия':('Not stated / see conditions','غير محدد / انظر الشروط'),
'шкала:':('scale:','المقياس:'),
'Экзамен':('Exam','الاختبار'),'Статус':('Status','الحالة'),'Балл':('Score','الدرجة'),'Условия':('Conditions','الشروط'),
'срок прошёл':('deadline passed','انتهى الموعد'),'сегодня — проверить время':('today — check time','اليوم — تحقق من التوقيت'),
'предстоящий срок':('upcoming deadline','موعد قادم'),
'Ошибка загрузки базы университетов.':('University database loading error.','خطأ أثناء تحميل بيانات الجامعات.'),
'Подробности ошибки':('Error details','تفاصيل الخطأ'),
'Программа:':('Program:','البرنامج:'),'Цикл:':('Intake:','الدورة:'),'Проверено:':('Checked:','تم التحقق:'),
'Оценки:':('Grades:','الدرجات:'),'Уточнить:':('Verify:','يحتاج للتحقق:'),'Источники:':('Sources:','المصادر:'),
'Сохранение гранта:':('Scholarship renewal:','استمرار المنحة:'),'Сроки:':('Deadlines:','المواعيد:'),
'не подтверждены':('not verified','غير مؤكدة'),
}

LABELS.update({
'Не удалось прочитать базу университетов. Загрузите universities_catalog.json в ту же папку GitHub, где находится app.py.':('Unable to load universities database. Place universities_catalog.json next to app.py on GitHub.','تعذّر تحميل قاعدة بيانات الجامعات. ضع ملف universities_catalog.json بجوار app.py في GitHub.'),
'Например: промышленная инженерия, искусство, Bilkent':('Example: industrial engineering, arts, Bilkent','مثال: الهندسة الصناعية، الفنون، Bilkent'),
})

def country_label(code, base, lang, translate):
    if lang == 'ru': return base
    if lang == 'en': return COUNTRY_EN.get(code, base)
    if lang == 'ar': return COUNTRY_AR.get(code, base)
    return translate(COUNTRY_EN.get(code, base), lang)

def field_label(code, base, lang, translate):
    if lang == 'ru': return base
    if lang == 'en': return FIELD_EN.get(code, base)
    if lang == 'ar': return FIELD_AR.get(code, base)
    return translate(FIELD_EN.get(code, base), lang)

def label(ru, lang, translate):
    if lang == 'ru': return ru
    en, ar = LABELS.get(ru, (ru, ru))
    if lang == 'en': return en
    if lang == 'ar': return ar if ru in LABELS else translate(en, lang)
    return translate(en, lang)

# Frequently recurring admissions notices: keep Arabic usable offline when the
# automatic translation provider is blocked or rate limited.
DATA_AR = {
'Финансирование не проверено для выбранной программы':'لم يتم التحقق من التمويل لهذا البرنامج.',
'Финансирование не подтверждено — проверьте официальный сайт':'التمويل غير مؤكد — تحقق من الموقع الرسمي.',
'Стипендия / покрытие не подтверждены для выбранного направления':'لم يتم تأكيد منحة أو تغطية التكاليف لهذا التخصص.',
'Здесь не подтверждён индивидуальный грант или бесплатное обучение для этого ребёнка.':'لم يتم تأكيد منحة شخصية أو دراسة مجانية لهذا الطالب.',
'Полная стипендия/скидка на обучение для этого направления не подтверждена. Ищите действующие условия грантов на официальном сайте.':'لا توجد منحة كاملة مؤكدة لهذا التخصص. تحقق من المنح المتاحة في الموقع الرسمي.',
'Возможен отдельный конкурс государственных грантов':'قد تتوفر منافسة منفصلة على المنح الحكومية.',
'Победа в грантовом конкурсе не гарантирована, отдельные международные квоты проверяются отдельно.':'الفوز بالمنحة غير مضمون؛ ويجب التحقق من الحصص الدولية بشكل منفصل.',
'Бакалаврские направления по официальному каталогу; точные требования отличаются по программе и категории поступающего.':'تظهر برامج البكالوريوس في الدليل الرسمي، وتختلف شروط القبول بحسب البرنامج وفئة المتقدم.',
'2027 (требует проверки)':'2027 (يتطلب التحقق)',
'Текущая страница; сроки нового набора уточнить':'الصفحة الحالية؛ تحقق من مواعيد التقديم الجديدة.',
'2026/27; сверить новый цикл':'2026/27؛ تحقق من دورة القبول التالية.',
'Английский':'الإنجليزية',
'Уточнить':'يجب التحقق',
'Зависит от программы':'حسب البرنامج',
'Справочник 2027; сверять год курса в каталоге':'دليل 2027؛ تحقق من سنة البرنامج في دليل الجامعة.',
'Поступление и получение гранта — отдельные решения. Финансирование нужно подтвердить письмом о присуждении.':'القبول والمنحة قراران منفصلان. يجب تأكيد التمويل بخطاب رسمي.',
'Программа найдена в официальном каталоге. Приём 2027 и условия для вашего аттестата проверяются отдельно.':'البرنامج مدرج في الدليل الرسمي. تحقق بشكل منفصل من قبول 2027 وشروط شهادتك.',
'Программы по справочнику 2026/27, дата нового набора уточняется':'البرامج بحسب دليل 2026/27؛ يُرجى التحقق من موعد القبول التالي.',
'2026/27 (данные справочника); проверить правила 2027':'بيانات دليل 2026/27؛ تحقق من شروط 2027.',
'Перечень программ 2026/27 из пользовательского справочника; международный приём и гранты отличаются.':'برامج 2026/27 بحسب الدليل المقدم؛ تختلف شروط قبول الدوليين والمنح.',
'Грант конкурсный. В карточке разделены подтверждённые факты и ещё не внесённые условия.':'المنحة تنافسية. توضح البطاقة المعلومات المتحققة والشروط التي لم تُدرج بعد.',
'Обучение и поддержка основных расходов — конкурсный грант':'منحة تنافسية تغطي الدراسة وبعض النفقات الأساسية',
}


def offline_dynamic(text, lang):
    """Fast no-network translations for repeated catalog notes."""
    if lang == 'ar':
        return DATA_AR.get(text)
    return None
