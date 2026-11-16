"""Independent artifact assertions, called by the browser after real downloads."""
import json
from pathlib import Path
import re
import sys
import unicodedata
from pypdf import PdfReader


def check(file, total, lang, stage):
    from founder_pdf import shape_ar
    from scoring import proof_evidence_text, proof_counts
    pages = PdfReader(file).pages
    first = pages[0].extract_text()
    text = "\n".join(p.extract_text() for p in pages)
    assert re.search(rf"{total}\s*/\s*25", first), first[:2000]
    assert "Incomplete" not in first
    positive = stage in ("five", "changed")
    def compact(value):
        return re.sub(r"\s+", "", "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)))
    assert compact(shape_ar("غير مكتمل")) not in compact(first)
    if lang == "en":
        expected = proof_evidence_text(proof_counts({"total_responses": 5} if positive else {}))
        assert expected in text, expected
        assert expected in first
        assert "Provisional assessment" in first
        if positive: assert compact("Review pilot evidence" if stage == "changed" else "Validate more") in compact(first)
        if positive: assert "No customer feedback entered yet" not in text
    else:
        for word in (("إجابات", "بإقرار", "مستقل") if positive else ("تُسجّل", "ملاحظات")):
            assert compact(word) in compact(text) or compact(shape_ar(word)) in compact(text), word
    Path(file).with_suffix(".txt").write_text(text, encoding="utf-8")
    return {"pages": len(pages), "score": total, "status": "provisional", "self_reported_count": 5 if positive else 0,
            "score_and_narrative_consistent": True}


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    print(json.dumps(check(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])))
