"""Programme matching. No inference of a degree from a university's name."""
import re
import unicodedata

# Each label is a discipline, not an institution or a promise of funding.
FIELDS = {
 'industrial': ('Промышленная инженерия', 'industrial engineering|industrial and systems engineering|промышленной инженерии|индустриальной инженерии|өндірістік инженерия|промышленная инженерия|промышленную инженерию|индустриальная инженерия|инженерия производства|endüstri mühendisliği|өнеркәсіптік инженерия|sanoat muhandisligi|ingeniería industrial|génie industriel|wirtschaftsingenieurwesen|الهندسة الصناعية|工业工程'),
 'mechanical': ('Машиностроение', 'mechanical engineering|механической инженерии|машиностроение|машиностроения|механическая инженерия|makine mühendisliği|машина жасау|ingeniería mecánica|génie mécanique|maschinenbau|الهندسة الميكانيكية|机械工程'),
 'manufacturing': ('Производство и автоматизация', 'manufacturing engineering|automation engineering|engineering management|systems engineering|ingegneria gestionale|управление производством|автоматизация производства|производственная инженерия|мехатроника|mechatronics|автоматизация|mechatronik|自动化'),
 'computer': ('Информатика и программирование', 'computer science|computer engineering|информатику|информатики|программирования|bilgisayar bilimi|software engineering|computing|информатика|программирование|программная инженерия|компьютерная инженерия|компьютерные науки|it|informatique|informatik|informática|bilgisayar mühendisliği|kompyuter fanlari|компьютерлік ғылымдар|علوم الحاسوب|计算机科学'),
 'data': ('Данные и искусственный интеллект', 'data science|artificial intelligence|наука о данных|искусственный интеллект|машинное обучение|ai|yapay zeka|жасанды интеллект|suniy intellekt|inteligencia artificial|intelligence artificielle|künstliche intelligenz|الذكاء الاصطناعي|人工智能'),
 'electrical': ('Электротехника и электроника', 'electrical engineering|electrical and electronic engineering|electrical and electronics engineering|электротехника|электроника|elektrik elektronik mühendisliği|electrotechnique|电气工程'),
 'civil': ('Строительство', 'civil engineering|строительство|строительная инженерия|inşaat mühendisliği|құрылыс|ingeniería civil|génie civil|الهندسة المدنية|土木工程'),
 'architecture': ('Архитектура', 'architecture|архитектура|mimarlık|сәулет|arquitectura|architektur|الهندسة المعمارية|建筑学'),
 'art': ('Изобразительное искусство', 'art|arts|исскуство|изобразительного искусства|fine art|fine arts|visual arts|studio art|painting|искусство|искусства|изобразительное искусство|живопись|рисование|sanat|resim|өнер|sanatshunoslik|arte|beaux arts|kunst|الفنون|艺术'),
 'design': ('Дизайн', 'design|graphic design|visual communication design|industrial design|дизайн|графический дизайн|промышленный дизайн|tasarım|diseño|التصميم|设计'),
 'media': ('Кино и медиа', 'media and visual arts|film and media studies|cinema|film|медиа|кино|кинематография|медиакоммуникации|sinema|电影'),
 'music': ('Музыка', 'music|музыка|музыки|müzik|música|musique|musik|музыка|الموسيقى|音乐'),
 'theatre': ('Театр', 'theater|theatre|театр|актерское искусство|актёрское искусство|tiyatro|teatro|théâtre|المسرح|戏剧'),
 'economics': ('Экономика', 'economics|экономика|экономики|iktisat|ekonomi|economía|économie|wirtschaft|الاقتصاد|经济学'),
 'business': ('Бизнес и менеджмент', 'business administration|business|management|бизнес|менеджмент|управление|işletme|бизнесті басқару|negocios|gestion|إدارة الأعمال|工商管理'),
 'finance': ('Финансы', 'finance|финансы|финансов|қаржы|finans|finanzas|التمويل|金融'),
 'psychology': ('Психология', 'psychology|психология|психологии|psikoloji|psicología|psychologie|علم النفس|心理学'),
 'biology': ('Биология', 'biology|biological sciences|биология|биологии|biyoloji|biología|biologie|علم الأحياء|生物学'),
 'chemistry': ('Химия', 'chemistry|химия|химии|kimya|química|chimie|chemie|الكيمياء|化学'),
 'physics': ('Физика', 'physics|физика|физики|fizik|física|physique|physik|الفيزياء|物理学'),
 'math': ('Математика', 'mathematics|math|applied mathematics|математика|математики|прикладная математика|matematik|matemáticas|mathématiques|mathematik|الرياضيات|数学'),
 'medicine': ('Медицина', 'medicine|general medicine|медицина|лечебное дело|tıp|medicina|médecine|medizin|الطب|医学'),
 'nursing': ('Сестринское дело', 'nursing|сестринское дело|hemşirelik|enfermería|التمريض|护理'),
 'law': ('Право', 'law|право|юриспруденция|юридический|hukuk|derecho|droit|recht|القانون|法学'),
 'education': ('Педагогика', 'education|pedagogy|педагогика|образование|учитель|eğitim|educación|éducation|педагогика|التربية|教育学'),
 'history': ('История', 'history|история|истории|tarih|historia|histoire|geschichte|التاريخ|历史'),
 'languages': ('Языки и литература', 'linguistics|literature|languages|лингвистика|филология|литература|языки|dilbilim|lingüística|linguistique|اللغويات|语言学'),
 'politics': ('Политология и международные отношения', 'political science|international relations|политология|международные отношения|uluslararası ilişkiler|relaciones internacionales|العلاقات الدولية|国际关系'),
 'environment': ('Экология и науки о Земле', 'environmental science|environmental studies|earth science|geography|geology|экология|география|геология|coğrafya|ecología|géographie|地理学'),
 'engineering': ('Инженерия — все направления', 'engineering|engineering sciences|инженерия|инженерные науки|инженер|mühendislik|инженерлік|ingeniería|ingénierie|ingenieurwesen|الهندسة|工程学'),
}
FIELDS.update({
 'aerospace': ('Авиация и космос', 'aerospace engineering|aeronautical engineering|авиастроение|авиакосмическая инженерия|uçak mühendisliği'),
 'chemical_eng': ('Химическая инженерия', 'chemical engineering|химическая инженерия|химической инженерии|kimya mühendisliği'),
 'materials': ('Материаловедение', 'materials science|materials engineering|материаловедение|malzeme bilimi'),
 'biomedical': ('Биомедицинская инженерия', 'biomedical engineering|биомедицинская инженерия|biyomedikal mühendisliği'),
 'automotive': ('Автомобилестроение', 'automotive engineering|автомобилестроение|otomotiv mühendisliği'),
 'agriculture': ('Сельское хозяйство', 'agriculture|agricultural engineering|агрономия|сельское хозяйство|ziraat'),
 'veterinary': ('Ветеринария', 'veterinary medicine|veterinary|ветеринария|ветеринарии|veterinerlik'),
 'dentistry': ('Стоматология', 'dentistry|стоматология|стоматологии|diş hekimliği'),
 'pharmacy': ('Фармация', 'pharmacy|фармация|фармацевтика|eczacılık'),
 'tourism': ('Туризм и гостеприимство', 'tourism|hospitality management|hotel management|туризм|гостиничное дело|turizm'),
 'journalism': ('Журналистика', 'journalism|журналистика|журналистики|gazetecilik'),
 'sociology': ('Социология', 'sociology|социология|социологии|sosyoloji'),
 'social_work': ('Социальная работа', 'social work|социальная работа|sosyal hizmet'),
 'philosophy': ('Философия', 'philosophy|философия|философии|felsefe'),
 'logistics': ('Логистика', 'logistics|supply chain|логистика|логистики|tedarik zinciri'),
 'statistics': ('Статистика', 'statistics|статистика|статистики|istatistik'),
})
RELATED = {
 'industrial': {'mechanical','manufacturing','math'}, 'mechanical': {'industrial','manufacturing'},
 'manufacturing': {'industrial','mechanical','electrical'}, 'computer': {'data','math','electrical'},
 'data': {'computer','math'}, 'art': {'design','media','music','theatre'},
 'design': {'art','architecture','media'}, 'media': {'art','design','theatre'},
 'architecture': {'design','civil'}, 'economics': {'business','finance'},
 'business': {'economics','finance'}, 'finance': {'economics','business'},
 'biology': {'chemistry','environment'}, 'chemistry': {'biology'},
 'medicine': {'nursing','biology'}, 'nursing': {'medicine'},
 'physics': {'math','electrical'}, 'math': {'computer','data'},
 'psychology': {'education'}, 'education': {'psychology'},
 'history': {'politics','languages'}, 'politics': {'history','law'},
 'languages': {'history'}, 'environment': {'biology'},
}
RELATED.update({'aerospace':{'mechanical'},'chemical_eng':{'chemistry','materials'},'materials':{'chemistry','physics'},'biomedical':{'biology','mechanical'},'automotive':{'mechanical','manufacturing'},'agriculture':{'biology','environment'},'veterinary':{'biology'},'dentistry':{'medicine'},'pharmacy':{'chemistry','biology'},'tourism':{'business'},'journalism':{'media','languages'},'sociology':{'politics','psychology'},'social_work':{'psychology','education'},'philosophy':{'history'},'logistics':{'industrial','manufacturing','business'},'statistics':{'math','data'}})
ENGINEERING = {'industrial','mechanical','manufacturing','computer','electrical','civil','engineering','aerospace','chemical_eng','materials','biomedical','automotive'}

def normalized(value):
    text = unicodedata.normalize('NFKD', str(value).casefold().replace('ё','е'))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return ' '.join(re.findall(r'\w+', text, re.UNICODE))

def field_ids(query):
    q = normalized(query)
    hits = []
    for key, (_, aliases) in FIELDS.items():
        for alias in aliases.split('|'):
            a = normalized(alias)
            for m in re.finditer(r'(?<!\w)' + re.escape(a) + r'(?!\w)', q):
                hits.append((m.start(), m.end(), key))
    # Suppress only nested aliases, preserving separate interests in the same query.
    found = {key for start, end, key in hits if not any(
        a <= start and b >= end and b-a > end-start for a,b,_ in hits)}
    if found == {'engineering'} and len(q.split()) > 1:
        from difflib import SequenceMatcher
        if any(SequenceMatcher(None,q,normalized(a)).ratio() >= .9 for key,(_,aliases) in FIELDS.items() if key != 'engineering' for a in aliases.split('|')):
            return set()
    return found


def suggest_fields(query):
    """Conservative typo suggestions; never silently substitutes a discipline."""
    from difflib import SequenceMatcher
    q = normalized(query)
    if len(q) < 5 or field_ids(q):
        return []
    scored=[]
    for key, (label, aliases) in FIELDS.items():
        score=max(SequenceMatcher(None,q,normalized(a)).ratio() for a in aliases.split('|'))
        if score >= .86:
            scored.append((score,key,label))
    return [(key,label) for _,key,label in sorted(scored,reverse=True)[:3]]

def programme_fields(program):
    if program.get('field_ids'):
        return set(program['field_ids'])
    return field_ids(program['name'])

def match_programmes(entry, query):
    """Return match category and matching programmes; empty-program rows never pad a search."""
    if not query.strip():
        return 'all', list(entry.get('programs', []))
    q = normalized(query)
    if q and q in normalized(entry['name'] + ' ' + ' '.join(entry.get('aliases', []))):
        return 'name', list(entry.get('programs', []))
    requested = field_ids(query)
    if 'engineering' in requested:
        requested = requested | ENGINEERING
    exact, related = [], []
    adjacent = set().union(*(RELATED.get(x, set()) for x in requested)) if requested else set()
    for p in entry.get('programs', []):
        subjects = programme_fields(p)
        strings = [p['name']] + p.get('search_tags', [])
        literal = any(q and q in normalized(s) for s in strings)
        if (requested & subjects) or (not requested and literal):
            exact.append(p)
        elif adjacent & subjects:
            related.append(p)
    if exact:
        return 'exact', exact
    if related:
        return 'related', related
    return None, []
