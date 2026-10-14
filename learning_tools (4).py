"""Curated lessons and topic-specific tutoring; optional configured AI provider."""
import json
import re
from pathlib import Path
from urllib.parse import quote

def load_lessons():
    data = json.loads(Path(__file__).with_name('learning_content.json').read_text(encoding='utf-8'))
    return data['lessons']

def words(s):
    return set(re.findall(r'[\w]+', s.casefold().replace('ё', 'е')))

def find_lesson(lessons, subject, topic, question=''):
    candidates = []
    text = (topic + ' ' + question).casefold().replace('ё','е')
    for lesson in lessons:
        if lesson['subject'] != subject:
            continue
        # Explicit topic matches outrank keywords in an unrelated follow-up.
        if topic == lesson['title'] or topic == lesson['id']:
            return lesson
        aliases = lesson['search_tags'] + [lesson['title']]
        score = max((len(a) for a in aliases if len(a)>2 and a.casefold().replace('ё','е') in text), default=0)
        if score:
            candidates.append((score,lesson))
    return max(candidates, key=lambda x:x[0])[1] if candidates else None

def lesson_modules(lessons):
    result = {}
    for l in lessons:
        # Practice is authored per topic, never copied from a different subject.
        result[l['title']] = dict(subject=l['subject'],minutes=l['minutes'],intro=l['theory'],
                                  worked_example=l['example'],base=l['questions'],remedial=[])
    return result

MODULE_ALIASES = {'Linear equations without guessing': ['линейные уравнения', 'уравнение'], 'Percentages in real life': ['проценты', 'процент'], 'A / an / the in two rules': ['артикли', 'articles'], 'Loops as repetition': ['циклы', 'цикл'], 'The 15-minute start': ['как начать', 'прокрастинация'], 'Turn an ambition into an evidence list': ['поступление', 'мотивационное письмо'], 'Russian: -тся or -ться': ['тся', 'ться'], 'Russian punctuation: simple sentence': ['пунктуация', 'запятая'], 'English: present simple or continuous': ['времена английского'], 'Geography: latitude and longitude': ['широта', 'долгота', 'координаты'], 'Geography: climate and latitude': ['климат'], 'Biology: cell basics': ['клетка', 'клетки'], 'Biology: genetics basics': ['генетика', 'наследственность'], 'Chemistry: atoms and the periodic table': ['таблица менделеева', 'периодическая таблица'], 'Chemistry: mixtures and compounds': ['смеси', 'соединения'], 'Physics: speed, distance and time': ['скорость', 'расстояние', 'путь'], 'Physics: forces and motion': ['силы', 'сила', 'законы ньютона'], 'History: chronology and evidence': ['хронология', 'исторические источники'], 'History: causes and consequences': ['причины и последствия'], 'Social studies: rights and institutions': ['права', 'государство'], 'Literature: figurative language': ['художественные средства'], 'Literature: plot and character': ['сюжет', 'герой', 'персонаж'], 'Economics: supply and demand': ['спрос', 'предложение'], 'Business: revenue, cost and profit': ['затраты'], 'Coding: variables and data types': ['переменные', 'типы данных'], 'Study skills: active recall': ['повторение', 'запоминание']}

def tutor_library(modules=None):
    import hashlib
    lessons = load_lessons()
    titles = {l['title'] for l in lessons}
    for title, m in (modules or {}).items():
        if title in titles:
            continue
        examples = m.get('base', [])
        sample = examples[0] if examples else None
        example = m.get('worked_example') or (sample['q'] + '\nОтвет: ' + str(sample['answer']) + '\n' + sample['explanation'] if sample else m['intro'])
        lessons.append(dict(id='module_'+hashlib.sha256(title.encode()).hexdigest()[:12], subject=m['subject'],
            title=title, search_tags=[title] + MODULE_ALIASES.get(title, []), minutes=m.get('minutes',10), theory=m['intro'], example=example,
            questions=examples))
    return lessons


def prepared_answer(lesson, action='explain'):
    if action == 'example':
        return lesson['example']
    if action == 'simpler':
        return lesson.get('simple_explanation') or lesson['theory'].split('. ')[0].rstrip('.') + '.\n\n' + lesson['example']
    return lesson['theory'] + '\n\n' + lesson['example']


# -----------------------------------------------------------------------
# Version 3.2: Extended grade-indexed topics and genuinely different help modes.
# The index is not a set of authored lessons. Without an AI API or a curated
# lesson, this module does not claim to answer a question it cannot answer.
# -----------------------------------------------------------------------
from functools import lru_cache

@lru_cache(maxsize=1)
def curriculum_index():
    path = Path(__file__).with_name('curriculum_guide.json')
    if not path.exists():
        return {'topics': [], 'offline_explanations': {}, 'sources': []}
    return json.loads(path.read_text(encoding='utf-8'))


def _norm(value):
    return re.sub(r'[^\w]+', ' ', str(value).casefold().replace('ё','е')).strip()


def get_rich_explanation(topic, question='', subject=''):
    # Do not select unrelated rich material on keyword-less or ambiguous queries.
    store = curriculum_index().get('offline_explanations', {})
    target = _norm(topic)
    query = _norm(question)
    if not target and not query:
        return None, None
    rich_subjects = {
        'Степени окисления':'Chemistry', 'Кислотность и pH':'Chemistry',
        'Вещества и смеси':'Chemistry', 'Спрос и предложение':'Economics & Business',
        'Линейные уравнения':'Math', 'Проценты':'Math',
        'Закон Ома':'Physics', 'Фотосинтез':'Biology',
        'Циклы':'Coding', 'Теорема Пифагора':'Math', 'Present Simple':'English',
        'Квадратные уравнения':'Math', 'Линейные функции и графики':'Math',
        'ДНК и РНК':'Biology', 'Кровообращение':'Biology',
        'Закон сохранения массы':'Chemistry', 'Вероятность простых событий':'Math',
        'Скорость путь время':'Physics', 'Митоз и мейоз':'Biology',
        'Периодическая таблица':'Chemistry', 'Генетика и наследование':'Biology',
        'Present Continuous':'English',
    }
    scores = []
    for title, record in store.items():
        if subject and rich_subjects.get(title) not in (None,subject):
            continue
        labels = [title] + record.get('aliases', [])
        for alias in labels:
            key = _norm(alias)
            if len(key) < 3:
                continue
            if target and (key == target or (len(key)>=6 and key in target)):
                scores.append((300+len(key),title,record))
            elif query and len(key)>=6 and key in query:
                scores.append((100+len(key),title,record))
    if scores:
        _,name,record=max(scores, key=lambda x:x[0])
        return name,record
    return None,None


def _quality_lesson(lesson):
    return bool(lesson and (lesson.get('theory') or lesson.get('example')))


def _offline_lesson_answer(lesson, mode='main'):
    if mode == 'simpler':
        original = lesson.get('simple_explanation')
        if original:
            return original
        theory = lesson.get('theory','').strip()
        # A different explanation method, not theory + the same example repeated.
        return ("**Попробуем иначе.** Вместо запоминания правила спросим, какую задачу оно решает. "
                "Раздели тему на три вопроса: что известно, что меняется и почему это связано?\n\n"
                "**Короткий ориентир:** " + (theory.split('. ')[0].rstrip('.') + '.' if theory else 'Начни с самого простого случая.')
                + "\n\nНазови один шаг, который остаётся непонятным: объяснение можно продолжить с него.")
    text = (lesson.get('theory') or '').strip()
    example = (lesson.get('example') or '').strip()
    if mode=='example':
        return '**Разобранный пример**\n\n'+example
    return ('**Что означает тема**\n\n'+text+ '\n\n**Как это работает на практике**\n\n' + example+
            '\n\n**Как проверить себя**\n\nПопробуй объяснить главное правило своими словами, затем реши одно похожее задание из блока ниже.')


def _rich_answer(title, record, mode):
    if mode == 'simpler':
        return '**То же самое простыми словами**\n\n' + record['simple']
    if mode == 'example':
        return '**Разберём новый пример**\n\n' + record['example']
    return ('### ' + title + '\n\n' + record['intro'] +
            '\n\n**Разобранный пример**\n\n' + record['example'] +
            '\n\n**Проверьте себя**\n\n' + record['quiz'])


def _ref_urls(topic, language):
    wikipedia_language = language if language in {'ru','en','ar','kk','tr','it','zh','ko','ja'} else 'en'
    from urllib.parse import quote
    text = quote(topic[:140], safe='')
    return {'wikipedia': f'https://{wikipedia_language}.wikipedia.org/w/index.php?search={text}',
            'khan': 'https://www.khanacademy.org/',
            'cambridge': 'https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-lower-secondary/curriculum'}


def render_tutor(st, subjects, ui, lx, ai_reply=None, modules=None):
    lessons = tutor_library(modules)
    index = curriculum_index()
    lang=st.session_state.get('interface_lang','ru')
    st.title(ui('AI Tutor','AI-репетитор'))
    st.write(ui('Choose a grade, subject and topic. We will explain the idea, show an example and practise.',
                'Выберите класс, предмет и тему. Затем разберём объяснение, пример и небольшую проверку.'))
    left,right=st.columns([1,2])
    with left:
        grade_options = [0] + list(range(1,12))
        grade = st.selectbox(ui('School grade','Класс'),grade_options,
                            format_func=lambda n: ui('All grades','Все классы') if n==0 else str(n),
                            key='tutor_grade_v36')
    with right:
        subject=st.selectbox(ui('Subject','Предмет'),list(subjects),format_func=lx,key='tutor_subject_v24')
    curated=[l for l in lessons if l['subject']==subject]
    indexed=[r['title'] for r in index.get('topics',[]) if r['subject']==subject and
             (grade==0 or r['grade_min']<=grade<=r['grade_max'])]
    lesson_titles = [l['title'] for l in curated]
    unique_topics=list(dict.fromkeys(indexed+lesson_titles))
    own=ui('My question','Мой вопрос')
    options=[own]+unique_topics
    select_key='tutor_topic_v25_'+subject
    if st.session_state.get(select_key) not in options:
        st.session_state[select_key]=own
    chosen=st.selectbox(ui('Topic','Тема'), options, key=select_key,format_func=lambda x: x if x==own else lx(x))
    if chosen==own:
        topic=st.text_input(ui('Topic in your own words','Тема своими словами'),
                            key='tutor_custom_v24', max_chars=200)
    else:
        topic=chosen
    question=st.text_area(ui('What would you like to understand?','Что хотите понять?'),
                          key='tutor_question_v24', max_chars=2000)
    st.caption(ui('The topic list is a guide across grades, not a separate authored lesson for every entry.',
                  'Список тем расширен, но готовый урок есть не для каждой записи. Произвольные вопросы требуют подключённой AI-модели.'))
    if st.button(ui('Explain','Объяснить'),type='primary',key='tutor_start_v24'):
        if not topic.strip() and not question.strip():
            st.warning(ui('Enter a topic or question.','Напишите тему или вопрос.'))
        else:
            # If a user typed a precise question, do not accidentally substitute a weak match.
            lesson = find_lesson(lessons,subject,topic,question)
            title,rich = get_rich_explanation(topic,question,subject)
            if topic and chosen!=own and chosen not in lesson_titles and not rich:
                lesson=None
            # AI first when configured: responds specifically to learner's prompt.
            live=None
            if ai_reply:
                with st.spinner(ui('Preparing your explanation…','Готовлю подробное объяснение…')):
                    try:
                        live = ai_reply(subject,topic,question,[])
                    except Exception:
                        live=None
            offline=(_rich_answer(title,rich,'main') if rich else
                     _offline_lesson_answer(lesson) if _quality_lesson(lesson) else '')
            st.session_state['tutor_v24']={
                'subject':subject,'topic':topic,'question':question,'lesson':lesson,
                'rich_name':title,'rich':rich,'answer':live,'offline':offline,
                'history':[],'initial_answer':live or offline,
            }
    session=st.session_state.get('tutor_v24')
    if not session or session['subject']!=subject:
        return
    st.caption(ui('Current topic: ','Текущая тема: ') + lx(session['topic'] or session['question']))
    if st.button(ui('Start over','Начать другую тему'),key='tutor_clear_v25'):
        st.session_state.pop('tutor_v24',None)
        st.rerun()
    l=session.get('lesson')
    rich=session.get('rich')
    rendered=session.get('answer') or session.get('offline')
    if rendered:
        with st.chat_message('assistant'):
            st.markdown(rendered if session.get('answer') else lx(rendered))
    else:
        st.info(ui('This topic is in the school topic index but does not have an authored explanation yet. To answer ANY new question dynamically, connect an AI provider in Streamlit Secrets. You can also read reference materials below.',
                   'Тема есть в справочнике, но готового объяснения пока нет. Для ответов на произвольные вопросы подключите AI-модель в Streamlit Secrets. Дополнительные материалы доступны ниже.'))
    if rendered:
        col1,col2=st.columns(2)
        for mode,col,label in [('simpler',col1,ui('Explain more simply','Объясни проще')),
                               ('example',col2,ui('Show another example','Покажи другой пример'))]:
            with col:
                if st.button(label,key='tutor_action_'+mode):
                    reply=None
                    if ai_reply:
                        prompt=("Explain the topic again MUCH more simply using a new analogy, short steps "
                                "and a DIFFERENT easy worked example, not the original text."
                                if mode=='simpler' else
                                "Provide ONE new worked example for this topic with clear steps and check the answer.")
                        try:
                            reply=ai_reply(session['subject'],session['topic'],prompt,
                                           ([{'role':'user','content':session['question'] or session['topic']},
                                             {'role':'assistant','content':rendered}] + session['history'][-6:]))
                        except Exception:
                            reply=None
                    generated=bool(reply)
                    if not reply:
                        if rich:
                            reply=_rich_answer(session.get('rich_name',''),rich,mode)
                        elif l:
                            reply=_offline_lesson_answer(l,mode)
                    if reply:
                        st.session_state['tutor_v24']['history'].extend([
                            {'role':'user','content':label}, {'role':'assistant','content':reply if generated else lx(reply)}
                        ])
                        st.rerun()
                    else:
                        st.info(ui('There is no additional offline version; connect an AI model for a new explanation.',
                                   'Нового объяснения в офлайн-базе пока нет. Подключите AI для другого разбора.'))
    for m in session['history']:
        with st.chat_message(m['role']):
            st.markdown(m['content'])
    if l and l.get('questions'):
        with st.expander(ui('Check your understanding','Проверьте себя')):
            for idx,q in enumerate(l['questions'][:4]):
                opts=q['options']
                value=st.radio(lx(q['q']),opts,format_func=lx,index=None,
                               key=f'tutor_quiz_{l["id"]}_{idx}')
                if st.button(ui('Check','Проверить'),key=f'tutor_mark_{l["id"]}_{idx}'):
                    if value is None:
                        st.info(ui('Choose an answer.','Выберите ответ.'))
                    elif value==q['answer']:
                        st.success(lx(q['explanation']))
                    else:
                        st.warning(lx(q['explanation']))
    with st.form('tutor_follow_v24',clear_on_submit=True):
        follow=st.text_input(ui('Follow-up question','Уточняющий вопрос'),max_chars=2000)
        send=st.form_submit_button(ui('Ask','Задать вопрос'))
    if send and follow.strip():
        context=[{'role':'user','content':session['question'] or session['topic']},
                 {'role':'assistant','content':rendered or ''}]+session['history'][-8:]
        reply=None
        if ai_reply:
            try:
                reply=ai_reply(subject,session['topic'],follow,context)
            except Exception:
                reply=None
        if not reply:
            rich_title,related=get_rich_explanation(follow,follow,subject)
            if related and rich_title != session.get('rich_name'):
                reply=_rich_answer(rich_title,related,'main')
            else:
                other=find_lesson(lessons,subject,'',follow)
                if _quality_lesson(other) and other is not l:
                    reply=_offline_lesson_answer(other)
        if not reply:
            reply=ui('I do not have a verified offline answer to this exact question. A configured AI model can answer follow-ups; meanwhile check the reference below.',
                     'На этот конкретный вопрос в проверенной офлайн-базе пока нет ответа. Подключённая AI-модель сможет разобрать уточнение; также можно открыть материал по теме ниже.')
        session['history'].extend([{'role':'user','content':follow},{'role':'assistant','content':reply}])
        st.rerun()
    if st.button(ui('Ask a human tutor about this topic','Попросить помощи у репетитора-человека'),key='tutor_human_v36'):
        st.session_state['human_support_prefill']=(subject+': '+str(session['topic'] or session['question']))[:690]
        st.session_state.page='Human Support'
        st.rerun()
    # References are always available, even when a lesson exists.
    chosen_ref = session['topic'] or session['question'] or subject
    refs=_ref_urls(chosen_ref,lang)
    st.markdown('**'+ui('Read more','Дополнительные материалы')+'**')
    r1,r2,r3=st.columns(3)
    with r1:
        st.link_button(ui('Find in Wikipedia','Найти в Википедии'),refs['wikipedia'],use_container_width=True)
    with r2:
        st.link_button(ui('Khan Academy courses','Курсы Khan Academy'),refs['khan'],use_container_width=True)
    with r3:
        st.link_button(ui('Cambridge curriculum','Программы Cambridge'),refs['cambridge'],use_container_width=True)
    st.caption(ui('Links are for further reading. Wikipedia entries are not independently verified by this application.',
                  'Ссылки предназначены для дополнительного чтения. Статьи Википедии не проверяются платформой автоматически.'))
