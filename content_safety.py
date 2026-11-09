"""Sentence-level model prose validation; no model text can become evidence."""

import re
import unicodedata
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


def _claim_text(text):
    """Comparison only: preserve original spelling, punctuation and business prose."""
    text = unicodedata.normalize("NFKC", text).lower().replace("’", "'")
    text = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u0640]", "", text)
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)
    return text.translate(str.maketrans("أإآٱى", "ااااي"))


_TRACTION_UNIT = (
    r"(?:pre[ -]?orders?|orders?|customers?|clients?|users?|sign[ -]?ups?|reservations?|subscribers?|members?)"
)
_COUNT = r"\d[\d,]*(?:\s*\+)?"
_EVIDENCE = re.compile(
    r"\b(?:research|surveys?|interviews?)\s+(?:shows?|suggests?|found|confirms?|prove[sd]?)\b|"
    r"\bcustomers?\s+(?:already\s+)?(?:said|reported|told us|love|prefer|are interested)\b|"
    r"\b(?:proven|verified|validated|guaranteed|confirmed)\s+(?:water )?(?:demand|savings|customers?|market|success)\b|"
    r"\b(?:strong demand|shows promise|identified leads|\d+(?:\.\d+)?\s*%\s+(?:demand|of customers))\b|"
    r"\b(?:is|are|was|were|has been|have been|already)\s+(?:not only\s+)?(?:(?:fully|already|commercially)\s+)*"
    r"(?:validated|proven|verified|confirmed|viable|guaranteed|profitable)\b|"
    r"\b(?:we|i|they|you|the business|the service|the product|our business|your business)\s+"
    r"(?:(?:have|has|had)\s+)?(?:already\s+)?(?:have|has|got|received|secured|sold|signed(?: up)?|attracted|gained|acquired)\s+"
    r"(?:(?:over|more than|at least)\s+)?"
    + _COUNT
    + r"\s+(?:(?:paying|repeat|existing|active)\s+)?"
    + _TRACTION_UNIT
    + r"\b|"
    r"\b" + _COUNT + r"\s+(?:customers?|people|users?|clients?)\s+(?:(?:have|has|already)\s+)*"
    r"(?:pre[ -]?ordered|signed up|paid|subscribed|joined|purchased)\b|"
    r"\b(?:we|i|they|you|your business|our business|the business)\s+(?:(?:have|has)\s+)?(?:already\s+)?"
    r"(?:secured repeat orders|achieved profitability|made sales|have paying customers|have existing customers)\b|"
    r"(?:اظهرت|اكدت)\s+(?:المقابلات|الدراسة|الابحاث)|قال العملاء|"
    r"(?:طلب|نجاح|عملاء)\s+(?:مثبت|مؤكد|قوي|مضمون)|عملاء مؤكدون|"
    r"(?:الطلب|الفكرة|السوق|المشروع|المنتج|النجاح)\s+(?:قد\s+)?(?:تم\s+)?"
    r"(?:اثباته|تاكيده|التحقق منه|مثبت|مؤكد|ناجح|مضمون|مربح)|"
    r"(?<!\w)(?:قد\s+)?(?:تم|يتم)\s+(?:بالفعل\s+)?(?:التحقق|اثبات|تاكيد)\b|"
    r"(?:لدينا|لدي|لديك|لديهم|حصلنا علي|حققنا|جذبنا|سجلنا)\s+(?:بالفعل\s+)?"
    r"(?:اكثر من\s+)?"
    + _COUNT
    + r"\s*(?:طلب|عميل|عميلا|عملاء|حجز|مشترك|مستخدم|طلبات|حجوزات)|"
    + _COUNT
    + r"\s*(?:عميل|عميلا|عملاء|اشخاص|مستخدم)\s+(?:قد\s+)?"
    r"(?:دفع|دفعوا|اشترك|اشتركوا|سجل|سجلوا|طلب|طلبوا)|"
    r"(?:حقق|حققنا|حققتم)\s+(?:المشروع\s+)?(?:ارباحا|نجاحا)|"
    r"(?:لدينا|لديك)\s+(?:بالفعل\s+)?(?:عملاء|طلبات|حجوزات)\s+(?:حاليون|حاليين|مؤكدة|مؤكدون)",
    re.I,
)


def _qualified_claim(text, match):
    """Negation/goals qualify this assertion, never an unrelated clause.

    Sentence splitting happens before this function. Commas/conjunctions bound
    the context too, so 'no advertising is needed, demand is proven' is blocked.
    A comma inside a number is not a clause boundary.
    """
    prefix = re.split(
        r"(?<=[.!?؟])\s+|[;؛:،]|,(?!\d)|\b(?:but|however|because|although|and|ولكن|لكن)\b",
        text[: match.start()],
    )[-1]
    suffix = text[match.end() :]
    if re.search(
        r"(?:\b(?:not|never)\s+(?:yet\s+)?|"
        r"\b(?:do not|don't|cannot|can't|never)\s+(?:assume|claim|say)\s+(?:\w+\s+){0,3}|"
        r"\bno\s+(?:evidence|proof|confirmation)\s+(?:\w+\s+){0,5}|"
        r"\b(?:unverified|unsupported)\s+(?:claim|assumption)\s+(?:\w+\s+){0,4}|"
        r"\bwithout\s+(?:evidence|claiming)\s+(?:\w+\s+){0,3}|"
        r"(?<!\w)(?:لم|لن|ليس|ليست|غير)\s+|"
        r"(?<!\w)(?:لا|لم|لن)\s+(?:نفترض|نثبت|نؤكد|نتحقق)\s+(?:ان\s+)?|"
        r"(?<!\w)لا\s+(?:يوجد|يتوفر)\s+(?:اي\s+)?دليل\s+(?:علي\s+)?(?:ان\s+)?)$",
        prefix,
    ):
        return True
    if re.match(
        r"\s+(?:is not|are not|has not been|have not been|remains unverified|غير مثبت|غير مؤكد|لم يثبت)\b", suffix
    ):
        return True
    # A verification condition is not a claim that approvals already exist.
    if re.search(
        r"\b(?:before|after|once|until)\s+(?:(?:official|applicable|necessary|required|legal)\s+)?"
        r"(?:requirements|approvals|permissions|licen[cs]es|permits)\s+$",
        prefix,
    ):
        return True
    # Local future/hypothesis markers, including the exact conditional research
    # construction; a separate sentence or comma-delimited assertion cannot borrow them.
    return bool(
        re.search(
            r"(?:\b(?:if|unless|whether|may|might|could|would|aim to|goal is to|hope to|plan to|target is to|"
            r"hypothetical|suppose|imagine)\b|(?<!\w)(?:اذا|ان ثبت|لو|قد|ربما|نهدف|نسعي|نخطط|نفترض)(?!\w))\s*"
            r"(?:\w+[ -]+){0,8}$",
            prefix,
        )
    )


def _unsupported_evidence(sentence):
    text = _claim_text(sentence)
    return any(not _qualified_claim(text, match) for match in _EVIDENCE.finditer(text))


def offending(sentence):
    """Match assertions/actions, never mere topics, prices or percentages."""
    if re.search(
        r'"[^"\n]+"\s*:|^(?:\{|\[)|ignore (?:all|previous) instructions|'
        r"\b(?:return|output|respond with|format as|use)\s+(?:only\s+)?(?:json|markdown|html)\b",
        sentence,
        re.I,
    ):
        return True
    if _unsupported_evidence(sentence):
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
    cleaned = filter_sentences(value)
    if len(cleaned) < minimum or not language_matches(cleaned, lang):
        return fallback
    return cleaned


def filter_sentences(value):
    """The shared safety boundary, without imposing a language on proper names."""
    text = markup(value)
    sentences = re.split(r"(?<=[.!?؟])\s+|(?<=[.!?؟])(?=[A-Z])", text)
    kept = [s.strip() for s in sentences if s.strip() and not offending(s)]
    return " ".join(kept)


def export_plan(plan):
    """Recheck model prose at export, including older browser-recovered plans.

    Keep the founder's idea, financial inputs and recorded Proof observations
    verbatim. They are labelled user input, not generated/verified evidence.
    Investor notes are a separate, user-authored input outside this plan.
    """

    def visit(value, path=()):
        if path and (path[-1] in ("proof_summary", "_financial_inputs") or path == ("state", "evidence")):
            from copy import deepcopy

            return deepcopy(value)
        if path in (("state", "idea"), ("readiness_report", "idea")) or (
            len(path) == 1 and path[0].startswith("_") and path[0] != "_alternate_plan"
        ):
            from copy import deepcopy

            return deepcopy(value)
        if isinstance(value, dict):
            return {key: visit(child, path + (key,)) for key, child in value.items()}
        if isinstance(value, list):
            return [visit(child, path + (str(i),)) for i, child in enumerate(value)]
        return filter_sentences(value) if isinstance(value, str) else value

    return visit(plan)


def clean_tree(value, lang):
    if isinstance(value, dict):
        return {k: clean_tree(v, lang) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_tree(v, lang) for v in value]
    if isinstance(value, str):
        return safe_text(value, lang, minimum=1)
    return value


def filter_tree(value):
    """Validate every model string before any template or bilingual copy uses it."""
    if isinstance(value, dict):
        return {key: filter_tree(child) for key, child in value.items()}
    if isinstance(value, list):
        return [filter_tree(child) for child in value]
    return filter_sentences(value) if isinstance(value, str) else value
