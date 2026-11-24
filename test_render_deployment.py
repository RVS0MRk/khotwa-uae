"""Deployment-only access/channel tests; no live provider and no real keys."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parent
SETUP='''
import os,json,io
from unittest.mock import patch
os.environ.update(GROQ_API_KEY='test-only-render-provider',KHOTWA_CONTENT_SIGNING_KEY='test-only-stable-signing-key-32-bytes-or-more',KHOTWA_LIVE_ACCESS_TOKEN='test-only-live-token-32-characters-or-more',RENDER='true',RENDER_EXTERNAL_URL='https://example.test')
import requests
requests.post=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Live network forbidden'))
import groq_client
from groq_client import GroqCompletion
from demo_data import plan,ideas,answer,SCENARIO,FINANCE
calls=[]
def provider(key,messages,**kwargs):
    calls.append(kwargs)
    if kwargs.get('max_completion_tokens')==2400:
        items=json.loads(messages[-1]['content']);value={'verdicts':[{'id':i['id'],'kind':'noun_phrase'}for i in items]}
    else:
        from flask import request
        lang=(request.json or {}).get('lang','en')
        value=plan(lang)if request.path=='/generate'else ideas(lang)if request.path=='/discover'else answer(lang)
    return GroqCompletion(json.dumps(value,ensure_ascii=False),{'http_status':200,'finish_reason':'stop','content_empty':False,'completion_tokens':123,'reasoning_tokens':4})
groq_client.request_completion=provider
import render_service as service
app=service.app;c=app.test_client()
base='https://example.test'
def post(path,data,live=False):return c.post(path,json=data,base_url=base,headers={'X-Khotwa-Channel':'live'if live else'demo'})
def login():
    r=c.post('/live',data={'access_token':os.environ['KHOTWA_LIVE_ACCESS_TOKEN']},base_url=base)
    assert r.status_code==303
'''


class RenderDeploymentTests(unittest.TestCase):
    def run_code(self,code):
        env={**os.environ,'GROQ_API_KEY':'','KHOTWA_CONTENT_SIGNING_KEY':'','PYTHONUTF8':'1'}
        result=subprocess.run([sys.executable,'-X','utf8','-c',SETUP+code],cwd=ROOT,env=env,
                              capture_output=True,text=True,encoding='utf8',timeout=120)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_public_demo_never_contacts_provider_and_is_bilingual(self):
        self.run_code('''
assert b'PUBLIC ACADEMIC DEMO' in c.get('/',base_url=base).data
assert c.get('/health',base_url=base).json['workers']==1
for lang in ('en','ar'):
    p=post('/generate',{**SCENARIO['common'],**SCENARIO[lang],'lang':lang})
    assert p.status_code==200 and p.json['_delivery_mode']=='simulated'
    assert p.json['opportunity_score']['assessed_count']==5
    assert p.json['_mode_signature']
    assert post('/discover',{**SCENARIO[lang],'lang':lang}).status_code==200
    assert post('/ask',{'question':'Suggest a question'if lang=='en'else'اقترح سؤالا','lang':lang}).status_code==200
assert not calls
''')

    def test_unauthorized_live_is_blocked_not_simulated(self):
        self.run_code('''
for path,data in [('/generate',{'idea':'A ceramics workshop'}),('/ask',{'question':'Suggest an interview'}),('/discover',{'skills':'Design'})]:
    r=post(path,data,True)
    assert r.status_code==401 and r.json['error']=='live_access_required'
    assert r.json['_delivery_mode']=='blocked'
    assert r.headers['X-Khotwa-Mode']=='live-access-blocked'
assert not calls
''')

    def test_private_login_live_metrics_and_public_tab_remains_demo(self):
        self.run_code('''
assert c.post('/live',data={'access_token':'wrong'},base_url=base).status_code==403
assert c.post('/live',data={'access_token':os.environ['KHOTWA_LIVE_ACCESS_TOKEN']},base_url=base,headers={'Origin':'https://evil.test'}).status_code==403
login()
page=c.get('/live',base_url=base)
assert b'data-live="true"' in page.data
for lang in ('en','ar'):
    p=post('/generate',{**SCENARIO['common'],**SCENARIO[lang],'lang':lang},True)
    assert p.status_code==200 and p.json['_delivery_mode']=='live'
    assert len(p.json['_deployment_metrics']['provider_calls'])==2
    assert not p.json['_deployment_metrics']['simulated_substitution']
    assert p.json['_deployment_channel']=='live'
before=len(calls)
p=post('/generate',{**SCENARIO['common'],**SCENARIO['en']})
assert p.json['_delivery_mode']=='simulated'and len(calls)==before
assert b'data-public-demo="true"' in c.get('/',base_url=base).data
cookie=c.get_cookie(service.COOKIE,domain='example.test')
assert cookie.http_only and cookie.secure and cookie.same_site=='Strict'
c.post('/live/logout',base_url=base)
assert post('/ask',{'question':'Question'},True).status_code==401
''')

    def test_provider_failure_never_falls_back_to_curated_content(self):
        self.run_code('''
login()
with patch.object(service,'json',service.json),patch.object(groq_client,'request_completion',side_effect=AssertionError('unused')):
    # The actual captured provider boundary raises, rather than returning data.
    provider.__code__= (lambda *a,**k:(_ for _ in ()).throw(TimeoutError('synthetic outage'))).__code__
    r=post('/generate',{'idea':'A ceramics workshop'},True)
assert r.status_code==500 and r.json['error']=='generation_failed'
assert r.json['_delivery_mode']=='live'
assert 'Satr'not in json.dumps(r.json)
''')

    def test_export_modes_are_bound_without_bypassing_original_receipts(self):
        self.run_code('''
from pypdf import PdfReader
p=post('/generate',{**SCENARIO['common'],**SCENARIO['en'],'lang':'en'}).json
p['_lang']='en'
r=post('/pdf',p)
assert r.status_code==200
assert all('SIMULATED AI DEMO' in page.extract_text()for page in PdfReader(io.BytesIO(r.data)).pages)
r.close()
q=dict(p);q['_deployment_channel']='live'
assert post('/pdf',q).status_code==403
q=dict(p);q['_content_receipt']={'forged':True}
assert post('/pdf',q).status_code==403
login()
assert post('/pdf',p,True).status_code==403
live=post('/generate',{**SCENARIO['common'],**SCENARIO['en'],'lang':'en'},True).json
assert post('/pdf',live).status_code==403
assert post('/pdf',live,True).status_code==200
''')

    def test_login_throttles_and_does_not_echo_credentials(self):
        self.run_code('''
for i in range(5):
    r=c.post('/live',data={'access_token':'wrong'},base_url=base)
    assert r.status_code==403
r=c.post('/live',data={'access_token':'wrong'},base_url=base)
assert r.status_code==429 and r.headers['Retry-After']=='600'
assert os.environ['GROQ_API_KEY'].encode()not in r.data
assert os.environ['KHOTWA_LIVE_ACCESS_TOKEN'].encode()not in r.data
assert os.environ['KHOTWA_CONTENT_SIGNING_KEY'].encode()not in r.data
''')

    def test_provider_call_budget_blocks_live_without_blocking_demo(self):
        self.run_code('''
os.environ['KHOTWA_LIVE_PROVIDER_CALLS_PER_10MIN']='2'
os.environ['KHOTWA_LIVE_PROVIDER_CALLS_PER_DAY']='2'
login()
payload={**SCENARIO['common'],**SCENARIO['en'],'lang':'en'}
assert post('/generate',payload,True).status_code==200
assert len(calls)==2
r=post('/generate',payload,True)
assert r.status_code==429 and r.json['_delivery_mode']=='live'
assert 'Retry-After'in r.headers and len(calls)==2
assert post('/generate',payload).status_code==200 and len(calls)==2
''')

    def test_expired_and_forged_private_cookies_are_rejected(self):
        self.run_code('''
import time,hmac,hashlib
login()
cookie=c.get_cookie(service.COOKIE,domain='example.test')
c.set_cookie(service.COOKIE,cookie.value[:-1]+('0'if cookie.value[-1]!='0'else'1'),domain='example.test',secure=True)
assert post('/ask',{'question':'Question'},True).status_code==401
login()
with patch.object(service.time,'time',return_value=time.time()+3601):
    assert post('/ask',{'question':'Question'},True).status_code==401
assert not calls
''')


if __name__=='__main__':
    unittest.main()
