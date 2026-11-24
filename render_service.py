"""Render entry point: public simulated academic demo; authenticated live AI.

The frozen app, scoring, finance and receipt algorithms are reused. Mode is
request-local, never a process-wide switch, and never falls back from live to
curated responses. Secrets must be configured in Render, not in Git.
"""
from collections import deque
from functools import wraps
import hashlib
import hmac
import io
import json
import os
import platform
import re
import secrets
import time
from threading import Lock

from flask import g, jsonify, make_response, redirect, render_template, request

ACADEMIC_COMMIT = '24eaa98b5c114168b1b8efda5644047e72033e46'
VERSION = 'V2.2.8 Academic Final'
AI_ROUTES = {'/generate', '/discover', '/ask'}
CHANNEL_ROUTES = AI_ROUTES | {'/pdf', '/investment/pdf', '/finance'}
COOKIE = 'khotwa_private_live'


def create_app():
    signing = os.environ.get('KHOTWA_CONTENT_SIGNING_KEY', '')
    if len(signing) < 32:
        raise RuntimeError('Configure a stable KHOTWA_CONTENT_SIGNING_KEY of at least 32 characters before startup.')
    # The production adapter never reads the legacy local credential file.
    configured_groq = os.environ.get('GROQ_API_KEY', '')
    if not configured_groq:
        os.environ['GROQ_API_KEY'] = 'public-demo-provider-not-configured'
    import app as original
    import groq_client
    import material_claims
    from demo_data import plan, ideas, answer

    application = original.app
    application.config['DEBUG'] = False
    application.config['KHOTWA_RENDER_DEPLOYMENT'] = True
    secret = os.environ.get('KHOTWA_LIVE_ACCESS_TOKEN', '')
    live_enabled = len(secret) >= 32 and bool(configured_groq)
    secret_key = signing.encode()
    session_key = hmac.new(secret_key, ('restricted-live-session|'+secret).encode(), hashlib.sha256).digest()
    original_completion = original.call_groq
    original_classifier = material_claims.classify
    transport = groq_client.request_completion
    login_windows, provider_windows = {}, {'ten_minutes': deque(), 'day': deque()}
    lock = Lock()

    def number(name, default):
        try:
            value = int(os.environ.get(name, default))
            return value if 1 <= value <= 10000 else default
        except ValueError:
            return default

    def authorized():
        if not live_enabled:
            return False
        bearer = request.headers.get('Authorization', '')
        if bearer.startswith('Bearer ') and len(bearer) <= 600:
            return hmac.compare_digest(bearer[7:].encode(), secret.encode())
        value = request.cookies.get(COOKIE, '')
        if len(value) > 256:
            return False
        try:
            stamp, nonce, signature = value.split('.')
            timestamp = int(stamp)
            if timestamp > time.time() + 30 or time.time() - timestamp > 3600:
                return False
            expected = hmac.new(session_key, ('live-access|'+stamp+'.'+nonce).encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except (ValueError, TypeError):
            return False

    def same_origin():
        origin = request.headers.get('Origin')
        expected = os.environ.get('RENDER_EXTERNAL_URL', '').rstrip('/') or request.host_url.rstrip('/')
        return (not origin or origin.rstrip('/') == expected) and request.headers.get('Sec-Fetch-Site') != 'cross-site'

    def mode_signature(value, channel):
        binding=json.dumps({'receipt':value.get('_content_receipt'),'id':value.get('_canonical_id'),'channel':channel},
                           sort_keys=True,separators=(',',':')).encode()
        return hmac.new(secret_key,b'render-plan-mode|'+binding,hashlib.sha256).hexdigest()

    def stamp_plan(value, channel):
        if isinstance(value,dict) and value.get('_content_receipt'):
            value['_deployment_channel']=channel
            value['_mode_signature']=mode_signature(value,channel)
            alternate=value.get('_alternate_plan')
            if isinstance(alternate,dict):
                stamp_plan(alternate,channel)

    def deployment_guard():
        g.khotwa_live = False
        g.provider_calls = []
        if request.path == '/live':
            g.khotwa_live = authorized()
        if request.path in CHANNEL_ROUTES:
            channel = request.headers.get('X-Khotwa-Channel', 'demo')
            if channel not in {'demo', 'live'}:
                return jsonify(error='invalid_channel'), 400
            if channel == 'live':
                if not authorized():
                    return jsonify(error='live_access_required', mode='blocked'), 401
                if not same_origin():
                    return jsonify(error='cross_origin_request'), 403
                g.khotwa_live = True
            if request.path in {'/pdf','/investment/pdf'} and request.method=='POST' and request.is_json:
                body=request.get_json(silent=True)
                value=body.get('plan') if isinstance(body,dict) and request.path=='/investment/pdf' else body
                if (not isinstance(value,dict) or value.get('_deployment_channel')!=channel or
                        not isinstance(value.get('_mode_signature'),str) or
                        not hmac.compare_digest(value['_mode_signature'],mode_signature(value,channel))):
                    return jsonify(error='plan_mode_mismatch_regenerate'),403
        if request.path in {'/live', '/live/logout'} and request.method == 'POST' and not same_origin():
            return jsonify(error='cross_origin_request'), 403

    # Authorization and channel selection precede input/route/provider work.
    application.before_request_funcs.setdefault(None, []).insert(0, deployment_guard)

    def measured_transport(*args, **kwargs):
        if not getattr(g, 'khotwa_live', False):
            raise RuntimeError('Provider access is disabled for the public academic demo.')
        now = time.monotonic()
        with lock:
            wait = 0
            for key, window, maximum in (
                ('ten_minutes', 600, number('KHOTWA_LIVE_PROVIDER_CALLS_PER_10MIN', 24)),
                ('day', 86400, number('KHOTWA_LIVE_PROVIDER_CALLS_PER_DAY', 120)),
            ):
                values = provider_windows[key]
                while values and now-values[0] >= window:
                    values.popleft()
                if len(values) >= maximum:
                    wait = max(wait, int(window-(now-values[0]))+1)
            if wait:
                raise groq_client.GroqGenerationError('Restricted live provider-call budget exhausted',
                    {'local_rate_limited':True,'retry_after':min(wait,600)})
            for values in provider_windows.values():
                values.append(now)
        start = time.monotonic()
        diagnostic = {}
        try:
            result = transport(*args, **kwargs)
            diagnostic = result.diagnostics
            return result
        except Exception as exc:
            diagnostic = getattr(exc, 'diagnostics', {})
            raise
        finally:
            allowed = ('http_status','finish_reason','content_empty','completion_tokens','reasoning_tokens')
            record = {key:diagnostic.get(key) for key in allowed if key in diagnostic}
            record.update(duration_ms=round((time.monotonic()-start)*1000),
                          kind='verification' if kwargs.get('max_completion_tokens') == 2400 else 'generation')
            g.provider_calls.append(record)

    def routed_completion(system, user, json_mode=True, history=None, endpoint='/generate'):
        if g.khotwa_live:
            return original_completion(system, user, json_mode, history, endpoint)
        language = (request.get_json(silent=True) or {}).get('lang', 'en')
        value = ideas(language) if endpoint == '/discover' else answer(language) if endpoint == '/ask' else plan(language)
        return json.dumps(value, ensure_ascii=False)

    def routed_classifier(items, api_key):
        if g.khotwa_live:
            return original_classifier(items, api_key)
        # Only the fixed, app-owned rehearsal provider is used in this channel.
        return {item['id']:'noun_phrase' for item in items}

    original.call_groq = routed_completion
    material_claims.classify = routed_classifier
    original.request_completion = groq_client.request_completion = measured_transport

    @application.context_processor
    def deployment_context():
        live = getattr(g, 'khotwa_live', False)
        return {'render_deployment':True,'public_demo':not live,'restricted_live':live,'demo_mode':not live}

    @application.route('/live', methods=['GET','POST'])
    def private_live():
        if request.method == 'POST':
            client = request.headers.get('X-Forwarded-For','').rsplit(',',1)[-1].strip() or request.remote_addr or 'unknown'
            now = time.monotonic()
            with lock:
                for key in list(login_windows):
                    if not login_windows[key] or now-login_windows[key][-1] >= 600:
                        del login_windows[key]
                attempts = login_windows.setdefault(client, deque())
                if len(attempts) >= 5:
                    response = make_response(render_template('live_access.html', unavailable=not live_enabled, error='Too many attempts. Try again in 10 minutes.'),429)
                    response.headers['Retry-After']='600'
                    return response
                attempts.append(now)
            token = request.form.get('access_token','')
            if live_enabled and len(token) <= 512 and hmac.compare_digest(token.encode(),secret.encode()):
                stamp,nonce = str(int(time.time())),secrets.token_hex(12)
                signature=hmac.new(session_key,('live-access|'+stamp+'.'+nonce).encode(),hashlib.sha256).hexdigest()
                response=redirect('/live',code=303)
                response.set_cookie(COOKIE,stamp+'.'+nonce+'.'+signature,max_age=3600,httponly=True,
                                    secure=request.is_secure or os.environ.get('RENDER')=='true',samesite='Strict')
                return response
            return render_template('live_access.html', unavailable=not live_enabled,error='Access was not granted. / لم يُمنح الوصول.'),403
        if authorized():
            return render_template('index.html')
        return render_template('live_access.html',unavailable=not live_enabled,error='')

    @application.post('/live/logout')
    def private_logout():
        response=redirect('/',code=303)
        response.delete_cookie(COOKIE)
        return response

    def health():
        commit=os.environ.get('RENDER_GIT_COMMIT','')
        return jsonify(status='ok',version=VERSION,academic_commit=ACADEMIC_COMMIT,
                       deployed_commit=commit if re.fullmatch(r'[0-9a-f]{40}',commit) else None,
                       public_ai='simulated_academic_demo',live_ai='restricted' if live_enabled else 'disabled',
                       python=platform.python_version(),platform=platform.system(),workers=1)
    application.view_functions['health']=health

    @application.after_request
    def deployment_response(response):
        live=getattr(g,'khotwa_live',False)
        blocked = request.headers.get('X-Khotwa-Channel') == 'live' and not live
        response.headers['X-Khotwa-Mode']='live-access-blocked' if blocked else 'restricted-live' if live else 'public-simulated-demo'
        response.headers['Cache-Control']='no-store' if not request.path.startswith('/static/') else response.headers.get('Cache-Control','no-cache')
        if request.path in AI_ROUTES and response.is_json:
            value=response.get_json()
            if isinstance(value,dict):
                value['_delivery_mode']='blocked' if blocked else 'live' if live else 'simulated'
                if request.path=='/generate' and response.status_code==200:
                    stamp_plan(value,'live' if live else 'demo')
                if live:
                    value['_deployment_metrics']={'provider_calls':g.provider_calls,'simulated_substitution':False}
                response.set_data(application.json.dumps(value))
        if request.path in {'/pdf','/investment/pdf'} and not live and response.status_code==200 and response.mimetype=='application/pdf':
            from pypdf import PdfReader,PdfWriter
            from reportlab.pdfgen import canvas
            response.direct_passthrough=False
            reader=PdfReader(io.BytesIO(response.get_data()));writer=PdfWriter()
            for page in reader.pages:
                overlay=io.BytesIO();c=canvas.Canvas(overlay,pagesize=(float(page.mediabox.width),float(page.mediabox.height)))
                c.setFillColorRGB(.55,.08,.06);c.setFont('Helvetica-Bold',8)
                c.drawCentredString(float(page.mediabox.width)/2,16,'SIMULATED AI DEMO - OBSERVATIONS ARE SELF-REPORTED, NOT INDEPENDENTLY VERIFIED')
                c.save();target=writer.add_page(page);target.merge_page(PdfReader(overlay).pages[0])
            result=io.BytesIO();writer.write(result);response.set_data(result.getvalue())
        return response

    return application


app=create_app()

if __name__=='__main__':
    app.run(host='127.0.0.1',port=int(os.environ.get('PORT','5014')),debug=False,use_reloader=False,threaded=True)
