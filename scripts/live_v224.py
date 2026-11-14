"""Explicit owner opt-in: 10 ideas + relevant Advisor questions, <=40 provider attempts.

No automatic retries. Stop on any primary/provider quota error or incomplete
verification. The local app's normal key loader is used; never print the key.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=[
('en','Healthy lunch-box subscriptions for office workers in Abu Dhabi.','Abu Dhabi','How can I test lunch demand before buying equipment?'),
('en','Robotics workshops for children in Sharjah.','Sharjah','How can I interview parents before renting a venue?'),
('en','Mobile car cleaning in Dubai.','Dubai','How can I test demand without paid advertising?'),
('en','Small online clothing store in Ajman.','Ajman','How can I test preferences before buying inventory?'),
('en','Sustainable packaging for local restaurants.','Abu Dhabi','Which procurement questions should I ask restaurant owners?'),
('ar','مشروع وجبات صحية لموظفي المكاتب في أبوظبي.','Abu Dhabi','كيف أختبر الطلب قبل شراء المعدات؟'),
('ar','ورش روبوتات للأطفال في الشارقة.','Sharjah','كيف أقابل أولياء الأمور قبل استئجار مكان؟'),
('ar','خدمة غسيل سيارات متنقلة في دبي.','Dubai','كيف أختبر الطلب دون إعلانات مدفوعة؟'),
('ar','متجر إلكتروني للملابس في عجمان.','Ajman','كيف أختبر التفضيلات قبل شراء المخزون؟'),
('ar','مشروع تغليف صديق للبيئة للمطاعم.','Abu Dhabi','ما الأسئلة التي أطرحها عن شراء العبوات؟'),
]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm-live',action='store_true')
    parser.add_argument('--output',default='outputs/v224-live')
    args=parser.parse_args()
    if not args.confirm_live:
        parser.error('Requires --confirm-live; no provider calls made.')
    output=(ROOT/args.output).resolve()
    if not output.is_relative_to(ROOT/'outputs'):
        parser.error('Output must be inside ignored outputs/.')
    sys.path.insert(0,str(ROOT))
    import os
    os.chdir(ROOT)
    import app
    if not app.API_KEY or app.API_KEY in ('test-only-placeholder','test-key','your-key-here'):
        parser.error('No configured real key; no provider calls made.')
    import requests
    from flask import request,has_request_context
    original=requests.post;attempts=[];results=[]
    def counted(url,*a,**kw):
        if url!=app.GROQ_URL:return original(url,*a,**kw)
        if len(attempts)>=40:raise RuntimeError('Explicit 40-attempt budget exhausted')
        record={'endpoint':request.path if has_request_context()else'unknown','attempt':len(attempts)+1};attempts.append(record);started=time.monotonic()
        try:
            response=original(url,*a,**kw);record['http_status']=response.status_code;return response
        finally:record['seconds']=round(time.monotonic()-started,3)
    requests.post=counted
    output.mkdir(parents=True,exist_ok=True)
    def save():
        (output/'results.json').write_text(json.dumps({'mode':'REAL LIVE','maximum_provider_attempts':40,'actual_provider_attempts':len(attempts),'requests':attempts,'cases':results},ensure_ascii=False,indent=2),encoding='utf-8')
    client=app.app.test_client()
    try:
        for index,(lang,idea,region,question)in enumerate(CASES):
            for endpoint,payload in [('/generate',{'lang':lang,'idea':idea,'region':region,'budget':6500}),('/ask',{'lang':lang,'question':question})]:
                if endpoint=='/ask':payload['plan_context']=plan
                started=time.monotonic();r=client.post(endpoint,json=payload)
                row={'case':index+1,'lang':lang,'endpoint':endpoint,'http_status':r.status_code,'seconds':round(time.monotonic()-started,3)}
                body=r.get_json()or{};row['verification']=body.get('_verification',{}).get('status')if endpoint=='/generate'else r.headers.get('X-Khotwa-Content-Verification');row['response']=body
                results.append(row);save();print(json.dumps({k:v for k,v in row.items()if k!='response'}),flush=True)
                if r.status_code!=200 or row['verification'] not in ('checked','source_composed'):
                    print('STOP: request or content verification did not complete. No automatic retries. Respect Retry-After and investigate provider quotas.');return 1
                if endpoint=='/generate':
                    plan={k:v for k,v in body.items()if k not in ('_alternate_plan','_content_receipt','_provenance','_verification')}
                if index!=9 or endpoint!='/ask':time.sleep(65)
    finally:requests.post=original;save()
    return 0


if __name__=='__main__':raise SystemExit(main())
