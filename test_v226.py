"""Fixed independent V2.2.6 acceptance tables; transport is always mocked."""
from copy import deepcopy
from html import escape
import io
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

from test_support import configure_mock_environment
configure_mock_environment()
import app
import material_claims as gate
import provenance
import publication_policy as policy
from content_safety import export_plan, safe_text
from input_options import CHOICES, ARABIC, DEFAULTS, RISK, sanitize_export_display
from scoring import DIMENSIONS
from test_finance import BASE
from test_v22_content import fixture
from pypdf import PdfReader

ROOT = Path(__file__).parent
CASES = json.loads((ROOT / 'tests/fixtures/v226_cases.json').read_text(encoding='utf-8'))
IMPERATIVE = re.compile(r'^(?:ask|message|provide|conduct|leverage|capture|estimate|interview|test|compare|record|review|check|verify|define|identify|describe|map|draft|create|collect|contact|write|prepare|research|list|analyse|analyze|decide|avoid|use|share|send|track|confirm|choose|document|explore|find|plan|approach|meet|present|gather|outline|explain|اسأل|قابل|اختبر|قارن|سجل|راجع|تحقق|حدد|اكتب|اجمع|تواصل|ابحث|خطط|ابدأ|قدم)(?:\b|\s)', re.I)
HYPOTHESIS = re.compile(r'\b(?:may|might|could|likely|assum\w*)\b|(?<!\w)(?:قد|ربما|افتراض\w*)(?!\w)', re.I)


def plausible(items, key):
    """The requested three-label mock; never calls the policy under test."""
    return {i['id']: ('planning' if IMPERATIVE.search(i['text']) or i['text'].endswith(('?', '؟')) else
                      'hypothesis' if HYPOTHESIS.search(i['text']) else 'noun_phrase') for i in items}


def get_path(data, path):
    for part in path.split('.'):
        data = data[int(part)] if isinstance(data, list) else data[part]
    return data


def put(data, path, value):
    owner = data
    parts = path.split('.')
    for part in parts[:-1]:
        owner = owner[int(part)] if isinstance(owner, list) else owner[part]
    owner[int(parts[-1]) if isinstance(owner, list) else parts[-1]] = value


MIXED = {
    'ar': 'هل يدفع مديرو أسطول Deliveroo مبلغ AED 1,250 شهرياً لاختبار خدمة خطوة المقترحة (مع Careem)؟ نحتاج إلى مقارنة الافتراض مع البديل الحالي ومقابلة مديرين قبل أي التزام، مع فحص خيارات QuickLane وCityFleet ومواعيد العمل المناسبة.',
    'en': 'Would Deliveroo managers pay AED 1,250 monthly to test خطوة with Careem? Compare the proposed approach with دراجتي and the current alternative (including dispatch timing), and interview coordinators before any commitment to a commercial trial.',
}


class V226Tests(unittest.TestCase):
    def setUp(self):
        transport = patch('requests.post', side_effect=AssertionError('Live provider forbidden'))
        transport.start(); self.addCleanup(transport.stop)
        classifier = patch.object(gate, 'classify', side_effect=plausible)
        classifier.start(); self.addCleanup(classifier.stop)
        self.client = app.app.test_client()

    def generate(self, raw=None, lang='en', idea=None):
        raw = deepcopy(raw or fixture('rich_plan_en'))
        body = {'idea': idea if idea is not None else raw.get('summary') or 'Proposed mobile workshop', 'region': 'Abu Dhabi', 'budget': 10000, 'lang': lang}
        with patch.object(app, 'call_groq', return_value=json.dumps(raw, ensure_ascii=False)):
            response = self.client.post('/generate', json=body)
        self.assertEqual(response.status_code, 200)
        return response.json

    def test_four_review_plans_retain_eighty_percent_and_all_score_dimensions(self):
        for name in ('v226_rich_lunch', 'v224_live_lunch', 'v224_live_lunch_ar', 'v224_live_packaging'):
            with self.subTest(fixture=name):
                raw = fixture(name); lang = 'ar' if name.endswith('_ar') else 'en'
                result = self.generate(raw, lang)
                excluded = set(CASES['excluded_retention_paths'][name])
                original = [(p,t) for p,t in gate.prose_items(raw) if p not in excluded]
                retained = {t for p,t in gate.prose_items(result)}
                self.assertGreaterEqual(sum(t in retained for p,t in original) / len(original), .8)
                self.assertEqual(result['opportunity_score']['assessed_count'], 5)
                self.assertEqual(result['opportunity_score']['total'], sum(raw['opportunity_score'][k]['score'] for k in DIMENSIONS))
                for key in ('problem', 'solution'):
                    self.assertEqual(result['idea_overview'][key], raw['idea_overview'][key])
                for key in DIMENSIONS:
                    self.assertEqual(result['opportunity_score'][key]['reason'], raw['opportunity_score'][key]['reason'])

    def test_complete_sentences_survive_without_manufactured_tails(self):
        good = fixture('v226_rich_lunch')['first_step_today']
        result, _ = gate.verify_model({'summary':good}, {}, 'en', 'synthetic')
        self.assertEqual(result['summary'], good)
        for lang, bad in (('en', CASES['review_unsafe']['en'][-1]),
                          ('ar', 'مرسى، مربحة منذ الإطلاق، تخطط لإضافة مركبة ثانية.')):
            result, _ = gate.verify_model({'summary':bad}, {}, lang, 'synthetic')
            self.assertEqual(result['summary'], '')
        safe = 'Interview nearby riders about current repair alternatives.'
        text = safe + ' HarborLoop earned AED 9000 yesterday. Compare their alternatives.'
        result, _ = gate.verify_model({'summary':text}, {}, 'en', 'synthetic')
        self.assertEqual(result['summary'], safe + ' Compare their alternatives.')
        self.assertNotRegex(result['summary'], r'^(?:[a-z]|and\b|whether\b|but\b)')

    def test_independent_claims_under_five_wrong_labels(self):
        for lang in ('en', 'ar'):
            self.assertGreaterEqual(len(CASES['independent_unsafe'][lang]), 30)
            for label in ('planning', 'hypothesis', 'negation', 'user_attributed', 'noun_phrase'):
                survivors = []
                for text in CASES['independent_unsafe'][lang] + CASES['review_unsafe'][lang]:
                    with patch.object(gate, 'classify', side_effect=lambda items,key:{i['id']:label for i in items}):
                        clean, _ = gate.verify_model({'summary':text, 'title':text, 'pitches':{'ten_sec':text}}, {'idea':'Proposed local workshop'}, lang, 'synthetic')
                    if text in json.dumps(clean, ensure_ascii=False): survivors.append(text)
                # Stronger than the permitted <=10% for noun_phrase.
                self.assertEqual(survivors, [], (lang,label,survivors))

    def test_claims_cannot_reach_any_ai_route_or_authenticated_export(self):
        for lang in ('en','ar'):
            for bad in CASES['independent_unsafe'][lang]:
                with self.subTest(lang=lang,claim=bad):
                    raw = fixture('rich_plan_' + lang)
                    raw['summary'] = bad; raw['first_step_today'] = bad
                    raw['pitches'] = {k:bad for k in raw['pitches']}
                    raw['opportunity_score']['local_fit']['reason'] = bad
                    p = self.generate(raw,lang,idea='Proposed local bicycle repair service / خدمة صيانة دراجات مقترحة')
                    self.assertNotIn(bad,json.dumps(p,ensure_ascii=False))
                    self.assertIsNone(p['opportunity_score']['local_fit']['score'])
                    self.assertNotIn(bad,json.dumps(export_plan(p),ensure_ascii=False))
                    self.assertIsNotNone(provenance.verified_receipt(p))
                    models = [('/ask',{'question':'Suggest a research step','lang':lang},
                               {'title':bad,'summary':bad,'points':[{'title':bad,'text':bad}],'next_action':bad,'caution':''}),
                              ('/discover',{'skills':'Repair research','lang':lang,'budget':10000},
                               {'ideas':[dict(name=bad,fit=bad,customer=bad,first_test=bad,assumption=bad,category='Services & Maintenance') for _ in range(3)]})]
                    for endpoint,body,model in models:
                        with patch.object(app,'call_groq',return_value=json.dumps(model,ensure_ascii=False)):
                            r = self.client.post(endpoint,json=body)
                        self.assertEqual(r.status_code,200)
                        self.assertNotIn(bad,json.dumps(r.json,ensure_ascii=False))

    def test_legitimate_denials_actions_and_hypotheses_remain_intact(self):
        for lang in ('en','ar'):
            kept = 0
            for text in CASES['safe'][lang]:
                clean, _ = gate.verify_model({'summary':text}, {}, lang, 'synthetic')
                kept += clean['summary'] == text
                self.assertEqual(clean['summary'],text,(lang,text))
                self.assertEqual(safe_text(text,lang),text,(lang,text))
            self.assertGreaterEqual(kept/len(CASES['safe'][lang]),.9)

    def test_timeout_keeps_nonclaim_plan_but_never_claims_or_garbage(self):
        raw = fixture('v226_rich_lunch')
        for verdict in ({}, RuntimeError('synthetic timeout')):
            kwargs = {'side_effect':verdict} if isinstance(verdict,Exception) else {'return_value':verdict}
            with patch.object(gate,'classify',**kwargs):
                clean, meta = gate.verify_model(raw,{},'en','synthetic')
                # Approved outage contract: this identical, unhedged noun-only
                # description in two fields is not an authenticated assertion.
                self.assertEqual(clean['summary'],'')
                self.assertEqual(clean['first_step_today'],raw['first_step_today'])
                self.assertEqual(clean['idea_overview']['solution'],'')
                for bad in CASES['independent_unsafe']['en']:
                    result, _ = gate.verify_model({'summary':bad},{},'en','synthetic')
                    self.assertEqual(result['summary'],'')

    def test_rejected_reason_cannot_be_rescued_by_safe_neighbour_or_proof_alias(self):
        good = 'Founder regularly repairs bicycles near a distribution depot.'
        bad = 'HarborLoop received the operating permit yesterday.'
        for dimension in DIMENSIONS:
            raw = fixture('rich_plan_en')
            raw['opportunity_score'][dimension]['reason'] = good + ' ' + bad
            raw.pop('bilingual_text',None)
            p = self.generate(raw)
            self.assertIsNone(p['opportunity_score'][dimension]['score'])
            self.assertEqual(p['opportunity_score']['assessed_count'],4)
            self.assertIsNone(p['opportunity_score']['total'])
            self.assertEqual(export_plan(p)['opportunity_score']['assessed_count'],4)
            self.assertEqual(p['state']['opportunity_score'],p['opportunity_score'])

    def test_even_valid_signed_text_is_rechecked_without_resigning(self):
        p = self.generate()
        bad = CASES['independent_unsafe']['en'][24]
        p['summary'] = bad
        p['opportunity_score']['local_fit']['reason'] = bad
        provenance.seal(p,provenance.sources({},p))
        receipt = deepcopy(p['_content_receipt'])
        self.assertIsNotNone(provenance.verified_receipt(p))
        cleaned = export_plan(p)
        self.assertNotIn(bad,json.dumps(cleaned))
        self.assertIsNone(cleaned['opportunity_score']['local_fit']['score'])
        self.assertEqual(p['_content_receipt'],receipt)

    def test_qualifiers_are_whole_words_and_do_not_borrow_across_clauses(self):
        self.assertIsNone(gate._QUALIFIED.search('قدرها'))
        for text in CASES['review_unsafe']['ar'][1:5]:
            self.assertTrue(policy.ungrounded_assertion(text),text)
        for word in ('ربيع','طبيعي','مقدار','قدرها'):
            self.assertIsNone(policy._HEDGE.search(policy.normalize(word)),word)
        self.assertEqual(policy.clauses('تقلل وجبات نخلة نفقات الغداء بنسبة 28%.'),['تقلل وجبات نخلة نفقات الغداء بنسبة 28%.'])

    def test_wrapped_lines_inherit_full_paragraph_direction_at_all_widths(self):
        from bidi import algorithm as bidi
        from reportlab.lib.styles import ParagraphStyle
        from pdf_text import Paragraph
        original = bidi.get_embedding_levels
        for lang,text in MIXED.items():
            expected = bidi.get_base_level(text)
            for width in range(150,521,10):
                actual = []
                def spy(value,storage,*args,**kwargs):
                    actual.append(storage['base_level']);return original(value,storage,*args,**kwargs)
                paragraph = Paragraph(escape(text),ParagraphStyle('mixed',fontName='Helvetica',fontSize=10,leading=15))
                with patch.object(bidi,'get_embedding_levels',side_effect=spy):paragraph.wrap(width,10000)
                self.assertTrue(actual,(lang,width))
                self.assertEqual(set(actual),{expected},(lang,width,actual))

    def test_hard_break_labels_have_separate_direction_and_pure_latin_is_unchanged(self):
        from bidi import algorithm as bidi
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import Paragraph as Original
        from pdf_text import Paragraph
        style = ParagraphStyle('mixed',fontName='Helvetica',fontSize=10,leading=15)
        levels = []; original = bidi.get_embedding_levels
        def spy(value,storage,*args,**kwargs):
            levels.append(storage['base_level']);return original(value,storage,*args,**kwargs)
        with patch.object(bidi,'get_embedding_levels',side_effect=spy):
            Paragraph('English label<br/>'+escape(MIXED['ar']),style).wrap(180,10000)
        self.assertEqual(levels[0],0);self.assertEqual(set(levels[1:]),{1})
        text = 'Compare estimated costs and interview time before committing to equipment.'
        a,b = Paragraph(text,style),Original(text,style)
        self.assertEqual(a.wrap(180,10000),b.wrap(180,10000))
        self.assertEqual(a.blPara.lines,b.blPara.lines)

    def test_export_enums_only_accept_app_choices_and_finite_nonnegative_budgets(self):
        for kind in CHOICES:
            for value in CHOICES[kind] | ARABIC[kind]:
                p = {'state':{('customer_type' if kind=='user_type' else kind):value},'_'+kind:value}
                cleaned = sanitize_export_display(deepcopy(p))
                self.assertEqual(cleaned,p)
        for value in ('claim text',-1,True,None,{},[],float('inf'),float('nan')):
            p = {'state':{'user_budget_aed':value},'_budget':value}
            self.assertEqual(sanitize_export_display(p)['_budget'],0)
        self.assertEqual(sanitize_export_display({'_budget':'2500.75'})['_budget'],2500.75)
        for value,target in RISK.items():
            self.assertEqual(sanitize_export_display({'risk_radar':[{'level':value}]})['risk_radar'][0]['level'],target)

    def test_parametrized_injected_display_fields_never_print_in_both_pdf_routes(self):
        paths = ['state.category','state.region','state.context','state.customer_type','state.user_budget_aed',
                 '_category','_region','_context','_user_type','_budget','risk_radar.0.level','decision_engine.risk_level']
        p = self.generate()
        bad = 'Dubai SME fund backing for SpokeFix came through.'
        for path in paths:
            dirty = deepcopy(p);put(dirty,path,bad)
            clean = export_plan(dirty)
            expected = 'Medium' if path.endswith(('level','risk_level')) else 0 if 'budget' in path else DEFAULTS['user_type' if 'customer_type' in path else path.split('.')[-1].removeprefix('_')]
            self.assertEqual(get_path(clean,path),expected)
            for lang in ('en','ar'):
                for endpoint,body in (('/pdf',dict(dirty,_lang=lang)),('/investment/pdf',{'plan':dirty,'finance':{'inputs':BASE},'lang':lang})):
                    with self.subTest(path=path,lang=lang,route=endpoint):
                        response = self.client.post(endpoint,json=body)
                        self.assertEqual(response.status_code,200)
                        reader = PdfReader(io.BytesIO(response.data));text='\n'.join(page.extract_text()for page in reader.pages)
                        self.assertNotIn('SpokeFix',text)
                        self.assertNotIn('\u25a0',text);self.assertNotIn('\ufffd',text)
                        response.close()
        own = deepcopy(p);own['state']['idea']='Founder input retained verbatim.'
        self.assertEqual(export_plan(own)['state']['idea'],own['state']['idea'])

    def test_category_javascript_regressions(self):
        result = subprocess.run(['node',str(ROOT/'tests/v226_category.cjs')],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__ == '__main__': unittest.main()
