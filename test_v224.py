"""V2.2.4 policy/provenance regressions. All provider I/O is mocked."""
import io
import json
import os
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch, Mock
from test_support import configure_mock_environment
configure_mock_environment()
import app
import material_claims as gate
from provenance import sources, seal, receipt_strings
from content_safety import export_plan
from groq_client import request_completion, GroqGenerationError
from test_v22_content import fixture
from test_finance import BASE

CASES=json.loads((Path(__file__).parent/'tests/fixtures/v224_claims.json').read_text(encoding='utf-8'))


def verdicts(items, _key):
    """Recorded semantic labels, not a production classifier or network call."""
    bad={s for k,v in CASES.items() if k.startswith(('unsupported','promises')) for s in v}
    return {i['id']: ('achievement' if i['text'] in bad else 'negation' if i['text'].startswith(('No free','لا نعد')) else 'noun_phrase')for i in items}


class V224Tests(unittest.TestCase):
    def setUp(self):
        self.no_network=patch('requests.post',side_effect=AssertionError('Live calls forbidden'));self.no_network.start();self.addCleanup(self.no_network.stop)
        self.semantic=patch.object(gate,'classify',side_effect=verdicts);self.semantic.start();self.addCleanup(self.semantic.stop)
        self.client=app.app.test_client()

    def generate(self,raw,lang='en',idea=None):
        with patch.object(app,'call_groq',return_value=json.dumps(raw,ensure_ascii=False)):
            r=self.client.post('/generate',json={'idea':idea or ('Lunch boxes for office workers'if lang=='en'else'وجبات لموظفي المكاتب'),'region':'Abu Dhabi','budget':6500,'lang':lang})
        self.assertEqual(r.status_code,200);return r.json

    def test_every_original_and_new_claim_in_plan_and_advisor_fields(self):
        for lang in ('en','ar'):
            for bad in CASES['unsupported_'+lang]+CASES['promises_'+lang]:
                with self.subTest(lang=lang,claim=bad):
                    raw=fixture('rich_plan_'+lang)
                    raw['summary']=bad;raw['first_step_today']=bad;raw['pitches']={k:bad for k in raw['pitches']}
                    raw['opportunity_score']['local_fit']['reason']=bad
                    raw['idea_overview']['solution']=bad
                    p=self.generate(raw,lang)
                    self.assertNotIn(bad,json.dumps(p,ensure_ascii=False))
                    answer=dict(title=bad,summary=bad,points=[dict(title=bad,text=bad)],next_action=bad,caution=bad)
                    with patch.object(app,'call_groq',return_value=json.dumps(answer,ensure_ascii=False)):
                        r=self.client.post('/ask',json={'question':'Suggest my next test'if lang=='en'else'اقترح اختبار الفكرة التالي','lang':lang})
                    self.assertEqual(r.status_code,200);self.assertNotIn(bad,json.dumps(r.json,ensure_ascii=False))

    def test_hypotheses_negations_and_neighbour_personalization(self):
        for planning in ('تحتاج مكونات الغداء وتوقيته إلى اختبار مع موظفين قبل الالتزام.', 'نختبر وجبات DeskFresh المكتبية بخيارات أسبوعية مرنة، ونرحب برأيك قبل البيع.'):
            self.assertEqual(gate.verify_model({'summary':planning},{},'ar','unused')[0]['summary'],planning)
        for lang in ('en','ar'):
            for good in CASES['safe_'+lang]:
                clean,meta=gate.verify_model({'summary':good}, {},lang,'unused')
                self.assertEqual(clean['summary'],good,(lang,good))
            good=CASES['safe_'+lang][-1];bad=CASES['unsupported_'+lang][0]
            clean,_=gate.verify_model({'summary':good+' '+bad},{},lang,'unused')
            self.assertEqual(clean['summary'],good)

    def test_naive_verifier_cannot_approve_material_sentence_or_invented_percentage(self):
        for kind in ('safe','planning','unknown','noun_phrase'):
            with patch.object(gate,'classify',side_effect=lambda items,key:{i['id']:kind for i in items}):
                for text in [CASES['unsupported_en'][0],CASES['unsupported_en'][1],CASES['unsupported_ar'][0],CASES['promises_en'][0]]:
                    self.assertEqual(gate.verify_model({'summary':text},{},'en','unused')[0]['summary'],'')

    def test_missing_error_and_oversized_verification_fail_closed(self):
        for value in ({},{0:[]},{0:{'unexpected':'object'}},RuntimeError('synthetic verification outage')):
            with patch.object(gate,'classify',**({'side_effect':value}if isinstance(value,Exception)else{'return_value':value})):
                clean,meta=gate.verify_model({'summary':CASES['unsupported_en'][0]}, {},'en','unused')
                self.assertEqual(clean['summary'],'')
        raw={'points':['x'*1000]*200}
        with patch.object(gate,'classify',return_value={})as classifier:
            clean,meta=gate.verify_model(raw,{},'en','unused')
        sent=classifier.call_args.args[0];self.assertLessEqual(len(sent),gate.MAX_ITEMS);self.assertLessEqual(sum(len(x['text'])for x in sent),gate.MAX_CHARS)
        self.assertTrue(all(not x for x in clean['points']))

    def test_user_attribution_is_bound_to_actual_statement(self):
        statement='My proposed clothing store offers free delivery in Ajman.'
        with patch.object(gate,'classify',return_value={0:'user_attributed'}):
            clean,_=gate.verify_model({'summary':'The founder says: '+statement},{'idea':statement},'en','unused')
            self.assertIn(statement,clean['summary']);self.assertIn('not independently verified',clean['summary'])
            clean,_=gate.verify_model({'summary':'The founder says that funding was approved.'},{'idea':statement},'en','unused')
            self.assertEqual(clean['summary'],'')

    def test_source_kinds_and_financial_projection_are_not_actual_revenue(self):
        p={'proof_summary':{'total_responses':2,'actual_payments':1},'_financial_inputs':BASE,'_provenance':{'kind':'externally_verified'}}
        ledger=sources({'idea':'Proposed service','budget':3000},p)
        self.assertEqual(ledger['entries']['user.budget']['kind'],'user_assumption')
        self.assertEqual(ledger['entries']['proof']['kind'],'self_reported_observation')
        self.assertFalse(ledger['entries']['proof']['verified'])
        self.assertEqual(ledger['entries']['finance']['kind'],'financial_projection')
        self.assertEqual(ledger['entries']['finance']['value']['revenue'],'5000.00')
        self.assertEqual(ledger['external_achievement_evidence'],[])

    def test_export_rechecks_edited_text_forged_receipts_and_state_aliases(self):
        p=self.generate(fixture());before=deepcopy(p);bad=CASES['unsupported_en'][1]
        self.assertTrue(receipt_strings(p));p['summary']+=' '+bad;p['state']['target_customer']=bad
        clean=export_plan(p)
        self.assertNotIn(bad,json.dumps(clean));self.assertIn(before['summary'],clean['summary'])
        # A placeholder has no terminal punctuation. Its negation must not
        # grant trust to a later, unrelated achievement in the same sentence.
        placeholder={"summary":"Not provided — describe it in Edit idea"}
        seal(placeholder,sources({"idea":"Lunch boxes"}))
        placeholder['summary']+=' '+bad
        self.assertEqual(export_plan(placeholder)['summary'],'Not provided — describe it in Edit idea')
        p['_content_receipt']['signature']='forged';p['summary']=bad
        self.assertNotIn(bad,json.dumps(export_plan(p)))
        p['_alternate_plan']['summary']=bad
        self.assertNotIn(bad,json.dumps(export_plan(p)))

    def test_export_preserves_user_observations_notes_and_finance_without_provider(self):
        p=self.generate(fixture());p['proof_summary']={'total_responses':2,'actual_payments':1};p['_financial_inputs']=BASE
        clean=export_plan(p)
        self.assertEqual(clean['proof_summary'],p['proof_summary']);self.assertEqual(clean['_financial_inputs'],BASE)
        self.assertEqual(app.analyze_finance({'inputs':BASE})['base']['operating_profit'],'1800.00')

    def test_both_pdf_paths_reject_each_unreviewed_achievement_and_offer(self):
        for lang in ('en','ar'):
            bad=' '.join(CASES['unsupported_'+lang][:2]+CASES['promises_'+lang][:2])
            p=self.generate(fixture('rich_plan_'+lang),lang);p['summary']=bad;p['first_step_today']=bad;p['idea_overview']['solution']=bad
            with patch('founder_pdf.export_plan',wraps=export_plan)as founder,patch('financial_report.export_plan',wraps=export_plan)as investment:
                for endpoint,payload,boundary in [('/pdf',dict(p,_lang=lang),founder),('/investment/pdf',{'plan':p,'finance':{'inputs':BASE},'notes':{'model':'User-entered model'},'lang':lang},investment)]:
                    r=self.client.post(endpoint,json=payload);self.assertEqual(r.status_code,200)
                    cleaned=export_plan(boundary.call_args.args[0]);self.assertNotIn(bad,json.dumps(cleaned,ensure_ascii=False));r.close()

    def test_language_versions_share_canonical_score_and_identity(self):
        for lang in ('en','ar'):
            raw=fixture('rich_plan_'+lang);raw.pop('bilingual_text',None)
            p=self.generate(raw,lang);a=p['_alternate_plan']
            self.assertEqual(p['_canonical_id'],a['_canonical_id']);self.assertEqual(p['opportunity_score'],a['opportunity_score'])
            self.assertEqual(p['customer_personas'],a['customer_personas']);self.assertEqual(p['state'],a['state'])
            self.assertEqual(a['_localization_status'],'fallback')

    def test_exact_arabic_advisor_token_and_coherent_partial_reply(self):
        answer={'title':'تحديث دليل الأدلة','summary':'لم أتمكن من إعداد إجابة موثوقة الآن.','points':[{'title':'سجّل الردود','text':'أدخل القيم في proof_mode_recorded_evidence_only لتتبع إجمالي الردود.'}],'next_action':'اسأل عشرة مالكي سيارات في دبي.','caution':''}
        for token in ('proof_mode_recorded_evidence_only','proofmoderecordedevidenceonly'):
            raw=deepcopy(answer);raw['points'][0]['text']=raw['points'][0]['text'].replace('proof_mode_recorded_evidence_only',token)
            with patch.object(app,'call_groq',return_value=json.dumps(raw,ensure_ascii=False)):
                r=self.client.post('/ask',json={'question':'كيف أختبر الطلب؟','lang':'ar'})
            self.assertEqual(r.status_code,200);self.assertNotIn(token,json.dumps(r.json,ensure_ascii=False))
            if r.json['answer']['points']:self.assertNotIn('لم أتمكن',r.json['answer']['summary'])

    def test_primary_provider_429_is_distinct_and_never_automatically_retried(self):
        exc=GroqGenerationError('Provider quota',{'http_status':429,'retry_after':17})
        for endpoint,payload in [('/generate',{'idea':'Lunch'}),('/ask',{'question':'Suggest a test'}),('/discover',{})]:
            with patch.object(app,'call_groq',side_effect=exc)as call:
                r=self.client.post(endpoint,json=payload)
            self.assertEqual(r.status_code,429);self.assertEqual(r.json['error'],'provider_rate_limited');self.assertEqual(r.headers['Retry-After'],'17');call.assert_called_once()

    def test_actual_provider_budget_counts_verification_attempts(self):
        import provider_budget
        provider_budget._windows.clear();self.addCleanup(provider_budget._windows.clear)
        with patch.dict(os.environ,{'RENDER':'true','KHOTWA_AI_CLIENT_PER_10MIN':'2','KHOTWA_AI_GLOBAL_PER_10MIN':'3'}),app.app.test_request_context('/generate'):
            self.assertEqual(provider_budget.reserve(),0);self.assertEqual(provider_budget.reserve(),0);self.assertGreater(provider_budget.reserve(),0)

    def test_verifier_transport_has_one_bounded_json_request_and_rejects_bad_ids(self):
        from groq_client import GroqCompletion
        with patch('groq_client.request_completion',return_value=GroqCompletion('{"verdicts":[{"id":0,"kind":"planning"}]}',{}))as transport:
            self.assertEqual(gate.semantic_classify([{'id':0,'text':'Ask office workers.'}],'synthetic'),{0:'planning'})
            transport.assert_called_once();self.assertEqual(transport.call_args.kwargs['timeout'],12);self.assertEqual(transport.call_args.kwargs['max_completion_tokens'],2400)
        for body in ('{"verdicts":[{"id":4,"kind":"planning"}]}','{"verdicts":[{"id":0},{"id":0}]}','{}'):
            with patch('groq_client.request_completion',return_value=GroqCompletion(body,{})),self.assertRaises(ValueError):gate.semantic_classify([{'id':0,'text':'Ask office workers.'}],'synthetic')

    def test_actual_packaging_replay_preserves_questions_without_invented_savings(self):
        lunch=fixture('v224_live_lunch')
        clean,_=gate.verify_model(lunch,{'idea':'Healthy lunch-box subscriptions for office workers in Abu Dhabi.'},'en','unused')
        self.assertEqual(clean['summary'],lunch['summary'])
        raw=fixture('v224_live_packaging')
        p=self.generate(raw,idea='Sustainable packaging for local restaurants.')
        text=json.dumps(p,ensure_ascii=False)
        self.assertNotIn('30%',text);self.assertNotIn('zero upfront cost',text)
        self.assertEqual(p['validation_questions'],raw['validation_questions'])
        self.assertIn('packaging',p['summary'].lower())

    def test_live_validation_requires_explicit_opt_in_before_import_or_requests(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('bounded_live_v224',Path(__file__).parent/'scripts/live_v224.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with patch('sys.argv',['live_v224.py']),self.assertRaises(SystemExit)as stopped:module.main()
        self.assertEqual(stopped.exception.code,2)
