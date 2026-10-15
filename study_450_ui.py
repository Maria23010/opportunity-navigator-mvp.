"""Shared offline lessons and practice. Quality is explicitly labelled."""
import json
from functools import lru_cache
from pathlib import Path
import streamlit as st
@lru_cache(maxsize=1)
def bank():
    return json.loads(Path(__file__).with_name('study_450_bank.json').read_text(encoding='utf8'))['topics']
def picker(prefix,ui):
    items=list(bank().values());a,b=st.columns([1,2])
    with a: grade=st.selectbox(ui('Grade','Класс'),[0]+list(range(1,12)),format_func=lambda x:ui('All','Все') if x==0 else str(x),key=prefix+'_grade')
    with b:
        subjects=sorted({r['subject'] for r in items})
        subject=st.selectbox(ui('Subject','Предмет'),subjects,key=prefix+'_subject')
    eligible=[r for r in items if r['subject']==subject and (not grade or r['grade_min']<=grade<=r['grade_max'])]
    if not eligible:st.info(ui('No topics for this grade.','Для этого класса тем нет.'));return None
    titles=sorted(r['title'] for r in eligible)
    incoming=st.session_state.pop(prefix+'_incoming',None)
    if incoming in titles:st.session_state[prefix+'_topic']=incoming
    if st.session_state.get(prefix+'_topic') not in titles:st.session_state[prefix+'_topic']=titles[0]
    title=st.selectbox(ui('Topic','Тема'),titles,key=prefix+'_topic')
    return next(r for r in eligible if r['title']==title)
def render_study_tutor(ui):
    st.subheader(ui('Lessons library','Библиотека уроков'))
    item=picker('study_tutor',ui)
    if not item:return
    curated=item.get('quality')=='curated_subject_specific'
    if not curated:st.info(ui('This lesson is based on a short source note and still needs a complete rewrite.','Этот урок пока основан на кратком исходном конспекте и требует полноценной переработки.'))
    modes={'full':ui('Detailed','Подробно'),'easy':ui('Simpler','Проще'),'short':ui('Brief','Кратко')}
    mode=st.radio(ui('Explanation','Формат объяснения'),list(modes),format_func=lambda k:modes[k],horizontal=True,key='study_level')
    if item.get('illustration'):
        image=Path(__file__).with_name(item['illustration'])
        if image.exists():st.image(str(image),caption=ui('Diagram of a mushroom','Схема строения гриба'))
    st.markdown(item['levels'][mode])
    if st.button(ui('Practice this topic →','Тренироваться по этой теме →'),type='primary',key='study_go_practice'):
        st.session_state['study_practice_subject']=item['subject'];st.session_state['study_practice_incoming']=item['title'];st.session_state['page']='Learning Hub';st.rerun()
def render_study_practice(ui):
    st.subheader(ui('Topic practice','Тренировка по теме'))
    item=picker('study_practice',ui)
    if not item:return
    if item.get('quality')!='curated_subject_specific':st.info(ui('These are basic comprehension checks; full subject-specific tasks are not yet prepared.','Здесь пока только вопросы на понимание: полноценные предметные задания ещё не подготовлены.'))
    tasks=item['tasks'];key='study_task_number';old=st.session_state.get('study_task_identity')
    identity=item['subject']+'::'+item['title']
    if old!=identity:st.session_state['study_task_identity']=identity;st.session_state.pop(key,None)
    idx=st.selectbox(ui('Question','Вопрос'),range(len(tasks)),format_func=lambda i:f'{i+1}. {tasks[i]["category"]}',key=key)
    task=tasks[idx];st.markdown('#### '+task['category']);st.write(task['prompt'])
    if task['type']=='mcq':
        answer=st.radio(ui('Choose an answer','Выбери ответ'),range(len(task['options'])),format_func=lambda i:task['options'][i],index=None,key='answer_'+identity+'_'+str(idx))
        if st.button(ui('Check answer','Проверить ответ'),key='check_'+identity+'_'+str(idx)):
            if answer is None:st.warning(ui('Choose an answer first.','Сначала выбери ответ.'))
            else:
                if answer==task['correct']:st.success(ui('Correct!','Верно!'))
                else:st.error(ui('Not quite.','Пока неверно.'))
                st.info(task['self_check'])
    else:
        st.text_area(ui('Your answer','Твой ответ'),key='answer_'+identity+'_'+str(idx))
        with st.expander(ui('Compare with the lesson','Сверить с уроком')):st.write(task['self_check'])
    a,b=st.columns(2)
    with a:
        if st.button(ui('Next question','Следующий вопрос'),key='study_next'):
            st.session_state[key]=(idx+1)%len(tasks);st.rerun()
    with b:
        if st.button(ui('Back to lesson','Вернуться к уроку'),key='study_to_tutor'):
            st.session_state['study_tutor_subject']=item['subject'];st.session_state['study_tutor_incoming']=item['title'];st.session_state['page']='AI Tutor';st.rerun()
