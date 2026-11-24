"""Loopback-only offline university rehearsal; never a production entry point.

Run: python demo_server.py --port 5010
All provider outputs are fixed fictional data. Actual routing, normalization,
finance, scoring, Proof Mode and signed export validation run normally.
"""
import argparse
import io
import json
import os
from pathlib import Path
import re
import secrets


def create_demo_app():
    # Explicit dummy credential prevents the legacy local secret-file fallback.
    # The stable rehearsal key is generated locally, ignored by Git and never
    # included in archives. It is not a production credential.
    os.environ['GROQ_API_KEY'] = 'offline-demo-no-provider-access'
    # Rehearsal-only, loopback quotas. No paid provider calls are possible.
    # Production defaults in app.py are deliberately unchanged.
    os.environ.setdefault('KHOTWA_AI_CLIENT_PER_10MIN', '300')
    os.environ.setdefault('KHOTWA_AI_GLOBAL_PER_10MIN', '600')
    os.environ.setdefault('KHOTWA_PDF_CLIENT_PER_10MIN', '60')
    key_path = Path(__file__).resolve().parent / 'outputs/.demo-signing-key'
    key_path.parent.mkdir(exist_ok=True)
    if not key_path.exists():
        key_path.write_text(secrets.token_hex(32), encoding='ascii')
    os.environ['KHOTWA_CONTENT_SIGNING_KEY'] = key_path.read_text(encoding='ascii').strip()
    import app as application
    import config
    import material_claims
    from flask import request
    import requests
    from demo_data import plan, ideas, answer

    config.GROQ_API_KEY = application.API_KEY = 'offline-demo-no-provider-access'
    def blocked_network(*args, **kwargs):
        raise RuntimeError('Network access is disabled in the offline rehearsal.')
    requests.post = blocked_network

    def completion(system, user, json_mode=True, history=None, endpoint='/generate'):
        # Only these curated responses can be emitted, independent of input
        # injection. This is deliberately not a simulated general-purpose AI.
        language = (request.get_json(silent=True) or {}).get('lang', 'en')
        value = ideas(language) if endpoint == '/discover' else answer(language) if endpoint == '/ask' else plan(language)
        return json.dumps(value, ensure_ascii=False)
    application.call_groq = completion
    material_claims.classify = lambda items, _key: {item['id']:'noun_phrase' for item in items}
    flask_app = application.app
    flask_app.jinja_env.globals['demo_mode'] = True
    flask_app.config['KHOTWA_OFFLINE_DEMO'] = True

    @flask_app.after_request
    def label_demo(response):
        response.headers['X-Khotwa-Mode'] = 'offline-simulated-demo'
        if response.mimetype == 'application/pdf' and response.status_code == 200:
            # The route first verifies the real content receipt. Add a visible
            # rehearsal label afterwards; no signature check is bypassed.
            from pypdf import PdfReader, PdfWriter
            from reportlab.pdfgen import canvas
            response.direct_passthrough = False
            reader = PdfReader(io.BytesIO(response.get_data()))
            writer = PdfWriter()
            for page in reader.pages:
                overlay = io.BytesIO()
                c = canvas.Canvas(overlay, pagesize=(float(page.mediabox.width), float(page.mediabox.height)))
                c.setFillColorRGB(.55,.08,.06)
                c.setFont('Helvetica-Bold', 8)
                c.drawCentredString(float(page.mediabox.width)/2, 16, 'SIMULATED DEMO DATA - NOT LIVE AI OR CUSTOMER RESEARCH')
                c.save()
                target = writer.add_page(page)
                target.merge_page(PdfReader(overlay).pages[0])
            result = io.BytesIO()
            writer.write(result)
            response.set_data(result.getvalue())
        return response

    @flask_app.get('/demo-status')
    def demo_status():
        return {'mode':'offline-simulated-demo', 'live_ai':False, 'version':'V2.2.8 Academic Final', 'network':'provider disabled'}

    return flask_app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5010)
    args = parser.parse_args()
    print('Khotwa V2.2.8 Academic Final | SIMULATED OFFLINE REHEARSAL | http://127.0.0.1:' + str(args.port), flush=True)
    create_demo_app().run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False, threaded=True)
