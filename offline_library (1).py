"""Small-file offline school library. No API keys and no unsupported AI claims."""
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

@lru_cache(maxsize=1)
def load_topic_notes():
    directory=Path(__file__).with_name('curriculum_lessons')
    result={}
    for path in sorted(directory.glob('*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        for row in data.get('lessons',[]):
            key=(row['subject'],row['title'])
            if key in result:
                raise ValueError(f'Duplicate school topic: {key}')
            result[key]=row
    return result

def topic_note(subject,title):
    return load_topic_notes().get((subject,title))

def lesson_links(note, lang='ru'):
    """Never imply a subject homepage is an exact-match article."""
    subject=note['subject']
    ref=note['reference']
    label=ref['label']
    site_url=ref['url']
    if ref.get('kind')!='конкретная статья':
        label+=' · оглавление предмета'
    # Only expose a query as a search, NOT as a verified matching course.
    domain=site_url.split('/')[2]
    query='site:'+domain+' "'+note['title']+'"'
    search='https://www.google.com/search?q='+quote(query)
    return [(label,site_url),('Поиск материалов по теме в этом источнике',search)]

def _t(ui,english,russian):
    return ui(english,russian)

def show_topic_note(st,note,ui,lx,namespace='library'):
    title=note['title']
    detailed=note.get('level')=='подробный авторский разбор'
    st.caption(ui('In-depth authored explanation' if detailed else 'Short offline topic notes — not a complete course',
                  'Подробный подготовленный разбор' if detailed else 'Базовый конспект — не полный учебный курс'))
    st.subheader(ui('1. Theory and key idea','1. Теория и главное правило'))
    st.markdown(lx(note.get('theory_extended') or note['intro']))
    st.subheader(ui('2. Step-by-step approach','2. Как разбирать задание'))
    for i,step in enumerate(note['steps'],1):
        st.markdown(f'{i}. {lx(step)}')
    st.subheader(ui('3. Worked example','3. Разобранный пример'))
    st.markdown(lx(note['example']))
    for additional in note.get('examples_extra', []):
        with st.expander(ui('Another worked example','Другой разобранный пример')):
            st.markdown(lx(additional))
    with st.expander(ui('Explain in simpler words','Объяснить проще')):
        st.markdown(lx(note.get('simple_extended') or note['simple']))
    st.subheader(ui('4. Try it yourself','4. Попробуйте сами'))
    st.write(lx(note['quiz']))
    st.text_area(ui('Your attempt (not submitted to anyone)','Ваше решение (никому не отправляется)'),
                 key=f'{namespace}_answer_{note["subject"]}_{title}',height=85)
    with st.expander(ui('See answer and self-check guide','Показать разбор для самопроверки')):
        st.markdown(lx(note.get('check_answer') or note['example']))
        st.caption(ui('Compare your reasoning, not only the final sentence.',
                      'Сравните ход рассуждений, а не только последнее предложение.'))
    st.subheader(ui('5. Further reading','5. Дополнительные материалы'))
    for label,url in lesson_links(note):
        st.link_button(lx(label), url)
    if not note.get('reference_verified'):
        st.caption(ui('The reference opens a subject catalogue, not a verified article about this exact topic. Search results must be checked.',
                      'Ссылка ведёт в предметный справочник, а не на проверенную статью по этой конкретной теме. Результаты поиска нужно проверить.'))

def render_offline_learning_center(st,ui,lx):
    notes=load_topic_notes()
    grades=[0]+list(range(1,12))
    left,right=st.columns([1,2])
    with left:
        grade=st.selectbox(ui('School grade','Класс'),grades,
            format_func=lambda n: ui('All grades','Все классы') if n==0 else str(n),
            key='school_lesson_grade_v37')
    with right:
        subjects=sorted({key[0] for key in notes})
        subject=st.selectbox(ui('Subject','Предмет'),subjects,format_func=lx,
                             key='school_lesson_subject_v37')
    pool=[r for (s,t),r in notes.items() if s==subject and (grade==0 or r['grade_min']<=grade<=r['grade_max'])]
    names=sorted(r['title'] for r in pool)
    if not names:
        st.warning(ui('No topics for this grade','Для этого класса темы не найдены'))
        return
    st.caption(ui(f'{len(names)} topics in this selection',f'Тем в выбранной группе: {len(names)}'))
    key='school_lesson_topic_v37_'+subject
    if st.session_state.get(key) not in names:
        st.session_state[key]=names[0]
    title=st.selectbox(ui('Lesson','Урок'),names,format_func=lx,key=key)
    show_topic_note(st,notes[(subject,title)],ui,lx,'hub')

LEGACY_TOPICS={
    'Loops as repetition':('Coding','Циклы'),
    'Linear equations without guessing':('Math','Линейные уравнения'),
    'Percentages in real life':('Math','Проценты'),
    'Russian: -тся or -ться':('Russian language','Правописание -тся и -ться'),
    'Russian punctuation: simple sentence':('Russian language','Пунктуация'),
    'English: present simple or continuous':('English','Present Simple'),
    'Biology: cell basics':('Biology','Строение клетки'),
    'Biology: genetics basics':('Biology','Генетика и наследование'),
    'Chemistry: atoms and the periodic table':('Chemistry','Атомы и молекулы'),
    'Chemistry: mixtures and compounds':('Chemistry','Вещества и смеси'),
    'Physics: speed, distance and time':('Physics','Скорость путь время'),
    'Physics: forces and motion':('Physics','Законы Ньютона'),
    'Geography: latitude and longitude':('Geography','Широта и долгота'),
    'Geography: climate and latitude':('Geography','Климатообразующие факторы'),
    'History: chronology and evidence':('History','Исторические источники'),
    'History: causes and consequences':('History','Причины исторических событий'),
    'Social studies: rights and institutions':('Social studies','Права и обязанности'),
    'Literature: figurative language':('Literature','Средства выразительности'),
    'Literature: plot and character':('Literature','Сюжет и композиция'),
    'Economics: supply and demand':('Economics & Business','Спрос и предложение'),
    'Business: revenue, cost and profit':('Economics & Business','Себестоимость и прибыль'),
    'Coding: variables and data types':('Coding','Python: переменные'),
    'Study skills: active recall':('Study skills','Активное воспроизведение'),
    'Python: функции':('Coding','Python: функции'),
    'Части речи':('Russian language','Части речи'),
    'Исторические источники':('History','Исторические источники'),
    'Плотность вещества':('Physics','Плотность'),
    'Литосферные плиты':('Geography','Литосфера'),
}

def legacy_topic_note(title,subject):
    if (subject,title) in load_topic_notes():
        return topic_note(subject,title)
    target=LEGACY_TOPICS.get(title)
    if target and target[0]==subject:
        return topic_note(*target)
    # Under no circumstances return an unrelated subject due to a substring match.
    return None
