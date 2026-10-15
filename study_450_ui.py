"""Unified 450-topic offline tutor and practice library."""
import json
from functools import lru_cache
from pathlib import Path
import streamlit as st

@lru_cache(maxsize=1)
def bank():
    return json.loads(Path(__file__).with_name('study_450_bank.json').read_text(encoding='utf-8'))['topics']

def picker(prefix, ui):
    records=list(bank().values())
    a,b=st.columns([1,2])
    with a:
        grade=st.selectbox(ui('Grade','Класс'),[0]+list(range(1,12)),format_func=lambda x:ui('All','Все') if x==0 else str(x),key=prefix+'_grade')
    with b:
        subject_options=sorted({x['subject'] for x in records})
        if st.session_state.get(prefix+'_subject') not in subject_options: st.session_state[prefix+'_subject']=subject_options[0]
        subject=st.selectbox(ui('Subject','Предмет'),subject_options,key=prefix+'_subject')
    filtered=[x for x in records if x['subject']==subject and (grade==0 or x['grade_min']<=grade<=x['grade_max'])]
    titles=sorted(x['title'] for x in filtered)
    if not titles:
        st.info(ui('No topics for this grade.','Для этого класса тем нет.'))
        return None
    requested=st.session_state.pop(prefix+'_incoming',None)
    key=prefix+'_topic'
    if requested in titles: st.session_state[key]=requested
    if st.session_state.get(key) not in titles: st.session_state[key]=titles[0]
    title=st.selectbox(ui('Topic','Тема'),titles,key=key)
    return next(x for x in filtered if x['title']==title)

def render_study_tutor(ui):
    st.subheader(ui('School lessons: 450 topics','Школьные уроки: 450 тем'))
    st.caption(ui('Three reading modes based on the existing offline notes. No API required.', 'Три формата на основе имеющихся офлайн-конспектов. API не нужен.'))
    item=picker('study_tutor',ui)
    if not item:return
    modes={'full':ui('Detailed','Подробно'),'easy':ui('Simpler','Проще'),'short':ui('Brief','Кратко')}
    mode=st.radio(ui('Explanation','Формат объяснения'),list(modes),format_func=lambda k:modes[k],horizontal=True,key='study_level')
    st.markdown(item['levels'][mode])
    with st.expander(ui('About the material','О качестве материала')):
        st.write(ui('Some source notes are short. This view reorganizes them; it does not pretend they are newly researched full textbooks.', 'Часть исходных конспектов короткая. Здесь они представлены в трёх форматах, но это ещё не три независимо написанных полноценных учебника.'))
    if st.button(ui('Go to practice →','Перейти к тренировке →'),type='primary',key='study_go_practice'):
        st.session_state['study_practice_subject']=item['subject']
        st.session_state['study_practice_incoming']=item['title']
        st.session_state['page']='Learning Hub'
        st.rerun()

def render_study_practice(ui):
    st.subheader(ui('Practice by topic','Нарешка по темам'))
    st.caption(ui('12 varied open-ended exercises per topic, 5,400 in total. Self-check guidance; no automatic grading of free text.', '12 заданий на каждую тему, всего 5 400. Самопроверка; автоматической оценки свободного ответа нет.'))
    item=picker('study_practice',ui)
    if not item:return
    tasks=item['tasks']
    idx=st.selectbox(ui('Exercise','Задание'),range(len(tasks)),format_func=lambda i:f'{i+1}. {tasks[i]["category"]}',key='study_task_number')
    task=tasks[idx]
    st.markdown('#### '+task['category'])
    st.write(task['prompt'])
    st.text_area(ui('Your solution','Ваш ответ'),key='study_response_'+item['subject']+'_'+item['title']+'_'+str(idx),height=130)
    with st.expander(ui('Self-check guide','Открыть подсказку для самопроверки')):
        st.write(task['self_check'])
        st.caption(ui('For open questions, multiple correct answers are possible.','У открытых заданий могут быть разные правильные ответы.'))
    a,b=st.columns(2)
    with a:
        if st.button(ui('Next exercise','Следующее задание'),key='study_next'):
            st.session_state['study_task_number']=(idx+1)%len(tasks)
            st.rerun()
    with b:
        if st.button(ui('Back to explanation','Вернуться к теории'),key='study_to_tutor'):
            st.session_state['study_tutor_subject']=item['subject']
            st.session_state['study_tutor_incoming']=item['title']
            st.session_state['page']='AI Tutor'
            st.rerun()
