"""Test the isolated demo adapter in a subprocess; never contaminate app:app."""
from pathlib import Path
import os
import subprocess
import sys
import unittest


class OfflineDemoTests(unittest.TestCase):
    def test_bilingual_rehearsal_is_labeled_network_free_and_uses_real_exports(self):
        code = '''
import io,json
from demo_server import create_demo_app
from demo_data import SCENARIO,FINANCE
from pypdf import PdfReader
from finance import calculate
app=create_demo_app();c=app.test_client()
assert c.get('/demo-status').json['live_ai'] is False
html=c.get('/').data.decode()
assert 'SIMULATED DATA' in html and 'data-demo="true"' in html
assert 'demo.css' in html
for lang in ('en','ar'):
    response=c.post('/discover',json={**SCENARIO[lang],**SCENARIO['common'],'lang':lang})
    assert response.status_code==200
    assert response.json['ideas'][0]['name']==('سطر' if lang=='ar' else 'Satr')
    r=c.post('/generate',json={**SCENARIO[lang],**SCENARIO['common'],'lang':lang})
    assert r.status_code==200
    p=r.json
    assert p['opportunity_score']['assessed_count']==5 and p['opportunity_score']['total']==17
    assert p['first_step_today'].startswith('ارسم اليوم' if lang=='ar' else 'Sketch a bilingual')
    assert p['_content_receipt']
    p['_lang']=lang
    response=c.post('/pdf',json=p)
    assert response.status_code==200
    texts=[page.extract_text() for page in PdfReader(io.BytesIO(response.data)).pages]
    assert all('SIMULATED DEMO DATA' in text for text in texts)
    response.close()
    response=c.post('/investment/pdf',json={'plan':p,'finance':{'inputs':FINANCE},'lang':lang})
    assert response.status_code==200
    assert all('SIMULATED DEMO DATA' in page.extract_text() for page in PdfReader(io.BytesIO(response.data)).pages)
    response.close()
    response=c.post('/ask',json={'question':'Suggest a question' if lang=='en' else 'اقترح سؤالا','lang':lang})
    assert response.status_code==200
    assert ('محاكى' if lang=='ar' else 'Simulated') in response.json['answer']['title']
r=calculate(FINANCE)
assert r['startup_capital']=='4300.00' and r['operating_profit']=='2140.00'
assert r['funding_gap']=='-1700.00' and r['break_even_units']==40
assert r['payback_months']=='1.19' and r['runway_months'] is None
import requests
try: requests.post('https://api.groq.com')
except RuntimeError: pass
else: raise AssertionError('Offline demo must block the provider')
print('PASS: bilingual simulation labels, discovery, 17/25, Advisor, Founder and Investment exports, finance, provider blocked')
'''
        result = subprocess.run([sys.executable, '-X', 'utf8', '-c', code],
                                cwd=Path(__file__).resolve().parent, env={**os.environ,'GROQ_API_KEY':''},
                                capture_output=True, text=True, encoding='utf-8', timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS:', result.stdout)

    def test_production_template_has_no_rehearsal_banner(self):
        code = '''
from test_support import configure_mock_environment
configure_mock_environment()
import app
html=app.app.test_client().get('/').data.decode()
assert 'data-demo="true"' not in html
assert 'SIMULATED DATA' not in html
assert '/demo-status' not in {rule.rule for rule in app.app.url_map.iter_rules()}
'''
        result = subprocess.run([sys.executable,'-X','utf8','-c',code], cwd=Path(__file__).resolve().parent,
                                capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
