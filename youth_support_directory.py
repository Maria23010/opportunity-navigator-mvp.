"""Curated external support services, no personal data transmission and no diagnosis.

Verified sources and review date are stored in youth_help_resources.json.
Phone numbers are generally intended for calls placed within the listed country.
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).with_name('youth_help_resources.json')

COUNTRY_CODES = {
    'Australia': ('Австралия','أستراليا'),
    'Azerbaijan': ('Азербайджан','أذربيجان'),
    'Brunei': ('Бруней','بروناي'),
    'United Kingdom': ('Великобритания','المملكة المتحدة'),
    'Hungary': ('Венгрия','المجر'),
    'Hong Kong (China)': ('Гонконг','هونغ كونغ'),
    'Italy': ('Италия','إيطاليا'),
    'Canada': ('Канада','كندا'),
    'Qatar': ('Катар','قطر'),
    'China': ('Китай','الصين'),
    'Russia': ('Россия','روسيا'),
    'Romania': ('Румыния','رومانيا'),
    'Singapore': ('Сингапур','سنغافورة'),
    'United States': ('США','الولايات المتحدة'),
    'Türkiye': ('Турция','تركيا'),
    'South Korea': ('Южная Корея','كوريا الجنوبية'),
    'Japan': ('Япония','اليابان'),
    'United Arab Emirates': ('ОАЭ','الإمارات العربية المتحدة'),
    'Kazakhstan': ('Казахстан','كازاخستان'),
}


def load_directory():
    return json.loads(DATA_PATH.read_text(encoding='utf-8'))


def recommended_services(country, age=None, include_other_ages=False):
    resources = [r for r in load_directory()['resources'] if r['country'] == country]
    if age is None or include_other_ages:
        return resources
    try:
        age = int(age)
    except (TypeError, ValueError):
        return resources
    return [r for r in resources if r['min_age'] <= age <= r['max_age']]


def render_directory(st, lang='ru', initial_country='Global / not specified', initial_age=15, translate=None):
    """Display country- and age-appropriate outbound links, independent of chat backend."""
    info = load_directory()
    def L(en, ru, ar=None):
        if lang == 'ru': return ru
        if lang == 'en': return en
        if lang == 'ar' and ar: return ar
        if callable(translate):
            result = translate(en, lang)
            return result if isinstance(result, str) and result.strip() else en
        return en
    st.subheader(L('Find real support in your country', 'Найдите настоящую помощь в вашей стране', 'اعثر على دعم حقيقي في بلدك'))
    st.write(L(
        'Choose a country and age. These links open independent organizations; this platform does not provide therapy or send messages to them.',
        'Выберите страну и возраст. Ссылки ведут в независимые организации: сама платформа не проводит психотерапию и не отправляет им сообщения.',
        'اختر البلد والعمر. الروابط تؤدي إلى جهات مستقلة، والمنصة لا تقدم العلاج أو ترسل الرسائل نيابة عنك.'
    ))
    choices = ['Global / not specified'] + sorted(COUNTRY_CODES)
    current = initial_country if initial_country in choices else choices[0]
    def country_display(code):
        if code == 'Global / not specified':
            return L('Choose country', 'Выберите страну', 'اختر البلد')
        if lang == 'ru': return COUNTRY_CODES[code][0]
        if lang == 'ar': return COUNTRY_CODES[code][1]
        if lang == 'en': return code
        return translate(code, lang) if callable(translate) else code
    c1, c2 = st.columns([3, 1])
    with c1:
        country = st.selectbox(L('Country', 'Страна', 'البلد'), choices, index=choices.index(current),
                               format_func=country_display, key='youth_help_country')
    with c2:
        age = st.number_input(L('Age', 'Возраст', 'العمر'), min_value=5, max_value=29, value=max(5, min(29, int(initial_age or 15))), step=1, key='youth_help_age')
    st.info(L(
        'If you are in immediate danger, call your local emergency services now and tell a trusted adult nearby. Do not wait for a web reply.',
        'Если есть непосредственная опасность, сейчас обратитесь в местную экстренную службу и к взрослому, которому доверяете. Не ждите ответа на сайте.',
        'إذا كنت في خطر فوري، اتصل بالطوارئ المحلية وأخبر شخصاً بالغاً تثق به. لا تنتظر رداً عبر الإنترنت.'
    ))
    if country == choices[0]:
        st.write(L('Select a country to see available services.', 'Выберите страну, чтобы увидеть подходящие службы.', 'اختر بلداً لعرض خدمات الدعم.'))
        rows = []
    else:
        rows = recommended_services(country, age)
        if not rows:
            st.warning(L(
                'We do not yet have a verified age-matched service for this country. Use the international directory below; this does not mean there is no help.',
                'В базе пока нет проверенной службы для этого возраста и страны. Воспользуйтесь международным справочником ниже: это не означает отсутствия помощи.',
                'لا توجد لدينا خدمة موثقة لهذا العمر في هذا البلد بعد. استخدم الدليل الدولي أدناه.'
            ))
    for i, r in enumerate(rows):
        with st.container(border=True):
            st.markdown('**' + r['name'] + '**')
            description = r['details_ru'] if lang == 'ru' else r['details_en']
            if lang not in ('ru', 'en') and callable(translate):
                description = translate(description, lang)
            st.write(description)
            st.caption(L('Who: ages', 'Возраст:', 'العمر:') + f" {r['min_age']}–{r['max_age']} · " +
                       L('Hours', 'Часы', 'الساعات') + ': ' + r['hours'])
            if r.get('phone'):
                st.write(L('Phone / text:', 'Телефон / сообщения:', 'الهاتف / الرسائل:') + ' **' + r['phone'] + '**')
            st.link_button(L('Open official website', 'Открыть официальный сайт', 'افتح الموقع الرسمي'),
                           r['url'])
            if r['kind'] == 'safeguarding':
                st.caption(L('Mainly child protection and safeguarding, not a general therapy service.',
                             'Основное направление — защита ребёнка, а не общая психотерапия.',
                             'الخدمة مخصصة أساساً لحماية الأطفال وليس للعلاج النفسي العام.'))
    st.markdown('**' + L('More countries', 'Другие страны', 'بلدان أخرى') + '**')
    st.write(L('Find a child helpline by country at Child Helpline International. Local age limits, languages and operating hours vary.',
               'Справочник Child Helpline International позволяет найти детскую линию по стране. Возрастные ограничения, языки и график работы отличаются.',
               'ابحث عن خط مساعدة الأطفال حسب البلد. تختلف الأعمار واللغات وساعات العمل.'))
    st.link_button(L('International helpline directory', 'Международный справочник помощи', 'الدليل الدولي لخطوط المساعدة'),
                   info['international_directory'])
    st.caption(L('Numbers may work only inside the listed country. Check the official site before calling. Directory reviewed:',
                 'Номера могут работать только внутри соответствующей страны. Перед обращением уточните информацию на сайте. Проверено:',
                 'قد تعمل الأرقام داخل البلد فقط. تحقق من الموقع الرسمي. تاريخ المراجعة:') + ' ' + info['reviewed_at'])
