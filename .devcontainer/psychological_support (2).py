"""Human-only support. No invented specialists, availability, or sent messages."""
import time
from urllib.parse import urlparse
import requests

class SupportError(Exception):
    pass

class SupportClient:
    def __init__(self,url,key,state,slot):
        parsed=urlparse(url)
        if parsed.scheme!='https' or not parsed.hostname or not parsed.hostname.endswith('.supabase.co') or parsed.path not in ('','/'):
            raise SupportError('Неверная настройка сервиса поддержки.')
        self.url=url.rstrip('/');self.key=key;self.state=state;self.slot=slot
    def auth(self,path,payload):
        try:
            r=requests.post(self.url+'/auth/v1/'+path,json=payload,headers={'apikey':self.key},timeout=12)
            if not r.ok: raise SupportError('Не удалось войти. Проверьте данные и настройки доступа.')
            d=r.json()
            if not d.get('access_token'): raise SupportError('Сервис не создал сессию.')
            d['_refresh_at']=time.time()+int(d.get('expires_in',3600))-90
            self.state[self.slot]=d
        except requests.RequestException:
            raise SupportError('Сервис временно недоступен. Сообщение не отправлено.')
    def token(self):
        d=self.state.get(self.slot,{})
        if d and time.time()>d.get('_refresh_at',0):
            self.auth('token?grant_type=refresh_token',{'refresh_token':d['refresh_token']})
            d=self.state[self.slot]
        return d.get('access_token',self.key)
    def rpc(self,name,payload=None):
        return self.request('POST','rpc/'+name,payload or {})
    def request(self,method,path,payload=None,params=None):
        try:
            r=requests.request(method,self.url+'/rest/v1/'+path,json=payload,params=params,
                headers={'apikey':self.key,'Authorization':'Bearer '+self.token()},timeout=12)
            if not r.ok: raise SupportError('Действие не выполнено. Обновите страницу или попробуйте позже. Сообщение не отправлено.')
            return r.json() if r.content else None
        except requests.RequestException:
            raise SupportError('Связь прервалась. Обновите беседу, чтобы проверить, дошло ли сообщение.')
    def uid(self): return self.state.get(self.slot,{}).get('user',{}).get('id')

def render_support(st,secret):
    st.title('Психологическая помощь')
    st.write('Здесь можно обратиться к человеку и поговорить о том, что вас беспокоит.')
    with st.expander('Если помощь нужна прямо сейчас'):
        st.write('Если есть непосредственная опасность, обратитесь в местную экстренную службу или к безопасному взрослому рядом. Не ждите ответа в очереди.')
        st.write('В России: детский телефон доверия 8 800 2000 122; с мобильного — 124.')
        st.link_button('О детском телефоне доверия','https://deti.gov.ru/Press-Centr/region-news/24803')
        st.link_button('Службы помощи детям в других странах','https://childhelplineinternational.org/helplines/')
    url=secret('SUPPORT_SUPABASE_URL');key=secret('SUPPORT_SUPABASE_ANON_KEY')
    enabled=secret('SUPPORT_ENABLED','false').lower()=='true'
    if not enabled or not url or not key:
        st.info('Чат с психологами ещё не открыт. Сейчас можно воспользоваться службами помощи по ссылкам выше.')
        return
    privacy=secret('SUPPORT_PRIVACY_URL')
    contact=secret('SUPPORT_CONTACT_URL')
    # The operator must publish real privacy and safeguarding contacts before intake.
    if not privacy.startswith('https://') or not contact.startswith('https://'):
        st.info('Приём обращений пока закрыт. Контакты действующих служб помощи — выше.')
        return
    st.link_button('Как защищается переписка',privacy)
    st.link_button('Связаться с организатором / сообщить о проблеме',contact)
    st.caption('Переписку видит назначенный специалист; технический оператор сервиса имеет административный доступ. Не указывайте адрес, школу, телефон или полное имя. Чат не заменяет экстренную помощь.')
    role=st.radio('Открыть',['Обратиться за помощью','Кабинет психолога'],horizontal=True,key='support_role')
    slot='support_staff_auth' if role=='Кабинет психолога' else 'support_child_auth'
    try:
        api=SupportClient(url,key,st.session_state,slot)
        if role=='Кабинет психолога':
            if not st.session_state.get(slot):
                with st.form('support_login',clear_on_submit=True):
                    email=st.text_input('Email специалиста')
                    password=st.text_input('Пароль',type='password')
                    submit=st.form_submit_button('Войти')
                if submit:
                    api.auth('token?grant_type=password',{'email':email,'password':password})
                    if not api.rpc('support_is_staff'):
                        st.session_state.pop(slot,None)
                        st.error('Доступ специалиста ещё не подтверждён организатором.')
                    else: st.rerun()
                return
            if not api.rpc('support_is_staff'):
                st.session_state.pop(slot,None);st.error('Доступ специалиста закрыт.');return
            available=st.checkbox('Я на связи и могу принимать обращения',key='support_available')
            if st.button('Выйти из кабинета'):
                api.rpc('support_heartbeat',{'is_available':False})
                st.session_state.pop(slot,None);st.rerun()
            auto_claim=st.checkbox('Автоматически принимать следующее обращение, пока я на связи',value=True,key='support_auto_claim')
            @st.fragment(run_every='20s')
            def staff_panel():
                try:
                    api.rpc('support_heartbeat',{'is_available':available})
                    tickets=api.request('GET','support_tickets',params={'status':'eq.active','staff_id':'eq.'+api.uid(),'select':'*'})
                    if not tickets and available and auto_claim:
                        claimed=api.rpc('support_claim_next')
                        if claimed:
                            tickets=api.request('GET','support_tickets',params={'id':'eq.'+claimed,'select':'*'})
                    if not tickets:
                        st.info('Открытой беседы нет. Можно принять самое раннее обращение на одном из ваших языков.')
                        if st.button('Принять следующее обращение',disabled=not available,key='support_claim'):
                            claimed=api.rpc('support_claim_next')
                            if claimed: st.rerun()
                            else: st.info('Сейчас в очереди нет подходящих обращений.')
                    else: chat(st,api,tickets[0],True)
                except SupportError as e: st.error(str(e))
            staff_panel()
        else:
            @st.fragment(run_every='20s')
            def learner_panel():
                try:
                    presence=api.rpc('support_presence') or []
                    online=[x for x in presence if x['state']=='online']
                    st.subheader('Специалисты')
                    if not presence: st.info('Специалисты пока не подключены.')
                    for person in presence:
                        label={'online':'🟢 Свободен','busy':'🟠 В беседе','offline':'⚪ Не в сети'}[person['state']]
                        st.write(person['display_name']+' — '+label+' · '+', '.join(person['languages']))
                    tickets=[]
                    if api.uid():
                        tickets=api.request('GET','support_tickets',params={'learner_id':'eq.'+api.uid(),'status':'in.(waiting,active)','select':'*','order':'created_at.desc','limit':'1'})
                    if tickets:
                        chat(st,api,tickets[0],False)
                        return
                    if not online:
                        st.info('Сейчас нет свободного специалиста. Можно воспользоваться службами помощи выше или вернуться позже. Заявка ещё не отправлена.')
                        return
                    languages=sorted({lang for person in online for lang in person['languages']})
                    with st.form('support_new',clear_on_submit=True):
                        language=st.selectbox('Язык беседы',languages)
                        message=st.text_area('Что вас беспокоит?',max_chars=2000)
                        consent=st.checkbox('Я прочитал(а), кто видит переписку и как она хранится.')
                        st.caption('После обновления вкладки доступ к анонимной беседе может потеряться. Ответ не гарантируется мгновенно.')
                        send=st.form_submit_button('Обратиться к свободному психологу')
                    if send:
                        if not consent or not message.strip():
                            st.warning('Нужно описание вопроса и согласие с условиями переписки.');return
                        if not api.uid(): api.auth('signup',{})
                        ticket=api.rpc('support_create_ticket',{'lang':language,'first_message':message.strip()})
                        if ticket:
                            st.success('Обращение передано в очередь. Ожидаем, пока специалист примет его.');st.rerun()
                except SupportError as e: st.error(str(e))
            learner_panel()
    except SupportError as e: st.error(str(e))

def chat(st,api,ticket,staff):
    st.subheader('Беседа с психологом' if not staff else 'Текущая беседа')
    st.caption('Ожидаем специалиста' if ticket['status']=='waiting' else 'Специалист принял обращение')
    messages=api.request('GET','support_messages',params={'ticket_id':'eq.'+ticket['id'],'select':'author_id,body,created_at','order':'created_at.desc','limit':'200'})
    for m in reversed(messages or []):
        mine=m['author_id']==api.uid()
        with st.chat_message('user' if mine else 'assistant'):
            st.caption('Вы' if mine else ('Ученик' if staff else 'Психолог'))
            st.write(m['body'])
    with st.form('support_chat_'+ticket['id'],clear_on_submit=True):
        message=st.text_area('Сообщение',max_chars=2000)
        send=st.form_submit_button('Отправить')
    if send and message.strip():
        api.rpc('support_send',{'ticket':ticket['id'],'message':message.strip()});st.rerun()
    if not staff and ticket['status']=='active':
        if st.button('Специалист не отвечает — вернуться в очередь',key='support_requeue'):
            api.rpc('support_requeue',{'ticket':ticket['id']});st.rerun()
        st.caption('Возврат доступен, если специалист вышел из сети. Если помощь срочная, используйте контакты вверху страницы.')
    if st.button('Завершить беседу',key='support_close'):
        api.rpc('support_close',{'ticket':ticket['id']});st.rerun()
