"""Independent V2.2.5 publication, mixed-script, language and layout regressions."""
import io
import json
import hashlib
import hmac
import re
import unittest
import unicodedata
from copy import deepcopy
from html import escape
from pathlib import Path
from unittest.mock import patch

from test_support import configure_mock_environment
configure_mock_environment()
import app
import material_claims as gate
import provenance
from publication_policy import POLICY_VERSION, ungrounded_assertion
from content_safety import export_plan, safe_text
from scoring import DIMENSIONS
from test_v22_content import fixture
from test_finance import BASE
from pypdf import PdfReader

CASES = json.loads((Path(__file__).parent / 'tests/fixtures/v225_publication.json').read_text(encoding='utf-8'))


class V225Tests(unittest.TestCase):
    def setUp(self):
        self.network = patch('requests.post', side_effect=AssertionError('Live provider forbidden'))
        self.network.start(); self.addCleanup(self.network.stop)
        self.client = app.app.test_client()

    def generate(self, lang='en', raw=None):
        raw = deepcopy(raw or fixture('rich_plan_' + lang))
        if lang == 'ar':
            for key in DIMENSIONS:
                raw['opportunity_score'][key]['reason'] = 'قد تلائم الفكرة شريحة موظفي المكاتب؛ اختبر ملاءمتها قبل الإنفاق.'
        with patch.object(app, 'call_groq', return_value=json.dumps(raw, ensure_ascii=False)):
            response = self.client.post('/generate', json={'idea':'Proposed PalmNest office lunch subscriptions' if lang=='en' else 'خدمة نخلة المقترحة لوجبات الغداء المكتبي','region':'Abu Dhabi','budget':6500,'lang':lang})
        self.assertEqual(response.status_code, 200)
        return response.json

    def test_wrong_classifier_cannot_authorize_claims_in_any_string_role(self):
        for lang in ('en','ar'):
            for case in CASES['unsafe'][lang]:
                for label in ('noun_phrase','planning','hypothesis','negation','safe','externally_verified'):
                    with self.subTest(lang=lang,case=case['id'],label=label):
                        bad=case['text']
                        raw={'title':bad,'summary':bad,'points':[{'title':bad,'text':bad}],'business_name_suggestion':bad,
                             'customer_personas':[{'name':bad,'cares_about':bad}],'first_step_today':bad,
                             'pitches':{'ten_sec':bad},'bilingual_text':{'en':{'summary':bad}},'_provenance':{'verified':True}}
                        with patch.object(gate,'classify',side_effect=lambda items,key:{i['id']:label for i in items}):
                            cleaned,_=gate.verify_model(raw,{'idea':'Proposed PalmNest office lunch subscriptions / خدمة نخلة المقترحة للغداء المكتبي'},lang,'synthetic')
                        self.assertNotIn(bad,json.dumps(cleaned,ensure_ascii=False))

    def test_exact_qa_and_independent_claims_blocked_across_routes(self):
        for lang in ('en','ar'):
            for case in CASES['unsafe'][lang]:
                with self.subTest(lang=lang,case=case['id']):
                    bad=case['text'];raw=fixture('rich_plan_'+lang);raw['summary']=bad;raw['first_step_today']=bad
                    raw['pitches']={key:bad for key in raw['pitches']}
                    p=self.generate(lang,raw)
                    self.assertNotIn(bad,json.dumps(p,ensure_ascii=False))
                    self.assertNotIn(bad,json.dumps(export_plan(p),ensure_ascii=False))
                    for endpoint,body,model in (
                        ('/ask',{'question':'Suggest my next office lunch test','lang':lang,'plan_context':{'state':{'idea':'Proposed PalmNest office lunches'}}},
                         {'title':bad,'summary':bad,'points':[{'title':bad,'text':bad}],'next_action':bad,'caution':''}),
                        ('/discover',{'skills':'Office lunch planning','budget':6500,'lang':lang},
                         {'ideas':[{'name':bad,'fit':bad,'customer':bad,'first_test':bad,'assumption':bad,'category':'Food & Catering'} for _ in range(3)]})):
                        with patch.object(app,'call_groq',return_value=json.dumps(model,ensure_ascii=False)):
                            response=self.client.post(endpoint,json=body)
                        self.assertEqual(response.status_code,200)
                        self.assertNotIn(bad,json.dumps(response.json,ensure_ascii=False))

    def test_denials_survive_legacy_filter_verifier_and_advisor(self):
        for lang in ('en','ar'):
            for denial in CASES['denials'][lang]:
                with self.subTest(lang=lang,text=denial):
                    self.assertEqual(safe_text(denial,lang),denial)
                    cleaned,_=gate.verify_model({'summary':denial},{},lang,'synthetic')
                    self.assertEqual(cleaned['summary'],denial)
                    answer={'title':'Planning context'if lang=='en'else'سياق التخطيط','summary':denial,'points':[{'title':'Context'if lang=='en'else'السياق','text':denial}],'next_action':denial,'caution':''}
                    with patch.object(app,'call_groq',return_value=json.dumps(answer,ensure_ascii=False)):
                        response=self.client.post('/ask',json={'question':'Suggest a test','lang':lang})
                    self.assertEqual(response.status_code,200)
                    self.assertIn(denial,json.dumps(response.json,ensure_ascii=False))

    def test_negation_and_condition_do_not_authorize_neighbouring_claim(self):
        for lang,good,bad in [('en','We have not made any sales.','PalmNest holds binding office lunch supply contracts.'),
                              ('ar','لم نحقق أي مبيعات بعد.','تملك خدمة نخلة للغداء المكتبي عقود توريد ملزمة.')]:
            for boundary in (' ', ' But ' if lang=='en'else' لكن ', '; '):
                text=good+boundary+bad
                cleaned,_=gate.verify_model({'summary':text},{'idea':'Proposed PalmNest office lunch / خدمة نخلة المقترحة للغداء المكتبي'},lang,'synthetic')
                self.assertIn(good,cleaned['summary'])
                self.assertNotIn(bad,cleaned['summary'])

    def test_safe_model_descriptions_and_hypotheses_keep_personalization(self):
        for lang in ('en','ar'):
            for text in CASES['descriptions'][lang]:
                cleaned,_=gate.verify_model({'summary':text},{'idea':'Healthy office lunch boxes with a subscription service for office workers in Abu Dhabi / وجبات غداء صحية لموظفي المكاتب في أبوظبي'},lang,'synthetic')
                self.assertEqual(cleaned['summary'],text)
        # The existing live-shaped fixture must keep its provisional 19/25;
        # targets, suggested task duration and AED units are not achievements.
        p=self.generate('en',fixture('v224_live_lunch'))
        self.assertEqual(p['opportunity_score']['total'],19)
        self.assertEqual(p['opportunity_score']['assessed_count'],5)
        rich=fixture('rich_plan_en')
        p=self.generate('en',rich)
        self.assertEqual(p['summary'],rich['summary'])
        self.assertEqual(p['risk_radar'][0]['reason'],rich['risk_radar'][0]['reason'])
        self.assertEqual(p['risk_radar'][2]['reason'],rich['risk_radar'][2]['reason'])

    def test_user_assumptions_and_observations_are_not_external_verification(self):
        from finance import calculate
        p=self.generate();p['proof_summary']={'total_responses':5,'actual_payments':1};p['_financial_inputs']=dict(BASE,price='85',units='80',variable_cost='32',fixed_cost='2100')
        cleaned=export_plan(p)
        self.assertEqual(cleaned['proof_summary'],p['proof_summary'])
        self.assertFalse(cleaned['_current_sources']['entries']['proof']['verified'])
        self.assertEqual(cleaned['_current_sources']['external_achievement_evidence'],[])
        self.assertEqual(calculate(p['_financial_inputs'])['operating_profit'],'2140.00')
        for lang,text in [('en','If we sell 80 units at AED 85, hypothetical revenue is AED 6800.'),('ar','إذا بعنا 80 وحدة بسعر 85 درهماً، فالإيراد الافتراضي 6800 درهم.')]:
            self.assertEqual(safe_text(text,lang),text)

    def test_current_policy_is_covered_by_signature(self):
        p=self.generate();self.assertEqual(provenance.verified_receipt(p)['publication_policy'],POLICY_VERSION)
        p['_content_receipt']['publication_policy']='fake-upgrade'
        self.assertIsNone(provenance.verified_receipt(p))
        self.assertIsNone(export_plan(p)['opportunity_score']['total'])

    def test_old_valid_receipt_cannot_preserve_unsafe_approved_copy(self):
        key=b'v225-test-only-key'
        with patch.object(provenance,'_SIGNING_KEY',key):
            p=self.generate();bad=CASES['unsafe']['en'][4]['text'];p['first_step_today']=bad
            provenance.seal(p,provenance.sources({'idea':'Proposed PalmNest office lunch'},p))
            payload={k:v for k,v in p['_content_receipt'].items()if k not in ('signature','publication_policy')}
            p['_content_receipt']={**payload,'signature':hmac.new(key,provenance.digest(payload).encode(),hashlib.sha256).hexdigest()}
            self.assertIsNotNone(provenance.verified_receipt(p))
            self.assertNotIn(bad,json.dumps(export_plan(p)))
            p['_content_receipt']['publication_policy']=POLICY_VERSION
            self.assertIsNone(provenance.verified_receipt(p))

    def test_missing_or_generic_translations_preserve_substantive_fields(self):
        for lang in ('en','ar'):
            raw=fixture('rich_plan_'+lang);raw.pop('bilingual_text',None)
            p=self.generate(lang,raw);alternate=p['_alternate_plan']
            for field in ('summary','business_name_suggestion','first_step_today','idea_overview','pitches','customer_personas','seven_day_plan','risk_radar'):
                self.assertEqual(p[field],alternate[field],field)
            self.assertEqual(p['opportunity_score'],alternate['opportunity_score'])
            self.assertEqual(p['_canonical_id'],alternate['_canonical_id'])
            self.assertEqual(alternate['_localization_status'],'fallback')
        p=self.generate('ar');self.assertEqual(p['summary'],p['_alternate_plan']['summary'])
        self.assertNotIn('A proposed business hypothesis',p['_alternate_plan']['summary'])

    def test_shared_pdf_font_runs_bidi_and_xml_escaping(self):
        from pdf_text import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate
        buffer=io.BytesIO();value='PalmNest خطوة / مكتب Abu Dhabi — AED 85.50 <font name="BadFont">test</font>'
        story=[Paragraph(escape(value),ParagraphStyle('mixed',fontName='Helvetica',fontSize=11,leading=16))]
        SimpleDocTemplate(buffer).build(story);reader=PdfReader(buffer);text=reader.pages[0].extract_text()
        self.assertNotIn('\u25a0',text);self.assertNotIn('\ufffd',text)
        self.assertIn('85.50',text);self.assertIn('PalmNest',text);self.assertIn('BadFont',text)
        fonts={str(f.get_object().get('/BaseFont'))for f in reader.pages[0]['/Resources']['/Font'].get_object().values()}
        self.assertTrue(any('Amiri'in name for name in fonts));self.assertTrue(any('Helvetica'in name for name in fonts))

    def test_all_founder_pdf_states_and_languages_have_readable_glyphs(self):
        for native in ('en','ar'):
            p=self.generate(native)
            for stage,proof,score in [('none',{},15),('five',{'total_responses':5,'interested':5},15),
                                      ('payment',{'total_responses':5,'interested':5,'actual_payments':1},18),('clear',{},15)]:
                p['proof_summary']=proof
                for lang in ('en','ar'):
                    with self.subTest(native=native,stage=stage,export=lang):
                        r=self.client.post('/pdf',json=dict(p,_lang=lang));self.assertEqual(r.status_code,200)
                        pages=PdfReader(io.BytesIO(r.data)).pages;text='\n'.join(x.extract_text()for x in pages)
                        self.assertRegex(pages[0].extract_text(),rf'{score}\s*/\s*25')
                        self.assertNotIn('\u25a0',text);self.assertNotIn('\ufffd',text)
                        if native=='ar':
                            self.assertGreater(len(re.findall('[\u0600-\u06ff\ufb50-\ufeff]',text)),500)
                            fonts={str(f.get_object().get('/BaseFont'))for page in pages for f in page['/Resources']['/Font'].get_object().values()}
                            self.assertTrue(any('Amiri'in f for f in fonts))
                        if lang=='en':self.assertIn('First step today',text)
                        r.close()

    def test_investment_pdfs_render_mixed_business_and_user_notes(self):
        for native in ('en','ar'):
            p=self.generate(native)
            for lang in ('en','ar'):
                r=self.client.post('/investment/pdf',json={'plan':p,'finance':{'inputs':BASE},'notes':{'model':'خطة PalmNest / اشتراكات أسبوعية AED 85.50'},'lang':lang})
                self.assertEqual(r.status_code,200);text='\n'.join(x.extract_text()for x in PdfReader(io.BytesIO(r.data)).pages)
                self.assertNotIn('\u25a0',text);self.assertNotIn('\ufffd',text);self.assertIn('85.50',text)
                self.assertIn('1,800.00',text);r.close()

    def test_short_and_long_report_last_page_is_not_an_isolated_disclaimer(self):
        for lang in ('en','ar'):
            p=self.generate(lang);p['_financial_inputs']={'price':'30','available_capital':'10000','cash_mode':'simplified'}
            for long in (False,True):
                if long:
                    sentence='Interview office workers about lunch alternatives. 'if lang=='en'else'اسأل موظفي المكاتب عن بدائل الغداء. '
                    p['small_test_plan']['intro']=sentence*18
                    provenance.seal(p,provenance.sources({},p))
                r=self.client.post('/pdf',json=dict(p,_lang=lang));self.assertEqual(r.status_code,200)
                pages=PdfReader(io.BytesIO(r.data)).pages
                self.assertGreater(len(pages[-1].extract_text().split()),70)
                r.close()


if __name__=='__main__':unittest.main()
