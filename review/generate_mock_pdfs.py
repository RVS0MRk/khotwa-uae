"""Optional portable review utility; uses unchanged source test helpers."""
from pathlib import Path
import argparse, hashlib, json, sys
from copy import deepcopy

def main():
    parser=argparse.ArgumentParser(description='Generate 16 Founder and 4 Investment PDFs with mocked provider access; no credentials.')
    parser.add_argument('--output',type=Path,default=Path('outputs/v226-pdf-matrix'))
    args=parser.parse_args()
    source=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(source))
    from test_v225 import V225Tests
    from test_finance import BASE
    from test_v226 import MIXED
    from test_v22_content import fixture
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=True)
    test=V225Tests(); test.setUp(); rows=[]
    try:
        for native in ('en','ar'):
            raw=fixture('rich_plan_'+native);raw.pop('bilingual_text',None)
            raw['summary']=MIXED[native]
            raw['idea_overview']['why_market']=MIXED[native]
            raw['steps'][0]['description']=MIXED[native]
            plan=test.generate(native,raw)
            assert plan['summary']==MIXED[native], 'Required mixed paragraph was removed'
            for stage,counts in [('none',{}),('five',{'total_responses':5,'interested':5}),('payment',{'total_responses':5,'interested':5,'actual_payments':1}),('clear',{})]:
                for lang in ('en','ar'):
                    payload=deepcopy(plan); payload['proof_summary']=counts; payload['_lang']=lang
                    response=test.client.post('/pdf',json=payload)
                    assert response.status_code==200, ('Founder export failed',native,stage,lang,response.status_code)
                    file=output/f'founder-{native}-{stage}-labels-{lang}.pdf'; file.write_bytes(response.data)
                    rows.append({'file':file.name,'kind':'Founder','native':native,'stage':stage,'export_language':lang,'sha256':hashlib.sha256(response.data).hexdigest()}); response.close()
            for lang in ('en','ar'):
                response=test.client.post('/investment/pdf',json={'plan':plan,'finance':{'inputs':BASE},'notes':{'model':MIXED[native]},'lang':lang})
                assert response.status_code==200, ('Investment export failed',native,lang,response.status_code)
                file=output/f'investment-{native}-labels-{lang}.pdf'; file.write_bytes(response.data)
                rows.append({'file':file.name,'kind':'Investment','native':native,'export_language':lang,'sha256':hashlib.sha256(response.data).hexdigest()}); response.close()
    finally:
        test.doCleanups()
    (output/'generated-index.json').write_text(json.dumps({'mode':'mocked; no live Groq','reports':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated 16 Founder and 4 Investment reports in',output)

if __name__=='__main__': main()
