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


def render_tutor(st, subjects, ui, lx, ai_reply=None, modules=None):
    lessons = tutor_library(modules)
    st.title(ui('Tutor', 'Репетитор'))
    st.write(ui('Choose a topic, read an explanation, then practise.', 'Выберите тему, разберите объяснение и попробуйте решить задания.'))
    subject = st.selectbox(ui('Subject','Предмет'), list(subjects), format_func=lx, key='tutor_subject_v24')
    available = [l for l in lessons if l['subject']==subject]
    st.caption(ui(f'{len(available)} lessons in this subject',f'Уроков по предмету: {len(available)}'))
    labels = [l['title'] for l in available]
    chosen = st.selectbox(ui('Topic','Тема'), [ui('My question','Мой вопрос')]+labels, key='tutor_topic_v25_'+subject, format_func=lx)
    topic = st.text_input(ui('Topic in your own words','Тема своими словами'),key='tutor_custom_v24',max_chars=200) if chosen not in labels else chosen
    question = st.text_area(ui('What would you like to understand?','Что хотите понять?'),key='tutor_question_v24',max_chars=2000)
    if st.button(ui('Explain','Объяснить'),type='primary',key='tutor_start_v24'):
        if not topic.strip() and not question.strip():
            st.warning(ui('Enter a topic or question.','Напишите тему или вопрос.'))
        else:
            lesson = find_lesson(lessons,subject,topic,question)
            answer = None
            if ai_reply:
                with st.spinner(ui('Preparing an explanation…','Готовлю объяснение…')):
                    answer = ai_reply(subject,topic,question,[])
            st.session_state['tutor_v24'] = dict(subject=subject,topic=topic,question=question,
                lesson=lesson,answer=answer,history=[], initial_answer=answer or (prepared_answer(lesson) if lesson else ''))
    session = st.session_state.get('tutor_v24')
    if not session:
        return
    if session['subject'] != subject:
        return
    st.caption(ui('Current topic: ','Текущая тема: ') + lx(session['topic'] or session['question']))
    if st.button(ui('Start over','Начать другую тему'),key='tutor_clear_v25'):
        st.session_state.pop('tutor_v24',None)
        st.rerun()
    l = session['lesson']
    if session['answer']:
        st.chat_message('assistant').write(session['answer'])
    elif l:
        st.caption(ui('Lesson from the learning library','Объяснение из учебной библиотеки'))
        st.subheader(lx(l['title']))
        st.write(lx(l['theory']))
        st.markdown(ui('**Worked example**','**Разобранный пример**'))
        st.write(lx(l['example']))
    else:
        st.info(ui('There is no prepared explanation for this topic yet. Choose one of the available lessons or open a reference below.',
                   'Для этой темы ещё нет готового объяснения. Выберите урок из списка или откройте материал по теме ниже.'))
        search = quote((topic or question)[:200])
        st.link_button(ui('Find a reference','Найти материал по теме'),f'https://ru.wikipedia.org/w/index.php?search={search}')
        return
    if l:
        for action,label in [('simpler',ui('Explain more simply','Объясни проще')),('example',ui('Show a worked example','Покажи разбор примера'))]:
            if st.button(label,key='tutor_action_'+action):
                session['history'].extend([{'role':'user','content':label}, {'role':'assistant','content':lx(prepared_answer(l,action))}])
                st.rerun()
    for m in session['history']:
        st.chat_message(m['role']).write(m['content'])
    if l:
        with st.expander(ui('Check your understanding','Проверьте себя')):
            for idx,q in enumerate(l['questions']):
                opts=q['options'][idx%len(q['options']):]+q['options'][:idx%len(q['options'])]
                value=st.radio(lx(q['q']),opts,format_func=lx,index=None,key=f'tutor_quiz_{l["id"]}_{idx}')
                if st.button(ui('Check','Проверить'),key=f'tutor_mark_{l["id"]}_{idx}'):
                    if value is None: st.info(ui('Choose an answer.','Выберите ответ.'))
                    elif value==q['answer']: st.success(lx(q['explanation']))
                    else: st.warning(lx(q['explanation']))
    with st.form('tutor_follow_v24',clear_on_submit=True):
        follow=st.text_input(ui('Follow-up question','Уточняющий вопрос'),max_chars=2000)
        send=st.form_submit_button(ui('Ask','Задать вопрос'))
    if send and follow.strip():
        context=[{'role':'user','content':session['question'] or session['topic']},
                 {'role':'assistant','content':session.get('initial_answer','')}] + session['history'][-8:]
        response = ai_reply(subject,session['topic'],follow,context) if ai_reply else None
        if not response:
            other=find_lesson(lessons,subject,'',follow)
            if other:
                response=lx(prepared_answer(other))
            else:
                response=ui('This question needs an explanation beyond the prepared lesson. The available example and practice are above.',
                            'На этот уточняющий вопрос в учебной библиотеке пока нет отдельного ответа. Выше доступны объяснение, пример и задания по выбранной теме.')
        session['history'].extend([{'role':'user','content':follow},{'role':'assistant','content':response}])
        st.rerun()
