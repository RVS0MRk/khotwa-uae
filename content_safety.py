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
    text = text.translate(str.maketrans("أإآٱى", "ااااي"))
    return _arabic_matching_copy(text)


_TRACTION_UNIT = (
    r"(?:pre[ -]?orders?|orders?|customers?|clients?|users?|sign[ -]?ups?|reservations?|subscribers?|members?)"
)
_COUNT = r"\d[\d,]*(?:\s*\+)?"
# Categories, not a list of complete claims: a realised state/action plus its
# business context. Present-tense model descriptions ('customers pre-order')
# are deliberately distinct from reported outcomes ('customers have ordered').
_BUSINESS_OBJECT = re.compile(
    r"\b(?:customers?|clients?|users?|people|workers?|members?|subscribers?|sign[ -]?ups?|waitlist|"
    r"orders?|pre[ -]?orders?|subscriptions?|bookings?|purchases?|payments?|buyers?|batches|batch|sales|revenue|profits?|contracts?|agreements?|investors?|"
    r"funding|aed|demand|market|product[ -]market fit|money[ -]maker|interviews?|surveys?|pilot|"
    r"research|data|tests?|business|product|service)\b|"
    r"(?<!\w)(?:وال|ال|و|بال|ل)?(?:عملاء|عميل|مشتركين|مشتركون|مشترك|موظف|موظفين|موظفون|"
    r"مستخدم|مستخدمين|اشخاص|قائمة الانتظار|طلبات|طلب|كميات|دفعات|مبيعات|ايرادات|ارباح|عقود|اتفاقيات|"
    r"مستثمر|مستثمرين|مستثمرون|تمويل|درهم|الاقبال|اقبال|سوق|مقابلات|تجربة|دراسة|بيانات|خدمة|"
    r"مشروع|اشتراكات|حجوزات|مشترين)(?:نا|هم|ه|ا|ات)?(?!\w)",
    re.I,
)
_ACHIEVED = re.compile(
    r"\b(?:sold(?: out)?|signed|joined|paid|paying|committed|invested|raised|grew|achieved|attracted|"
    r"secured|reached|booked|ordered|subscribed|trust(?:s|ed)?|confirmed|showed|established|profitable|"
    r"product[ -]market fit|money[ -]maker|already)\b|"
    r"(?<!\w)(?:و)?(?:حقق(?:نا|ت|وا)?|بعنا|باع(?:وا|ت)?|وقع(?:نا|ت|وا)?|انضم(?:وا|ت)?|"
    r"يدفعون|دفع(?:وا|نا|ت)?|استثمر(?:نا|وا|ت)?|التزم(?:وا|نا|ت)?|نمت|ارتفعت|"
    r"اشترك(?:وا|ت|نا)?|حجز(?:وا|ت|نا)?|مؤكد(?:ة|ون)?|ثابت(?:ة)?|بالفعل|ارباح|مربح(?:ة)?)(?!\w)",
    re.I,
)
_EVIDENCE_SOURCE = re.compile(
    r"\b(?:interviews?|surveys?|(?:our|the) pilot|research|data|tests?)\s+"
    r"(?:confirmed|showed|found|proved|demonstrated)\b|"
    r"(?<!\w)(?:اثبتت|اظهرت|اكدت)\s+(?:المقابلات|التجربة|الدراسة|البيانات)(?!\w)",
    re.I,
)
_DEMAND_CERTAINTY = re.compile(
    r"(?:\b(?:demand|market)\b|(?<!\w)(?:الطلب|الاقبال|السوق)(?!\w)).{0,25}?"
    r"(?:(?:clearly|already|firmly)\s*)?(?P<certainty>established|confirmed|certain|مؤكد|ثابت)",
    re.I,
)
_QUANTIFIED_PEOPLE = re.compile(
    r"\b(?:over\s+|more than\s+|hundreds of\s+|thousands of\s+|\d[\d,]*\s+|"
    r"(?:one|two|three|four|five|six|seven|eight|nine|ten|several)\s+)"
    r"(?:(?:active|corporate|office|paying|regular)\s+){0,2}"
    r"(?:customers?|clients?|users?|people|workers?|members?|subscribers?)\s+"
    r"(?:(?:already|actively|regularly|now)\s+)?"
    r"(?:have|has|are|were|use|choose|recommend|endorse|buy|like|prefer|rely|trust|[a-z]+(?:ed|ing|s))\b|"
    r"(?<!\w)(?:اكثر من\s+)?\d[\d,]*\s+(?:عميل|عميلا|عملاء|مستخدم|مشترك|موظف|اشخاص)"
    r"\s+(?:ي|ت)[\u0621-\u064a]{2,}(?!\w)",
    re.I,
)
_CLAUSE_BOUNDARY = re.compile(r"(?<=[.!?؟])\s+|[;؛:،]|,(?!\d)|\b(?:but|however|because|although|and|ولكن|لكن)\b")
_DIRECTIVE = re.compile(
    r"^\s*[\"'“‘(]*(?:(?:please|first|then)\s+)?"
    r"(?:ask|check|track|test|measure|verify|review|record|compare|find out|investigate|"
    r"aim|target|plan|assume|expect|imagine|suppose|consider)\b|"
    r"^\s*(?:اسال|تحقق|راجع|اختبر|قس|قارن|تتبع|سجل|نهدف|هدفنا|نخطط|نفترض|نتوقع)(?!\w)",
    re.I,
)
_ASSERTIVE_SUBJECT = re.compile(
    r"\b(?:this|our|your|the)\s+(?:idea|business|product|market|demand|concept)\s+"
    r"(?:is|are|has|have|was|were)\b|(?<!\w)(?:الفكرة|المشروع|الطلب|السوق)\s+"
    r"(?:مؤكد|مثبت|ناجح|مضمون|مربح)",
    re.I,
)


def _possessive_stem(word):
    for suffix in ("نا", "ها", "هم", "ك"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            stem = word[: -len(suffix)]
            return stem[:-1] + "ة" if stem.endswith("ت") else stem
    return word


def _arabic_matching_copy(text):
    """Inflections only; derive noun membership from the unchanged patterns."""

    def normalize(match):
        word = match.group()
        stem = _possessive_stem(word)
        if stem != word and _BUSINESS_OBJECT.fullmatch(stem):
            return stem
        # Accusative tanween leaves an alef after diacritic removal.
        if word.endswith("ا") and _ACHIEVED.fullmatch(word[:-1]):
            return word[:-1]
        # Construct-state masculine plural drops the final noon (موظفو المكتب).
        if word.endswith("و") and _BUSINESS_OBJECT.fullmatch(word + "ن"):
            return word + "ن"
        return word

    return re.sub(r"[\u0621-\u064a]+", normalize, text)


def _possessive_outcome_subject(clause):
    # A possessive noun directly before an existing outcome state is a subject,
    # including business names outside the lists. No new noun/verb vocabulary.
    for outcome in _ACHIEVED.finditer(clause):
        before = re.search(r"([\u0621-\u064a]+)\s+$", clause[: outcome.start()])
        if before and _possessive_stem(before[1]) != before[1]:
            return True
    return False


def _participial_description(clause, outcome):
    """An attributive participle without a finite completed-result assertion."""
    if outcome.group() not in {"ordered", "booked", "delivered", "sold", "shipped", "subscribed"}:
        return False
    if re.search(r"\b(?:has|have|had|is|are|was|were|did|does|do|already)\b|\d|\b(?:yesterday|last|so far)\b", clause):
        return False
    prefix = clause[: outcome.start()].strip()
    premodifier = prefix.endswith("pre-")
    if premodifier:
        prefix = prefix[:-4].strip()
    if prefix and (_BUSINESS_OBJECT.search(prefix) or re.search(r"\b(?:i|we|you|they|he|she|it)\b", prefix)):
        return False
    if not re.match(r"\s+(?!out\b)[a-z]+\b", clause[outcome.end() :]):
        return False
    # Post-nominal modifiers introduce how/by whom/for whom the product is
    # ordered. A following direct object instead makes this a finite result
    # ('Office teams ordered all ...'), not a noun modifier.
    if (
        prefix
        and not premodifier
        and not re.match(
            r"\s+(?:online|by|for|to|from|at|in|through|via|with|on|weekly|monthly|daily)\b",
            clause[outcome.end() :],
        )
    ):
        return False
    # Other finite achieved outcomes still invalidate the sentence.
    return all(
        m.group() in {"ordered", "booked", "delivered", "sold", "shipped", "subscribed"}
        for m in _ACHIEVED.finditer(clause)
    )


def _directive_guarded(clause):
    if not _DIRECTIVE.search(clause):
        return False
    # A heading followed by a new factual clause is not a request to check it:
    # 'Test the offer This idea is validated'. Keep genuine interrogative
    # complements, including 'Check whether this idea is validated'.
    for assertion in _ASSERTIVE_SUBJECT.finditer(clause):
        if not re.search(r"\b(?:whether|if|how|when)\b|(?<!\w)(?:هل|اذا)(?!\w)", clause[: assertion.start()]):
            return False
    return True


def _outcome_guarded(clause, start=0):
    """Only this assertion's clause may supply a question, goal or negation."""
    if clause.rstrip().endswith(("?", "؟")) or _directive_guarded(clause):
        return True
    prefix = clause[:start]
    if re.search(
        r"\b(?:if|unless|until|whether|would|could|may|might|will|shall|hypothetical\w*|"
        r"hypothesis|hypotheses|expect(?:s|ed)?|assum(?:e|es|ed|ption)|"
        r"(?:aim|target|goal)s?\s+(?:is|of|to|for)|plans?\s+to|planned\s+to)\b|"
        r"(?<!\w)(?:اذا|لو|حتي|هل|افتراض\w*|قد|ربما|سوف|نهدف|نخطط|نتوقع|هدفنا)(?!\w)",
        prefix,
    ):
        return True
    if re.search(
        r"\b(?:none of|not one of)\s+(?:\w+\s+){0,16}(?:(?:has|have|had|is|was)\s+)?(?:ever\s+|yet\s+)?$|"
        r"\b(?:no one|nobody)\s+(?:(?:has|have|had|is|was)\s+)?(?:ever\s+|yet\s+)?$|"
        r"\b(?:has|have)\s+not\s+(?:\w+\s+){0,3}$|"
        r"\b(?:not|never)\s+(?!only\b)(?:yet\s+|already\s+|been\s+|being\s+)*$|"
        r"\bno\s+(?:\w+\s+){0,2}(?:customer|client|investor|funding|revenue|profit)s?\s+(?:has\s+|have\s+)?$|"
        r"\b(?:unverified|unproven)\s+(?:\w+\s+){0,2}$|"
        r"(?<!\w)لا\s+(?:يوجد|يتوفر)\s+(?:اي\s+)?دليل\s+(?:علي\s+)?(?:ان\s+)?(?:\w+\s+){0,3}$|"
        r"(?<!\w)(?:لم|لا|ليس|ليست|غير)\s+(?:يتم\s+|تم\s+)?$|"
        r"(?<!\w)(?:بلا|دون)\s+(?:بيع\s+او\s+)?$",
        prefix,
    ):
        return True
    return False


def _unsupported_outcome(sentence):
    from publication_policy import negated_clause
    text = _claim_text(sentence)
    for clause in _CLAUSE_BOUNDARY.split(text):
        if negated_clause(clause):
            continue
        # A question mark belongs to this sentence only, never a previous one.
        if clause.rstrip().endswith(("?", "؟")) or _directive_guarded(clause):
            continue
        if not _BUSINESS_OBJECT.search(clause) and not _possessive_outcome_subject(clause):
            continue
        matches = list(_ACHIEVED.finditer(clause)) + list(_EVIDENCE_SOURCE.finditer(clause))
        matches += list(_QUANTIFIED_PEOPLE.finditer(clause))
        for match in matches:
            if _participial_description(clause, match):
                continue
            if not _outcome_guarded(clause, match.start()) and not _qualified_claim(clause, match):
                return True
        for match in _DEMAND_CERTAINTY.finditer(clause):
            if not _outcome_guarded(clause, match.start("certainty")) and not _qualified_claim(clause, match):
                return True
    return False


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
    # Existing precise patterns use the same guards, scoped to this clause.
    # A condition or question in a neighbouring clause cannot exempt a fact.
    local = prefix + _CLAUSE_BOUNDARY.split(text[match.start() :])[0]
    from publication_policy import negated_clause
    if negated_clause(local):
        return True
    if _outcome_guarded(local, len(prefix)):
        return True
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
    if _unsupported_evidence(sentence) or _unsupported_outcome(sentence):
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

    from material_claims import protect_export

    return protect_export(visit(plan))


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
