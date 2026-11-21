"""Independent, fixed input measurements; no provider requests, no PDF builds."""
from pathlib import Path
import hashlib,json,re,sys,os
from copy import deepcopy
from unittest.mock import patch
WORKSPACE=Path(__file__).resolve().parents[1]
ROOT=Path(os.environ.get('KHOTWA_PROBE_SOURCE',str(WORKSPACE)));sys.path.insert(0,str(ROOT))
OUT=WORKSPACE/'outputs/v226-acceptance';(OUT/'evidence').mkdir(parents=True,exist_ok=True)
from test_support import configure_mock_environment
configure_mock_environment()
import app,material_claims as gate
from test_v22_content import fixture
from scoring import DIMENSIONS
CASES=json.loads((ROOT/'tests/fixtures/v226_cases.json').read_text(encoding='utf-8'))
IMPERATIVE=re.compile(r'^(?:ask|message|provide|conduct|leverage|capture|estimate|interview|test|compare|record|review|check|verify|define|identify|describe|map|draft|create|collect|contact|write|prepare|research|list|analyse|analyze|decide|avoid|use|share|send|track|confirm|choose|document|explore|find|plan|approach|meet|present|gather|outline|explain|اسأل|قابل|اختبر|قارن|سجل|راجع|تحقق|حدد|اكتب|اجمع|تواصل|ابحث|خطط|ابدأ|قدم)(?:\b|\s)',re.I)
HYPOTHESIS=re.compile(r'\b(?:may|might|could|likely|assum\w*)\b|(?<!\w)(?:قد|ربما|افتراض\w*)(?!\w)',re.I)
def plausible(items,key):
    return {i['id']:('planning'if IMPERATIVE.search(i['text'])or i['text'].endswith(('?','؟'))else'hypothesis'if HYPOTHESIS.search(i['text'])else'noun_phrase')for i in items}
def measure():
    retention=[]; safety=[]; safe=[]
    for name in ('v226_rich_lunch','rich_plan_en','v224_live_lunch','v224_live_lunch_ar','v224_live_packaging'):
        raw=fixture(name);lang='ar'if name.endswith('_ar')else'en';inputs={'idea':raw['summary'],'region':'Abu Dhabi','budget':10000,'lang':lang}
        with patch.object(gate,'classify',side_effect=plausible),patch.object(app,'call_groq',return_value=json.dumps(raw,ensure_ascii=False)):
            clean,meta=gate.verify_model(raw,inputs,lang,'synthetic')
            response=app.app.test_client().post('/generate',json=inputs)
        assert response.status_code==200
        plan=response.json; omitted=set(CASES['excluded_retention_paths'][name]); entries=[(p,t)for p,t in gate.prose_items(raw)if p not in omitted]
        values={t for _,t in gate.prose_items(plan)}; verified={t for _,t in gate.prose_items(clean)}
        new_fragments=[(p,t)for p,t in gate.prose_items(plan)if t and re.match(r'^(?:[a-z]|(?:and|whether|but)\b|(?:و|أو)\s)',t)and t not in{v for _,v in gate.prose_items(raw)}]
        retention.append({'fixture':name,'eligible':len(entries),'excluded_paths':sorted(omitted),'route_verbatim_kept':sum(t in values for p,t in entries),'route_retention':sum(t in values for p,t in entries)/len(entries),'verifier_retention':sum(t in verified for p,t in entries)/len(entries),'assessed_count':plan['opportunity_score']['assessed_count'],'total':plan['opportunity_score']['total'],'problem_retained':plan['idea_overview']['problem']==raw['idea_overview']['problem'],'solution_retained':plan['idea_overview']['solution']==raw['idea_overview']['solution'],'new_fragment_candidates':new_fragments,'missing':[(p,t)for p,t in entries if t not in values]})
    for lang in ('en','ar'):
        for label in ('planning','hypothesis','negation','user_attributed','noun_phrase'):
            for text in CASES['independent_unsafe'][lang]+CASES['review_unsafe'][lang]:
                with patch.object(gate,'classify',side_effect=lambda items,key:{i['id']:label for i in items}):
                    result,_=gate.verify_model({'summary':text},{'idea':'Proposed local bicycle repair service / خدمة صيانة دراجات مقترحة'},lang,'synthetic')
                safety.append({'lang':lang,'label':label,'text':text,'full_survived':text in result['summary'],'published':result['summary'],'independent':text in CASES['independent_unsafe'][lang]})
        for text in CASES['safe'][lang]:
            with patch.object(gate,'classify',side_effect=plausible):result,_=gate.verify_model({'summary':text},{'idea':'Proposed local bicycle repair service / خدمة صيانة دراجات مقترحة'},lang,'synthetic')
            safe.append({'lang':lang,'text':text,'retained_intact':result['summary']==text,'published':result['summary']})
    from content_safety import export_plan
    with patch.object(gate,'classify',side_effect=plausible),patch.object(app,'call_groq',return_value=json.dumps(fixture('rich_plan_en'))):
        p=app.app.test_client().post('/generate',json={'idea':'Proposed local workshop','budget':10000}).json
    paths=['state.category','state.region','state.context','state.customer_type','state.user_budget_aed','_category','_region','_context','_user_type','_budget','risk_radar.0.level','decision_engine.risk_level']
    metadata=[];bad='Dubai SME fund backing for SpokeFix came through.'
    for path in paths:
        value=deepcopy(p);owner=value;keys=path.split('.')
        for key in keys[:-1]:owner=owner[int(key)]if isinstance(owner,list)else owner[key]
        owner[int(keys[-1])if isinstance(owner,list)else keys[-1]]=bad
        clean=export_plan(value);result=clean
        for key in keys:result=result[int(key)]if isinstance(result,list)else result[key]
        metadata.append({'path':path,'unsafe_value_retained':result==bad,'display_value':result})
    return {'retention':retention,'safety':safety,'legitimate':safe,'export_display':metadata,'fixture_sha256':{name:hashlib.sha256((ROOT/'tests/fixtures'/name).read_bytes()).hexdigest()for name in('v226_cases.json','v226_rich_lunch.json')},'live_provider_calls':False}
if __name__=='__main__':
    with patch('requests.post',side_effect=AssertionError('Live provider forbidden')):report=measure()
    tag=sys.argv[1] if len(sys.argv)>1 else 'after'
    (OUT/'evidence'/f'acceptance-{tag}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('RETENTION',[(r['fixture'],round(r['route_retention']*100,2),r['assessed_count'],r['problem_retained'],r['solution_retained'])for r in report['retention']])
    print('UNSAFE SURVIVORS',[(l,k,sum(r['full_survived']for r in report['safety']if r['lang']==l and r['label']==k))for l in('en','ar')for k in('planning','hypothesis','negation','user_attributed','noun_phrase')])
    print('SAFE',[(l,sum(r['retained_intact']for r in report['legitimate']if r['lang']==l),len(CASES['safe'][l]))for l in('en','ar')])
