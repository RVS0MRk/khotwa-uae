"""Fictional, curated rehearsal scenario. No interviews, sales or AI calls.

This adapter is used only by demo_server.py; production app:app never imports it.
Numbers below are explicit illustrative assumptions, not prices or quotations.
"""
from copy import deepcopy

SCENARIO = {
    'en': {
        'idea': 'Satr: bilingual digital menu layouts for small cafes near Abu Dhabi University',
        'skills': 'Arabic and English writing, basic graphic design',
        'interests': 'Helping independent cafes communicate clearly',
        'experience': 'Student design projects; no customer interviews yet',
        'time_available': 'Six hours per week',
    },
    'ar': {
        'idea': 'سطر: تصميم قوائم طعام رقمية بالعربية والإنجليزية للمقاهي الصغيرة قرب جامعة أبوظبي',
        'skills': 'الكتابة بالعربية والإنجليزية والتصميم الأساسي',
        'interests': 'مساعدة المقاهي المستقلة على التواصل بوضوح',
        'experience': 'مشروعات تصميم دراسية؛ لا توجد مقابلات عملاء بعد',
        'time_available': 'ست ساعات أسبوعيا',
    },
    'common': {'budget': 6000, 'category': 'Technology & Digital', 'region': 'Abu Dhabi', 'context': 'B2B', 'user_type': 'small_businesses'},
    'disclosure': 'SIMULATED DEMO DATA. No real AI generation, customer research, orders, quotes or payments.',
}

# The existing finance engine computes all outputs. No result is invented.
FINANCE = dict(equipment='1200', initial_software='250', initial_marketing='350', other_startup='450', licensing='300',
               working_capital='1500', contingency='250', contingency_mode='aed', available_capital='6000',
               price='85', units='80', variable_cost='32', fixed_cost='2100', cogs_per_unit='20',
               cash_collections='6800', cash_operating_outflow='4660')


def plan(language='en', bilingual=True):
    ar = language == 'ar'
    def t(en, arabic):
        return arabic if ar else en
    name = t('Satr', 'سطر')
    segment = t('Independent cafe owners near Abu Dhabi University', 'أصحاب المقاهي المستقلة قرب جامعة أبوظبي')
    first = t('Sketch a bilingual menu sample today, then ask five nearby cafe owners how they update menus; record objections without selling.',
              'ارسم اليوم نموذجا لقائمة طعام باللغتين، ثم اسأل خمسة أصحاب مقاه قريبة عن تحديث القوائم؛ سجل الاعتراضات دون بيع.')
    rows = [
        ('Define one segment', 'حدد شريحة واحدة', 'Describe nearby independent cafes and their current menu alternative.', 'صف المقاهي المستقلة القريبة والبديل الحالي لقوائم الطعام.'),
        ('Interview before spending', 'قابل العملاء قبل الإنفاق', 'Ask five cafe owners about the last menu change and its difficulties.', 'اسأل خمسة أصحاب مقاه عن آخر تحديث للقائمة والصعوبات المرتبطة به.'),
        ('Sketch the concept', 'ارسم الفكرة', 'Prototype a bilingual paper menu and ask about readability without selling.', 'ارسم نموذجا ورقيا باللغتين واسأل عن وضوحه دون بيع.'),
        ('Test stated interest', 'اختبر الاهتمام المعلن', 'Invite voluntary no-payment interest and record objections honestly.', 'اجمع اهتماما طوعيا بلا دفع وسجل الاعتراضات بأمانة.'),
        ('Compare assumptions', 'قارن الافتراضات', 'Review time, software and printing assumptions before making commitments.', 'راجع افتراضات الوقت والبرامج والطباعة قبل الالتزام.'),
        ('Verify requirements', 'تحقق من المتطلبات', 'Check official activity requirements before operating or accepting payment.', 'تحقق من متطلبات النشاط الرسمية قبل التشغيل أو قبول الدفع.'),
        ('Choose the next experiment', 'اختر التجربة التالية', 'Decide whether to continue, adjust or stop using recorded observations and remaining gaps.', 'قرر الاستمرار أو التعديل أو التوقف وفقا للملاحظات المسجلة والفجوات المتبقية.'),
    ]
    reasons = [
        ('Nearby cafes may be reachable within the illustrative six-hour weekly schedule.', 'قد تكون المقاهي القريبة مناسبة للوقت التوضيحي المتاح وهو ست ساعات أسبوعيا.'),
        ('Cafe owners may need clearer bilingual menus; their willingness to change is unknown.', 'قد يحتاج أصحاب المقاهي إلى قوائم أوضح باللغتين؛ لا نعرف إن كانوا سيغيرون البديل الحالي.'),
        ('A paper concept may fit the stated budget, but actual software and approval costs need checking.', 'قد يلائم النموذج الورقي الميزانية المذكورة، لكن تكاليف البرامج والمتطلبات الفعلية تحتاج إلى تحقق.'),
        ('Sketching a sample can use the stated writing and design skills before spending.', 'يمكن رسم نموذج بالاعتماد على مهارات الكتابة والتصميم المذكورة قبل الإنفاق.'),
        ('Repeatable templates may help later, but workload and demand remain uncertain.', 'قد تساعد القوالب القابلة للتكرار لاحقا، لكن حجم العمل والطلب غير مؤكدين.'),
    ]
    dimensions = ('local_fit', 'clear_customer', 'low_starting_cost', 'easy_first_step', 'growth_potential')
    scores = (4, 2, 4, 4, 3)
    risk_names = [('Customer demand','طلب العملاء'),('Time capacity','الوقت المتاح'),('Cost assumptions','افتراضات التكلفة'),('Official requirements','المتطلبات الرسمية'),('Competition','المنافسة')]
    out = {
        'business_name_suggestion': name,
        'summary': t('Demonstration hypothesis: small cafes may need clearer bilingual digital menu layouts.', 'فرضية توضيحية: قد تحتاج المقاهي الصغيرة إلى قوائم طعام رقمية أوضح باللغتين.'),
        'idea_overview': {
            'problem': t('Cafe owners may find bilingual menu updates time-consuming; no customer interviews have been conducted for this scenario.', 'قد يجد أصحاب المقاهي تحديث القوائم باللغتين مستهلكا للوقت؛ لم تجر مقابلات عملاء لهذا السيناريو.'),
            'target_user': segment,
            'solution': t('Test a bilingual menu layout concept through paper samples and voluntary interviews.', 'اختبر فكرة تصميم قوائم باللغتين من خلال نماذج ورقية ومقابلات طوعية.'),
            'impact': t('Potential clarity benefit to test; no measured customer result.', 'منفعة محتملة في الوضوح للاختبار؛ لا توجد نتيجة مقاسة للعملاء.'),
            'evidence': t('No genuine customer research: this is simulated rehearsal data.', 'لا توجد أبحاث عملاء حقيقية؛ هذه بيانات تدريب محاكاة.'),
            'why_market': t('The proposed nearby segment may fit the stated language skills and limited weekly time.', 'قد تلائم الشريحة القريبة المقترحة المهارات اللغوية والوقت الأسبوعي المحدود.'),
        },
        'first_step_today': first, 'suggested_test_price_aed': 85,
        'opportunity_score': {d: {'score': s, 'reason': t(*r), 'improve': t('Interview the proposed cafe segment to check this assumption.', 'قابل شريحة المقاهي المقترحة للتحقق من هذا الافتراض.')} for d,s,r in zip(dimensions,scores,reasons)},
        'small_test_plan': {'intro': t('Test a paper concept before spending or selling.', 'اختبر نموذجا ورقيا قبل الإنفاق أو البيع.'), 'points': [t(r[2],r[3]) for r in rows[:5]]},
        'do_not_start_with': [t('Avoid paid promotion before checking the message.', 'تجنب الترويج المدفوع قبل اختبار الرسالة.')],
        'instead_do': [t('Interview cafe owners about their existing alternatives.', 'قابل أصحاب المقاهي حول بدائلهم الحالية.')],
        'seven_day_plan': [{'day': i+1, 'focus': t(r[0],r[1]), 'action': t(r[2],r[3]),
                           'output': t('Proposed experiment notes, not verified evidence.', 'ملاحظات تجربة مقترحة وليست أدلة مستقلة التحقق.'),
                           'time_needed': t('30–60 minutes, illustrative estimate', '٣٠–٦٠ دقيقة، تقدير توضيحي'),
                           'success_check': t('Record responses and gaps without assuming success.', 'سجل الردود والفجوات دون افتراض النجاح.')} for i,r in enumerate(rows)],
        'validation_before_spending': [t(r[2],r[3]) for r in rows[:4]],
        'validation_questions': [t('How did you update your menu last time?', 'كيف حدثت قائمة الطعام في المرة الأخيرة؟'),
                                 t('Which bilingual layout problems occurred?', 'ما مشكلات التصميم باللغتين التي واجهتك؟'),
                                 t('What alternative do you use now?', 'ما البديل الذي تستخدمه الآن؟'),
                                 t('Would you review a paper concept without payment?', 'هل تراجع نموذجا ورقيا دون دفع؟'),
                                 t('What would stop you from changing your current approach?', 'ما الذي قد يمنعك من تغيير طريقتك الحالية؟')],
        'whatsapp_message': t('Hi, I am exploring a bilingual menu concept. May I ask about your current menu process? This is research, not a sale.', 'مرحبا، أستكشف فكرة قوائم باللغتين. هل أسأل عن طريقتك الحالية؟ هذه مقابلة بحثية وليست بيعا.'),
        'readiness_report': {'target_customer': segment, 'best_first_action': first, 'estimated_first_test_cost_aed': 0,
                             'what_not_to_start_with': t('Avoid irreversible spending.', 'تجنب الإنفاق غير القابل للاسترجاع.'),
                             'main_risk': t('Demand is untested.', 'الطلب غير مختبر.'),
                             'first_customer_channel': t('Ask nearby cafe owners for voluntary interviews.', 'اسأل أصحاب المقاهي القريبة عن مقابلات طوعية.'), 'next_step': first},
        'decision_engine': {'decision': t('Validate more','تحقق أكثر'), 'reason': t('No customer evidence exists for this fictional scenario.', 'لا توجد أدلة عملاء لهذا السيناريو الخيالي.'), 'next_test_action': first, 'risk_level':'Medium', 'recommended_test_budget_aed':0},
        'customer_personas': [{'name': t('Independent cafe owners', 'أصحاب المقاهي المستقلة'),
                               'cares_about': t('Cafe owners may care about readable Arabic and English menus.', 'قد يهتم أصحاب المقاهي بوضوح القوائم بالعربية والإنجليزية.'),
                               'reach_through': t('Ask nearby independent cafe owners for voluntary introductions.', 'اسأل أصحاب المقاهي المستقلة القريبة عن تعارف طوعي.'),
                               'ask': t('What made your last menu update difficult?', 'ما الذي صعب آخر تحديث لقائمة الطعام؟')}],
        'risk_radar': [{'name':t(*r), 'level':'Medium', 'reason': t('This assumption remains unverified in the fictional scenario.', 'يبقى هذا الافتراض غير مؤكد في السيناريو الخيالي.'), 'fix':t('Check this assumption with the proposed segment before spending.', 'تحقق من هذا الافتراض مع الشريحة المقترحة قبل الإنفاق.')} for r in risk_names],
        'pitches': {'ten_sec':t('Could clearer bilingual menu layouts help your cafe? I am testing a concept.', 'هل قد تساعد قوائم أوضح باللغتين مقهاك؟ أختبر فكرة أولية.'),
                    'thirty_sec':t('I am exploring Arabic and English menu layouts for nearby independent cafes. Could we discuss your last menu update without a sales commitment?', 'أستكشف تصميم قوائم بالعربية والإنجليزية للمقاهي المستقلة القريبة. هل نناقش آخر تحديث لقائمتك دون التزام بالشراء؟'),
                    'whatsapp':t('May I ask about your current bilingual menu process? This is research without payment.', 'هل أسأل عن طريقتك الحالية لقوائم الطعام باللغتين؟ هذا بحث بلا دفع.'),
                    'instagram':t('Proposed bilingual menu concept: research before launch.', 'فكرة مقترحة لقوائم باللغتين: بحث قبل الإطلاق.')},
        'founder_passport': {'status':t('Unvalidated hypothesis','فرضية غير متحققة'), 'first_action':first, 'next_step':first},
        'steps': [{'step_number':i+1, 'action':t(r[2],r[3]), 'description':t(r[2],r[3]), 'estimated_cost_aed':0 if i<4 else None, 'timeline_days':1,
                   'who_to_contact':t('Voluntary cafe participants','مشاركون طوعيون من المقاهي'), 'location':t('Abu Dhabi','أبوظبي')} for i,r in enumerate(rows)],
        'total_estimated_cost_aed':None, 'total_timeline_days':7, 'first_customer_tip':t('Ask a nearby cafe owner for a voluntary interview.', 'اسأل صاحب مقهى قريب عن مقابلة طوعية.'),
    }
    if bilingual:
        paths = {'summary':'summary','problem':'idea_overview.problem','target_user':'idea_overview.target_user','solution':'idea_overview.solution',
                 'why_market':'idea_overview.why_market','first_customer_channel':'readiness_report.first_customer_channel','target_customer':'readiness_report.target_customer'}
        out['bilingual_text'] = {}
        for code in ('en','ar'):
            translated = plan(code, False)
            values = {}
            for key, path in paths.items():
                value = translated
                for bit in path.split('.'):
                    value = value[bit]
                values[key] = value
            for d in dimensions:
                for key in ('reason','improve'):
                    values[d+'_'+key] = translated['opportunity_score'][d][key]
            out['bilingual_text'][code] = values
    return out


def ideas(language='en'):
    ar = language == 'ar'
    names = ['سطر', 'حرف', 'موعد'] if ar else ['Satr', 'Harf', 'Mawid']
    fits = ['قد يلائم تصميم قوائم باللغتين مهارات الكتابة والتصميم المذكورة.', 'قد يلائم تصميم السير الذاتية باللغتين مهارات الكتابة المذكورة.', 'قد يلائم رسم صفحات حجز ورقية مهارات التصميم المذكورة.'] if ar else ['Bilingual menu design may fit the stated writing and design skills.', 'Bilingual CV layout may fit the stated writing skills.', 'Paper booking-page design may fit the stated design skills.']
    return {'ideas':[{'name': n, 'fit': fits[i],
                       'customer': 'أصحاب المقاهي القريبة' if i==0 and ar else 'Nearby cafe owners' if i==0 else 'شريحة محتملة تحتاج إلى مقابلات' if ar else 'A potential segment needing interviews',
                       'first_test':'اسأل خمسة مشاركين محتملين عن البديل الحالي دون بيع.' if ar else 'Ask five potential participants about their current alternative without selling.',
                       'assumption':'فرضية توضيحية غير مختبرة؛ لا توجد أبحاث عملاء حقيقية.' if ar else 'Untested demonstration hypothesis; no genuine customer research.',
                       'category':'Technology & Digital'} for i,n in enumerate(names)]}


def answer(language='en'):
    ar = language == 'ar'
    return {'title':'مستشار التدريب المحاكى' if ar else 'Simulated rehearsal Advisor',
            'summary':'اسأل أصحاب المقاهي عن آخر تحديث للقائمة قبل عرض النموذج؛ هذه إجابة محاكاة وليست ذكاء اصطناعيا حيا.' if ar else 'Ask cafe owners about their last menu update before showing the sample; this is a simulated reply, not live AI.',
            'points':[{'title':'سؤال المقابلة' if ar else 'Interview question', 'text':'ما أصعب جزء في تحديث القائمة باللغتين؟' if ar else 'What was hardest about updating the menu in both languages?'}],
            'next_action':plan(language,False)['first_step_today'],
            'caution':'سجل الملاحظات الحقيقية فقط؛ لا تعتبر بيانات التدريب أبحاث عملاء.' if ar else 'Record only genuine observations; rehearsal data is not customer research.'}
