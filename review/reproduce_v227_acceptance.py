"""Fixed new-domain cases, independent classifier mock; never contacts Groq."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from unittest.mock import patch

WORKSPACE = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('KHOTWA_PROBE_SOURCE', str(WORKSPACE)))
sys.path.insert(0, str(SOURCE))
from test_support import configure_mock_environment
configure_mock_environment()
import app
import material_claims as gate
from test_v22_content import fixture

CASES = json.loads((WORKSPACE/'tests/fixtures/v227_cases.json').read_text(encoding='utf-8'))
OUT = WORKSPACE/'outputs/v227-implementation-20261122'
(OUT/'evidence').mkdir(parents=True, exist_ok=True)
# This test oracle is intentionally separate from the implementation helpers.
IMPERATIVE = re.compile(r'^(?:ask|message|provide|conduct|leverage|capture|estimate|interview|test|compare|record|review|check|verify|define|identify|describe|map|draft|create|collect|contact|write|prepare|research|list|analyse|analyze|decide|avoid|use|share|send|track|confirm|choose|document|explore|find|plan|approach|meet|present|gather|outline|explain|اسأل|قابل|اختبر|قارن|سجل|راجع|تحقق|حدد|اكتب|اجمع|تواصل|ابحث|خطط|ابدأ|قدم)(?:\b|\s)', re.I)
HEDGE = re.compile(r'(?<!\w)(?:can|may|might|could|would|likely|possible|assum\w*|قد|ربما|يمكن|افتراض\w*)(?!\w)', re.I)


def mixed(items, key):
    return {i['id']: ('planning' if IMPERATIVE.search(i['text']) or i['text'].endswith(('?', '؟')) else
                      'hypothesis' if HEDGE.search(i['text']) else 'noun_phrase') for i in items}


def raw_fields(text):
    return {'title':text, 'business_name_suggestion':text, 'summary':text, 'idea_overview':{'problem':text,'solution':text},
            'first_step_today':text,'pitches':{'ten_sec':text,'whatsapp':text},
            'opportunity_score':{'easy_first_step':{'score':4,'reason':text}},
            'decision_engine':{'reason':text}}


def provider(mode):
    if mode in ('timeout','error'):
        return patch.object(gate,'classify',side_effect=TimeoutError('synthetic classifier outage') if mode=='timeout' else RuntimeError('synthetic classifier error'))
    if mode == 'missing':
        return patch.object(gate,'classify',return_value={})
    return patch.object(gate,'classify',side_effect=lambda items,key:{i['id']: ([] if mode=='invalid' else mode) for i in items})


def measure():
    records=[]; fps=[]
    for lang in ('en','ar'):
        for mode in ('achievement','promise','planning','hypothesis','negation','noun_phrase','unknown','missing','invalid','timeout','error'):
            with provider(mode):
                for text in CASES['unsafe'][lang]:
                    clean,meta=gate.verify_model(raw_fields(text),{'idea':'Proposed rehearsal studio'},lang,'synthetic')
                    retained=[p for p,v in gate.prose_items(clean)if v==text]
                    records.append({'lang':lang,'mode':mode,'text':text,'retained_paths':retained,'survived':bool(retained),'status':meta['status']})
    for text in CASES['false_positives']:
        lang='ar' if re.search('[\u0600-\u06ff]',text)else'en'
        with patch.object(gate,'classify',side_effect=mixed):
            clean,_=gate.verify_model({'summary':text},{},lang,'synthetic')
        fps.append({'text':text,'retained':clean['summary']==text,'published':clean['summary']})
    from review import reproduce_v226_acceptance as old
    old.plausible=mixed
    retained=old.measure()['retention']
    raw=fixture('v226_rich_lunch');raw['opportunity_score']['easy_first_step']['reason']=CASES['false_positives'][0]
    with patch.object(gate,'classify',side_effect=mixed),patch.object(app,'call_groq',return_value=json.dumps(raw)):
        result=app.app.test_client().post('/generate',json={'idea':'Proposed office lunch boxes','budget':10000,'lang':'en'}).json
    safe=[]
    for lang in ('en','ar'):
        with provider('timeout'):
            for text in CASES['safe'][lang]:
                clean,meta=gate.verify_model({'summary':text},{},lang,'synthetic')
                safe.append({'lang':lang,'text':text,'retained':clean['summary']==text,'published':clean['summary'],'status':meta['status']})
    return {'source':str(SOURCE),'fixture_sha256':hashlib.sha256((WORKSPACE/'tests/fixtures/v227_cases.json').read_bytes()).hexdigest(),
            'claims':records,'false_positives':fps,'retention':retained,'outage_safe':safe,
            'review_reason_plan':{'assessed':result['opportunity_score']['assessed_count'],'total':result['opportunity_score']['total'],'reason':result['opportunity_score']['easy_first_step']['reason']},'live_groq':False}


if __name__ == '__main__':
    with patch('requests.post',side_effect=AssertionError('Live provider forbidden')):
        report=measure()
    tag=sys.argv[1]if len(sys.argv)>1 else'after'
    (OUT/'evidence'/f'acceptance-{tag}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for lang in ('en','ar'):
        print(lang,{m:sum(r['survived']for r in report['claims']if r['lang']==lang and r['mode']==m)for m in ('planning','hypothesis','negation','unknown','timeout','noun_phrase')})
    print('RETENTION',[(r['fixture'],round(r['route_retention']*100,2),r['assessed_count'])for r in report['retention']])
    print('FALSE POSITIVES',sum(r['retained']for r in report['false_positives']),'/ 4; REVIEW REASON',report['review_reason_plan'])
