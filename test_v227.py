"""V227 label/form contracts; immutable earlier tests are left untouched."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from test_support import configure_mock_environment
configure_mock_environment()
import app
import material_claims as gate
import publication_policy as policy
from content_safety import offending
from review.reproduce_v227_acceptance import CASES, mixed, raw_fields, provider
from test_v22_content import fixture


class V227Tests(unittest.TestCase):
    def setUp(self):
        network = patch('requests.post',side_effect=AssertionError('Live provider forbidden'))
        network.start();self.addCleanup(network.stop)

    def test_new_domain_sixty_claims_blocked_under_wrong_labels_in_eight_fields(self):
        for lang in ('en','ar'):
            self.assertEqual(len(CASES['unsafe'][lang]),30)
            for mode in ('planning','hypothesis','negation','achievement','promise','instruction'):
                with provider(mode):
                    for bad in CASES['unsafe'][lang]:
                        with self.subTest(lang=lang,mode=mode,bad=bad):
                            clean,_=gate.verify_model(raw_fields(bad),{},lang,'synthetic')
                            self.assertNotIn(bad,json.dumps(clean,ensure_ascii=False))
                            self.assertIsNone(clean['opportunity_score']['easy_first_step']['score'])

    def test_unknown_missing_invalid_timeout_error_fail_closed(self):
        for mode in ('unknown','missing','invalid','timeout','error'):
            for lang in ('en','ar'):
                with provider(mode):
                    for bad in CASES['unsafe'][lang]:
                        clean,meta=gate.verify_model(raw_fields(bad),{},lang,'synthetic')
                        self.assertNotIn(bad,json.dumps(clean,ensure_ascii=False),(mode,lang,bad))
                        self.assertEqual(meta['status'],'fallback')
        for invalid in (None,[],{0:None},{0:'unrecognized'},{0:{'kind':'planning'}}):
            with patch.object(gate,'classify',return_value=invalid):
                clean,meta=gate.verify_model({'summary':CASES['unsafe']['en'][0]}, {},'en','synthetic')
                self.assertEqual(clean['summary'],'');self.assertEqual(meta['status'],'fallback')

    def test_noun_phrase_residual_is_the_existing_backstop(self):
        for lang in ('en','ar'):
            with provider('noun_phrase'):
                for text in CASES['unsafe'][lang]:
                    clean,_=gate.verify_model({'summary':text},{},lang,'synthetic')
                    self.assertEqual(clean['summary'],'' if offending(text) else text)

    def test_safe_outage_forms_survive_in_full(self):
        for lang in ('en','ar'):
            with provider('timeout'):
                for text in CASES['safe'][lang]:
                    clean,meta=gate.verify_model({'summary':text},{},lang,'synthetic')
                    self.assertEqual(clean['summary'],text)
                    self.assertEqual(meta['status'],'fallback')

    def test_short_label_allowlist_is_bounded_and_not_a_declarative_escape(self):
        labels={'title':'Studio experiment','name':'ChordRoom','business_name_suggestion':'ChordRoom',
                'target_customer':'Local ensembles','location':'Al Ain','focus':'Interview design'}
        with provider('missing'):
            clean,_=gate.verify_model(labels,{},'en','synthetic');self.assertEqual(clean,labels)
            for key in labels:
                bad=CASES['unsafe']['en'][0]
                clean,_=gate.verify_model({key:bad},{},'en','synthetic');self.assertEqual(clean[key],'')
            long=' '.join(['Rehearsal']*13)
            clean,_=gate.verify_model({'title':long,'summary':'Studio experiment'},{},'en','synthetic')
            self.assertEqual(clean,{'title':'','summary':''})

    def test_label_form_must_match_even_when_material_backstop_does_not_object(self):
        for text in ('ChordRoom is beside a college.','تقع قاعة وتر بجانب كلية.'):
            self.assertFalse(offending(text))
            for mode in ('planning','hypothesis','negation','unknown'):
                with provider(mode):
                    clean,_=gate.verify_model({'summary':text},{},'en','synthetic')
                    self.assertEqual(clean['summary'],'')
        for text in ('Ask musicians about rehearsal needs.','قد تحتاج الغرفة إلى عزل صوتي.','We have not opened the studio yet.'):
            with provider('missing'):
                self.assertEqual(gate.verify_model({'summary':text},{},'en','synthetic')[0]['summary'],text)

    def test_coordinated_nouns_share_predicate_and_denial(self):
        for text in CASES['false_positives']+[CASES['safe']['en'][1],CASES['safe']['ar'][1]]:
            self.assertEqual(len(policy.clauses(text)),1,text)
            with patch.object(gate,'classify',side_effect=mixed):
                clean,_=gate.verify_model({'summary':text},{},'en','synthetic')
            self.assertEqual(clean['summary'],text)
        for text in ('We have no members, and our calendar is booked solid.',
                     'If musicians request evening slots, our calendar is booked solid.',
                     'لم نفتتح الغرفة، وسددت شاحنة التجميل إيجارها بالكامل.'):
            for mode in ('planning','hypothesis','negation','unknown'):
                with provider(mode):
                    clean,_=gate.verify_model({'summary':text},{},'en','synthetic')
                    self.assertEqual(clean['summary'],'',(mode,text,policy.clauses(text)))

    def test_can_is_scoped_to_its_own_predicate_not_a_later_clause(self):
        for text in (CASES['false_positives'][0], 'يمكن إعداد رسالة اهتمام اليوم.'):
            self.assertTrue(policy.hypothesis_clause(policy.normalize(text)))
        for text in ('The calendar is booked solid, and we can discuss room sizes.',
                     'سددت الغرفة إيجارها بالكامل، ويمكن إعداد مقابلة.'):
            with provider('hypothesis'):
                self.assertEqual(gate.verify_model({'summary':text},{},'en','synthetic')[0]['summary'],'')

    def test_review_reason_preserves_all_five_dimensions(self):
        raw=fixture('v226_rich_lunch');raw['opportunity_score']['easy_first_step']['reason']=CASES['false_positives'][0]
        with patch.object(gate,'classify',side_effect=mixed),patch.object(app,'call_groq',return_value=json.dumps(raw)):
            r=app.app.test_client().post('/generate',json={'idea':'Proposed office lunch boxes','lang':'en','budget':10000})
        self.assertEqual(r.status_code,200);self.assertEqual(r.json['opportunity_score']['assessed_count'],5)
        self.assertEqual(r.json['opportunity_score']['total'],18)
        self.assertEqual(r.json['opportunity_score']['easy_first_step']['reason'],CASES['false_positives'][0])

    def test_generation_outage_uses_existing_fallback_without_blank_plan(self):
        raw=fixture('v226_rich_lunch');raw['summary']='Could musicians share a rehearsal space?'
        raw['idea_overview']['problem']='Local ensembles may need a rehearsal room.'
        raw['idea_overview']['solution']='Compare room access and sound isolation.'
        with provider('timeout'),patch.object(app,'call_groq',return_value=json.dumps(raw)):
            r=app.app.test_client().post('/generate',json={'idea':'Proposed rehearsal rooms','lang':'en','budget':10000})
        self.assertEqual(r.status_code,200);self.assertTrue(r.json['summary']);self.assertTrue(r.json['first_step_today'])
        self.assertEqual(r.json['_verification']['status'],'fallback')
        self.assertEqual(r.json['summary'],raw['summary'])


if __name__=='__main__':
    unittest.main()
