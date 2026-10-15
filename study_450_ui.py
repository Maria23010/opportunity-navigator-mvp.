"""Shared offline lessons and practice. Quality is explicitly labelled."""
import json
from functools import lru_cache
from pathlib import Path
import streamlit as st
def bank():
    """Read the complete bank, overlay authored lessons by their stable id."""
    root = Path(__file__).resolve().parent
    path = root / 'study_450_bank.json'
    data = json.loads(path.read_text(encoding='utf-8'))['topics']
    folder = root / 'lessons_450'
    if folder.is_dir():
        for lesson_file in sorted(folder.glob('*.json')):
            try:
                lesson = json.loads(lesson_file.read_text(encoding='utf-8'))
                identity = lesson.get('id') or (str(lesson.get('subject')) + '::' + str(lesson.get('title')))
                if identity not in data:
                    continue
                for field in ('levels', 'tasks', 'illustration'):
                    if field in lesson:
                        data[identity][field] = lesson[field]
                if lesson.get('lesson_status') == 'authored_batch_01' or lesson.get('quality') == 'curated_subject_specific':
                    data[identity]['quality'] = 'curated_subject_specific'
                data[identity]['_lesson_file'] = str(lesson_file.relative_to(root))
            except (OSError, ValueError, TypeError, KeyError):
                continue
    return data
def picker(prefix,ui,localize=lambda x:x):
    items=list(bank().values());a,b=st.columns([1,2])
    with a: grade=st.selectbox(ui('Grade','Класс'),[0]+list(range(1,12)),format_func=lambda x:ui('All','Все') if x==0 else str(x),key=prefix+'_grade')
    with b:
        subjects=sorted({r['subject'] for r in items})
        subject=st.selectbox(ui('Subject','Предмет'),subjects,format_func=localize,key=prefix+'_subject')
    eligible=[r for r in items if r['subject']==subject and (not grade or r['grade_min']<=grade<=r['grade_max'])]
    if not eligible:st.info(ui('No topics for this grade.','Для этого класса тем нет.'));return None
    titles=sorted(r['title'] for r in eligible)
    incoming=st.session_state.pop(prefix+'_incoming',None)
    if incoming in titles:st.session_state[prefix+'_topic']=incoming
    if st.session_state.get(prefix+'_topic') not in titles:st.session_state[prefix+'_topic']=titles[0]
    title=st.selectbox(ui('Topic','Тема'),titles,format_func=localize,key=prefix+'_topic')
    return next(r for r in eligible if r['title']==title)

def translate_lesson(markdown, lang, localize):
    """Translate a lesson as a single request when possible, preserving the original JSON."""
    if lang == 'ru' or not isinstance(markdown, str) or not markdown.strip():
        return markdown
    # Cache by lesson text and locale; avoids repeated HTTP calls on rerun.
    return _translate_lesson_cached(markdown, lang, localize)

@st.cache_data(ttl=604800, show_spinner=False)
def _translate_lesson_cached(markdown, lang, _localize):
    # Keep requests below typical public translator size limits.
    # Split at paragraph boundaries only for long lessons.
    if len(markdown) <= 3200:
        return _localize(markdown)
    blocks=markdown.split('\n\n'); groups=[]; current=[]; size=0
    for block in blocks:
        if size+len(block)>3000 and current:
            groups.append('\n\n'.join(current));current=[];size=0
        if len(block)>3000:
            if current:groups.append('\n\n'.join(current));current=[];size=0
            groups.extend(block[i:i+3000] for i in range(0,len(block),3000))
        else:current.append(block);size+=len(block)+2
    if current:groups.append('\n\n'.join(current))
    return '\n\n'.join(_localize(part) for part in groups)

def render_study_tutor(ui, localize=lambda x:x, lang="ru"):
    st.subheader(ui('Lessons library','Библиотека уроков'))
    item=picker('study_tutor',ui,localize)
    if not item:return
    curated=item.get('quality')=='curated_subject_specific'
    if not curated:st.info(ui('This lesson is based on a short source note and still needs a complete rewrite.','Этот урок пока основан на кратком исходном конспекте и требует полноценной переработки.'))
    modes={'full':ui('Detailed','Подробно'),'easy':ui('Simpler','Проще'),'short':ui('Brief','Кратко')}
    mode=st.radio(ui('Explanation','Формат объяснения'),list(modes),format_func=lambda k:modes[k],horizontal=True,key='study_level')
    if item.get('illustration'):
        image=Path(__file__).resolve().parent / item['illustration']
        if image.exists():st.image(str(image),caption=localize(item['title']))
    st.markdown(translate_lesson(item['levels'][mode], lang, localize))
    with st.expander(ui('Lesson source','Источник урока')):
        st.code(item.get('_lesson_file', 'study_450_bank.json'))
    if st.button(ui('Practice this topic →','Тренироваться по этой теме →'),type='primary',key='study_go_practice'):
        st.session_state['study_practice_subject']=item['subject'];st.session_state['study_practice_incoming']=item['title'];st.session_state['page']='Learning Hub';st.rerun()
def task_feedback(task):
    """Support old and new question schemas without KeyError."""
    for field in ('self_check', 'explanation', 'answer'):
        value = task.get(field)
        if value is not None and str(value).strip():
            return str(value)
    return 'Ответ для этого задания пока не указан.'

def render_study_practice(ui, localize=lambda x:x, lang="ru"):
    st.subheader(ui('Topic practice','Тренировка по теме'))
    item=picker('study_practice',ui,localize)
    if not item:return
    if item.get('quality')!='curated_subject_specific':st.info(ui('These are basic comprehension checks; full subject-specific tasks are not yet prepared.','Здесь пока только вопросы на понимание: полноценные предметные задания ещё не подготовлены.'))
    tasks=item['tasks'];key='study_task_number';old=st.session_state.get('study_task_identity')
    identity=item['subject']+'::'+item['title']
    if old!=identity:st.session_state['study_task_identity']=identity;st.session_state.pop(key,None)
    idx=st.selectbox(ui('Question','Вопрос'),range(len(tasks)),format_func=lambda i:f'{i+1}. {localize(tasks[i]["category"])}',key=key)
    task=tasks[idx];st.markdown('#### '+localize(task['category']));st.write(localize(task['prompt']))
    if task['type']=='mcq':
        answer=st.radio(ui('Choose an answer','Выбери ответ'),range(len(task['options'])),format_func=lambda i:localize(task['options'][i]),index=None,key='answer_'+identity+'_'+str(idx))
        if st.button(ui('Check answer','Проверить ответ'),key='check_'+identity+'_'+str(idx)):
            if answer is None:st.warning(ui('Choose an answer first.','Сначала выбери ответ.'))
            else:
                if answer==task.get('correct'):st.success(ui('Correct!','Верно!'))
                else:st.error(ui('Not quite.','Пока неверно.'))
                st.info(localize(task_feedback(task)))
    else:
        st.text_area(ui('Your answer','Твой ответ'),key='answer_'+identity+'_'+str(idx))
        with st.expander(ui('Compare with the lesson','Сверить с уроком')):st.write(localize(task_feedback(task)))
    a,b=st.columns(2)
    with a:
        if st.button(ui('Next question','Следующий вопрос'),key='study_next'):
            st.session_state[key]=(idx+1)%len(tasks);st.rerun()
    with b:
        if st.button(ui('Back to lesson','Вернуться к уроку'),key='study_to_tutor'):
            st.session_state['study_tutor_subject']=item['subject'];st.session_state['study_tutor_incoming']=item['title'];st.session_state['page']='AI Tutor';st.rerun()
