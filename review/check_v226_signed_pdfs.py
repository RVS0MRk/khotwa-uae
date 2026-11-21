"""Fresh actual PDF routes with deliberately incorrect classifier labels.

Synthetic inputs only. A valid receipt is additionally made over unsafe text
to demonstrate that a signature is integrity, not factual/safety approval.
"""
from copy import deepcopy
import io
import json
import re
from pathlib import Path
import sys
import unicodedata
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from test_v226 import V226Tests, CASES
from content_safety import export_plan
from pypdf import PdfReader
import material_claims as gate
import provenance
from test_finance import BASE
from test_v22_content import fixture


def main():
    output = ROOT / 'outputs/v226-signed-pdf-probes'
    output.mkdir(parents=True, exist_ok=True)
    test = V226Tests(); test.setUp(); rows = []
    try:
        for native in ('en', 'ar'):
            raw = fixture('v224_live_lunch_ar' if native == 'ar' else 'v226_rich_lunch')
            plan = test.generate(raw, lang=native)
            assert plan['opportunity_score']['total'] == 18
            normal = test.client.post('/pdf', json=dict(plan, _lang=native))
            assert normal.status_code == 200
            first = PdfReader(io.BytesIO(normal.data)).pages[0].extract_text()
            assert re.search(r'18\s*/\s*25', first)
            name = f'founder-{native}-personalized-18.pdf'
            (output/name).write_bytes(normal.data); normal.close()
            rows.append({'file':name,'native':native,'kind':'legitimate personalized assessment','dashboard_total':18,'actual_pdf_total':18,'assessed_dimensions':5})
            for index in (0, 17, 18, 27):
                marker = f'V226REJECT{native.upper()}{index}'
                # Keep a Latin marker inside the same rejected sentence: an
                # Arabic logical-string search alone could falsely pass after
                # bidi shaping/reordering in the PDF text stream.
                bad = CASES['independent_unsafe'][native][index].rstrip('.!?؟') + f' {marker}.'
                with patch.object(gate, 'classify', side_effect=lambda items,key:{i['id']:'noun_phrase' for i in items}):
                    checked, _ = gate.verify_model({'summary':bad}, {'idea':'Proposed repair service'}, native, 'synthetic')
                assert checked['summary'] == ''
                dirty = deepcopy(plan)
                dirty['summary'] = bad
                dirty['opportunity_score']['local_fit']['reason'] = bad
                provenance.seal(dirty, provenance.sources({}, dirty))
                receipt = deepcopy(dirty['_content_receipt'])
                assert provenance.verified_receipt(dirty)
                clean = export_plan(dirty)
                assert bad not in json.dumps(clean, ensure_ascii=False)
                assert clean['opportunity_score']['local_fit']['score'] is None
                for kind, route, body in (
                    ('founder', '/pdf', dict(dirty, _lang=native)),
                    ('investment', '/investment/pdf', {'plan':dirty,'finance':{'inputs':BASE},'lang':native}),
                ):
                    response = test.client.post(route, json=body)
                    assert response.status_code == 200
                    text = unicodedata.normalize('NFKC', '\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(response.data)).pages))
                    assert bad not in text
                    assert marker not in text
                    assert '\u25a0' not in text and '\ufffd' not in text
                    if kind == 'founder':
                        first = unicodedata.normalize('NFKC', PdfReader(io.BytesIO(response.data)).pages[0].extract_text())
                        assert ('غير مكتمل' if native == 'ar' else 'Incomplete') in first
                    file = output / f'{kind}-{native}-claim-{index}.pdf'
                    file.write_bytes(response.data); response.close()
                    rows.append({'file':file.name,'route':route,'native':native,'claim_index':index,'valid_unsafe_receipt_rechecked':True,'rejected_dimension':True,'bad_absent_from_renderable_plan':True,'latin_marker_absent_from_actual_pdf':True,'replacement_glyphs':False})
                assert dirty['_content_receipt'] == receipt
    finally:
        test.doCleanups()
    (output/'results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'PASS {len(rows)} actual signed PDF exports: two legitimate personalized 18/25 reports plus 16 rejected EN/AR achievements, savings, income and time guarantees; unsafe dimension removed, original receipt unchanged. No live Groq.')


if __name__ == '__main__':
    main()
