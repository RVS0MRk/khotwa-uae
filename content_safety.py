"""Sentence-level model prose validation; no model text can become evidence."""

import re
from html import unescape

MISSING = {"en": "Not provided — describe it in Edit idea", "ar": "لم يُقدّم — صفه في تعديل الفكرة"}


def markup(value):
    if not isinstance(value, str):
        return ""
    for _ in range(10):
        decoded = unescape(value)
        if decoded == value:
            break
        value = decoded
    value = re.sub(r"<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)", "", value, flags=re.I | re.S)
    value = re.sub(r"<br\s*/?>|</(?:p|div|li)>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]*>", "", value)
    value = re.sub(r"!?\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\\([\\`*_{}\[\]()#+.!>|~-])", r"\1", value)
    value = re.sub(r"[`*_#~|]", "", value)
    value = re.sub(r"&(?:#[xX]?[0-9a-fA-F]+|[A-Za-z]+);", "", value)
    value = re.sub(r"\.{2,}", ".", value)
    return " ".join(value.split())


def language_matches(value, lang, idea=""):
    value = str(value or "").replace(idea, "") if idea else str(value or "")
    ar = len(re.findall(r"[\u0600-\u06ff]", value))
    en = len(re.findall(r"[A-Za-z]", value))
    return ar > 0 and ar * 3 >= en if lang == "ar" else en > 0 and en * 3 >= ar


def offending(sentence):
    """Match assertions/actions, never mere topics, prices or percentages."""
    if re.search(
        r'"[^"\n]+"\s*:|^(?:\{|\[)|ignore (?:all|previous) instructions|'
        r"\b(?:return|output|respond with|format as|use)\s+(?:only\s+)?(?:json|markdown|html)\b",
        sentence,
        re.I,
    ):
        return True
    evidence = (
        r"\b(?:research|surveys?|interviews?)\s+(?:shows?|suggests?|found|confirms?|prove)|"
        r"\bcustomers?\s+(?:said|reported|told us|love|prefer|are interested)|"
        r"\b(?:proven|verified|validated|guaranteed)\s+(?:water )?(?:demand|savings|customers?|market|success)|"
        r"\b(?:strong demand|shows promise|identified leads|\d+(?:\.\d+)?\s*%\s+(?:demand|of customers))|"
        r"أظهرت (?:المقابلات|الدراسة)|قال العملاء|طلب (?:مثبت|مؤكد|قوي)|عملاء مؤكدون"
    )
    if re.search(evidence, sentence, re.I) and not re.search(
        r"\b(?:not|never|no|unverified)\b|^This looks promising if interviews confirm demand|لم |لا |^قد.*إذا أكدت المقابلات",
        sentence,
        re.I,
    ):
        return True
    if re.fullmatch(r"(?:mobile )?(?:water.use|waste.disposal|mobile.service) permits?", sentence.strip(" ."), re.I):
        return True
    checking = re.search(
        r"\b(?:check|verify|confirm|ask|before|if|after confirming|once verified)\b|تحقق|راجع|قبل|بعد تأكيد|إذا",
        sentence,
        re.I,
    )
    legal = (
        r"\b(?:you (?:must|need to)|must obtain|obtain|get|pay(?: for| the)?|apply for)\b.{0,65}"
        r"\b(?:DED|licen[cs]e|permit|VAT|tax|government fee)|"
        r"\b(?:licen[cs]e|permit|government fee)\b.{0,45}(?:AED|costs?\s+\d|is required|must be)|"
        r"(?:يجب|يلزم|استخرج|احصل على|ادفع).{0,50}(?:رخص|ترخيص|تصريح|ضريبة)"
    )
    if re.search(legal, sentence, re.I) and not checking:
        return True
    # Imperatives and recommendations to transact/operate are unsafe without a
    # condition verifying official requirements. Describing a business model is allowed.
    unsafe = (
        r"\b(?:take|collect|accept|request)\s+(?:(?:paid|customer)\s+)?(?:deposits?|payments?|money|paid pre.orders?)|"
        r"\bfind paying customers with free (?:washes|services)|"
        r"\b(?:start|begin|launch)\s+(?:operating|selling|commercial|the service)|"
        r"\b(?:run|schedule)\s+(?:(?:a|an|the)\s+)?(?:micro.pilot|actual service)|"
        r"\b(?:offer|provide|deliver|perform|run|start)\s+(?:free |paid |small |real |a |the )*(?:washes|wash|operational pilot|pilot service)|"
        r"(?:اجمع|اقبل|اطلب|خذ).{0,15}(?:عربون|دفعات|دفع)|ابدأ (?:التشغيل|البيع)|قدّم غسيلاً مجانياً"
    )
    if re.search(unsafe, sentence, re.I):
        guarded = re.search(
            r"no.payment|without (?:selling|payment|operating)|do not|never|after (?:confirming|verifying)|once .{0,30}verified|بلا دفع|دون دفع|لا تبدأ|لا تقبل|بعد تأكيد",
            sentence,
            re.I,
        )
        if not guarded:
            return True
    if re.search(r"\b(?:lower|reduce|prevent|cure|improve).{0,25}(?:injury|disease|medical|safety)\b", sentence, re.I):
        return True
    if re.search(
        r"(?:equipment can be sourced|confirmed supplier|supplier quotes confirm|guaranteed return)", sentence, re.I
    ):
        return True
    return False


def safe_text(value, lang="en", fallback="", minimum=12):
    text = markup(value)
    sentences = re.split(r"(?<=[.!?؟])\s+|(?<=[.!?؟])(?=[A-Z])", text)
    kept = [s.strip() for s in sentences if s.strip() and not offending(s)]
    cleaned = " ".join(kept)
    if len(cleaned) < minimum or not language_matches(cleaned, lang):
        return fallback
    return cleaned


def clean_tree(value, lang):
    if isinstance(value, dict):
        return {k: clean_tree(v, lang) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_tree(v, lang) for v in value]
    if isinstance(value, str):
        return safe_text(value, lang, minimum=1)
    return value
