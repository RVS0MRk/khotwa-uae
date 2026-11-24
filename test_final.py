"""Final-release regressions use new ceramic/restoration/menu examples.

These are software assertions over synthetic text, not customer research.
"""
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from test_support import configure_mock_environment
configure_mock_environment()
import app
import material_claims as gate
import publication_policy as policy
from content_safety import export_plan
from pypdf import PdfReader
from review.reproduce_final_acceptance import CASES, MODES, provider
from test_v22_content import fixture
from scoring import DIMENSIONS


class FinalLanguageTests(unittest.TestCase):
    def setUp(self):
        network = patch('requests.post', side_effect=AssertionError('Live provider forbidden'))
        network.start()
        self.addCleanup(network.stop)
        self.client = app.app.test_client()

    def test_new_commands_questions_and_uncertainty_survive_outages_intact(self):
        for lang in ('en', 'ar'):
            for mode in ('noun_phrase', 'unknown', 'missing', 'malformed', 'timeout'):
                with provider(mode):
                    for text in CASES['safe'][lang]:
                        clean, _ = gate.verify_model({'summary': text, 'first_step_today': text}, {}, lang, 'synthetic')
                        self.assertEqual(clean, {'summary': text, 'first_step_today': text}, (lang, mode, text))

    def test_original_forty_unsafe_cases_actually_execute_in_both_outage_modes(self):
        from test_v226 import V226Tests, CASES as legacy
        self.assertEqual(len(legacy['independent_unsafe']['en']), 40)
        case = V226Tests('test_timeout_keeps_nonclaim_plan_but_never_claims_or_garbage')
        case.setUp()
        try:
            with patch.object(gate, 'verify_model', wraps=gate.verify_model) as calls:
                case.test_timeout_keeps_nonclaim_plan_but_never_claims_or_garbage()
            probes = [call for call in calls.call_args_list if list(call.args[0]) == ['summary']]
            self.assertEqual(len(probes), 80)
            for bad in legacy['independent_unsafe']['en']:
                self.assertEqual(sum(call.args[0] == {'summary':bad} for call in probes), 2)
        finally:
            case.doCleanups()

    def test_english_unlisted_base_forms_and_arabic_inflections_are_commands(self):
        for lang in ('en', 'ar'):
            for text in CASES['safe'][lang]:
                if ('may need' in text or text.startswith(('We do not', 'لا نعرف', 'لا نعلم', 'قد '))):
                    continue
                with provider('planning'):
                    self.assertEqual(gate.verify_model({'first_step_today': text}, {}, lang, 'synthetic')[0]['first_step_today'], text)

    def test_coordinated_argument_lists_are_not_independent_assertions(self):
        for text in ('Budget for materials, packaging and transport before committing funds.',
                     'Compare colours, sizes and patterns with the proposed customer.',
                     'قارن الألوان والأحجام والأنماط مع العميل المحتمل.'):
            self.assertEqual(len(policy.clauses(text)), 1, policy.clauses(text))

    def test_business_and_persona_names_survive_unknown_and_noun_labels(self):
        for lang in ('en', 'ar'):
            for mode in ('noun_phrase', 'unknown', 'missing', 'malformed', 'timeout'):
                with provider(mode):
                    for text in CASES['names'][lang]:
                        raw = {'business_name_suggestion': text, 'customer_personas': [{'name': text}]}
                        self.assertEqual(gate.verify_model(raw, {}, lang, 'synthetic')[0], raw, (lang, mode, text))
        with provider('noun_phrase'):
            raw={'readiness_report':{'target_customer':'Restaurant owners/marketing managers with 1-20 seats'}}
            self.assertEqual(gate.verify_model(raw,{},'en','synthetic')[0],raw)

    def test_sentence_shaped_names_never_use_noun_or_outage_escape(self):
        for lang in ('en', 'ar'):
            for mode in MODES:
                with provider(mode):
                    for text in CASES['unsafe'][lang] + CASES['short_claims'][lang]:
                        raw = {'business_name_suggestion': text, 'customer_personas': [{'name': text}]}
                        clean, _ = gate.verify_model(raw, {}, lang, 'synthetic')
                        self.assertEqual(clean['business_name_suggestion'], '', (lang, mode, text))
                        self.assertEqual(clean['customer_personas'][0]['name'], '', (lang, mode, text))

    def test_wrong_non_noun_labels_and_failures_cannot_publish_fresh_claims(self):
        for lang in ('en', 'ar'):
            for mode in MODES:
                if mode == 'noun_phrase':
                    continue  # Measured separately: not a universal fact verifier.
                with provider(mode):
                    for text in CASES['unsafe'][lang]:
                        raw = {'summary': text, 'pitches': {'ten_sec': text}, 'opportunity_score': {
                            'clear_customer': {'score': 4, 'reason': text}}}
                        clean, _ = gate.verify_model(raw, {}, lang, 'synthetic')
                        self.assertEqual(clean['summary'], '', (lang, mode, text))
                        self.assertIsNone(clean['opportunity_score']['clear_customer']['score'])

    def test_past_arabic_hollow_verbs_cannot_borrow_command_exception(self):
        for text in ('استعاد المكان مصروفات تجهيزه بحلول يونيو.', 'أجاز البنك طلب الاستوديو.',
                     'استرد أسبوع الافتتاح تكلفته في الأمسية الثانية.',
                     'خصص المستثمر مبلغ 240000 درهم لخدمة غداء نخلة.'):
            with provider('planning'):
                self.assertEqual(gate.verify_model({'summary': text}, {}, 'ar', 'synthetic')[0]['summary'], '')

    def test_generic_imperatives_cannot_authorize_quantified_marketing_promises(self):
        unsafe = ('Double your revenue in three weeks.', 'Multiply your profits by five.',
                  'Earn the equivalent of AED 900 every day.', 'Pocket a guaranteed income every week.',
                  'Slash your costs by 80 percent.', 'Double your revenue.',
                  'Triple your profits.', 'Halve your costs.', 'ضاعف دخلك خلال أسبوع.')
        for mode in MODES:
            with provider(mode):
                for text in unsafe:
                    clean,_=gate.verify_model({'summary':text,'first_step_today':text}, {}, 'en', 'synthetic')
                    self.assertEqual(clean,{'summary':'','first_step_today':''},(mode,text))
        for text in ('Sketch a budget for five interview participants before buying tools.',
                     'Quantify your hypothetical revenue for three scenarios.'):
            with provider('timeout'):
                self.assertEqual(gate.verify_model({'summary':text},{},'en','synthetic')[0]['summary'],text)

    def test_uncertainty_and_lists_cannot_cover_an_adjacent_achievement(self):
        for text in ('لا نعرف إن كان السكان سيهتمون، لكن الورشة حققت 6000 درهم.',
                     'Compare colours, sizes and patterns; the workshop earned AED 7400.',
                     'Sketch a ceramic invitation, and our studio has 40 customers.'):
            for mode in ('planning', 'hypothesis', 'negation', 'unknown'):
                with provider(mode):
                    self.assertEqual(gate.verify_model({'summary': text}, {}, 'en', 'synthetic')[0]['summary'], '', (mode, text))

    def test_fresh_route_advisor_and_signed_export_contract(self):
        # Existing normalization, scoring, HMAC receipts and PDF implementation
        # are exercised unchanged. A rejected reason taints its entire score.
        for lang in ('en', 'ar'):
            bad = CASES['unsafe'][lang][0]
            raw = fixture('rich_plan_' + lang)
            raw['summary'] = bad
            raw['business_name_suggestion'] = CASES['short_claims'][lang][0]
            raw['first_step_today'] = CASES['safe'][lang][0]
            raw.pop('bilingual_text', None)
            raw['opportunity_score']['clear_customer']['reason'] = bad
            with provider('planning'), patch.object(app, 'call_groq', return_value=json.dumps(raw, ensure_ascii=False)):
                r = self.client.post('/generate', json={'idea': 'Proposed ceramic workshops' if lang == 'en' else 'ورش خزف مقترحة', 'lang': lang, 'budget': 6500})
            self.assertEqual(r.status_code, 200)
            plan = r.json
            self.assertNotIn(bad, json.dumps(plan, ensure_ascii=False))
            self.assertIsNone(plan['opportunity_score']['clear_customer']['score'])
            self.assertEqual(plan['first_step_today'], raw['first_step_today'])
            self.assertNotIn(bad, json.dumps(export_plan(plan), ensure_ascii=False))
            plan['_lang'] = lang
            pdf = self.client.post('/pdf', json=plan)
            self.assertEqual(pdf.status_code, 200)
            self.assertGreater(len(PdfReader(io.BytesIO(pdf.data)).pages), 1)
            pdf.close()
            answer = {'title': 'Research' if lang == 'en' else 'بحث', 'summary': bad, 'points': [{'title': 'Next step' if lang == 'en' else 'الخطوة التالية', 'text': bad}], 'next_action': raw['first_step_today'], 'caution': ''}
            with provider('planning'), patch.object(app, 'call_groq', return_value=json.dumps(answer, ensure_ascii=False)):
                r = self.client.post('/ask', json={'question': 'Suggest an interview' if lang == 'en' else 'اقترح مقابلة', 'lang': lang})
            self.assertEqual(r.status_code, 200)
            self.assertNotIn(bad, json.dumps(r.json, ensure_ascii=False))


if __name__ == '__main__':
    unittest.main()
