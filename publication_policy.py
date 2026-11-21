"""Clause-local publication policy, independent of an AI's verdict label.

This bounded linguistic policy is not an external fact verifier. Ordinary
descriptions, constraints and research survive. Realised commercial outcomes
and customer promises need a source the model cannot manufacture. Noun classes
describe protected domains, never particular businesses or review sentences.
"""
import re
from contextvars import ContextVar
from functools import wraps

POLICY_VERSION = "v226-1"
_CACHE = ContextVar('publication_checks', default=None)


def publication_scope(function):
    """Bound repeated checks to one operation; never retain visitor text globally."""
    @wraps(function)
    def scoped(*args, **kwargs):
        if _CACHE.get() is not None:
            return function(*args, **kwargs)
        token = _CACHE.set({})
        try:
            return function(*args, **kwargs)
        finally:
            _CACHE.reset(token)
    return scoped


def words(pattern):
    """Unicode whole words; an Arabic marker never matches inside a word."""
    return re.compile(r"(?<!\w)(?:" + pattern + r")(?!\w)", re.I)


_AUX = words(r"is|are|was|were|be|been|has|have|had|does|do|did")
_NEGATIVE = words(r"not|never|no|none|nobody|لم|ليس|ليست|لا|غير")
_HEDGE = words(r"may|might|could|would|likely|possible|potential|proposed|planned|suggested|"
               r"potentially|plans?\s+to|aims?\s+to|intends?\s+to|hopes?\s+to|"
               r"(?:our|my|the)\s+(?:plan|goal|aim|intention)\s+(?:is|was)\s+to|"
               r"نهدف|نسعي|نخطط|نقترح|هدفنا|"
               r"hypothe[st]\w*|assum\w*|projected|forecast|قد|ربما|يمكن|(?:ال)?محتمل[ةه]?|(?:ال)?مقترح[ةه]?|"
               r"(?:ال)?افتراض[\u0621-\u064a]*|فرضية|(?:ال)?متوقع[ةه]?")
_CONDITION = words(r"if|unless|whether|اذا|لو")
_UNCERTAIN = words(r"unknown|unverified|unproven|unconfirmed|untested|uncertain|"
                   r"غير\s+(?:معروف|معروفة|معلوم|معلومة|مثبت|مثبتة|مؤكد|مؤكدة)")
_FUNCTION = words(r"a|an|the|of|for|in|on|at|to|by|with|from|about|through|via|and|or|"
                  r"their|your|our|its|this|that|some|any|all|every|no|في|من|عن|الي|علي|مع|لدي|بين")
_PREPOSITION = re.compile(r"^(?:of|for|in|on|at|to|by|with|from|about|through|via)\b", re.I)
_QUANTITY = words(r"\d[\d,.]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                  r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred\w*|thousand\w*|"
                  r"million\w*|dozen\w*|half|third|quarter|percent|percentage|"
                  r"واحد|واحدة|اثنان|اثنين|ثلاث[ةا]?|اربع[ةا]?|خمس[ةا]?|ست[ةا]?|سبع[ةا]?|ثمان[يةا]*|"
                  r"تسع[ةا]?|عشر[ةا]?|عشرين|ثلاثين|اربعين|خمسين|ستين|سبعين|ثمانين|تسعين|"
                  r"عشرون|ثلاثون|اربعون|خمسون|ستون|سبعون|ثمانون|تسعون|مئة|مئتي|مائة|الف|الاف|نصف|ثلث|ربع|بالمئة|بالمائة")

# Semantic noun classes with regular Arabic inflection and possession.
_EN_RESULT = r"sales|revenues?|income|receipts|turnover|profits?|earnings|funding|financing|"
_EN_RESULT += r"investments?|investors?|backers?|backing|capital|grants?|loans?|credit|rounds?|"
_EN_RESULT += r"contracts?|agreements?|approvals?|licen[cs]es?|permits?|bookings?|appointments?|reservations?|"
_EN_RESULT += r"ratings?|retention|repeat.purchase|customer\s+base|waiting\s+list|waitlist"
_AR_RESULT = r"مبيعات|ايراد(?:ات)?|دخل|ارباح|ربح|عائد(?:ات)?|تمويل|استثمار(?:ات)?|"
_AR_RESULT += r"مستثمر(?:ون|ين)?|قرض|قروض|منح[ةه]?|دعم|عقد|عقود|اتفاقي[ةه]|اتفاقيات|"
_AR_RESULT += r"موافق[ةه]|موافقات|رخص[ةه]?|تراخيص|تصريح|تصاريح|حجز|حجوزات|مواعيد|"
_AR_RESULT += r"تقييم(?:ات)?|نجوم|احتفاظ|قائم[ةه]\s+(?:ال)?انتظار|قاعدة\s+عملاء"
_RESULT = words(_EN_RESULT + r"|(?:و|ف|ب|ل)?(?:ال)?(?:" + _AR_RESULT + r")(?:نا|ها|هم|كم|ه|ك)?")
_COST = words(r"costs?|fees?|bills?|spending|budget|money|time|wages?|income|earnings|"
              r"(?:ال)?(?:تكلف[ةه]|تكاليف|نفقات|مصروفات|فاتور[ةه]|رسوم|ميزاني[ةه]|مال|اجور|اجر|وقت|دخل)(?:نا|ها|هم|ك)?")
_PEOPLE = words(r"customers?|clients?|users?|members?|subscribers?|buyers?|riders?|couriers?|"
                r"(?:ال)?(?:عميل|عملاء|زبون|زبائن|مشترك(?:ون|ين)?|مستخدم(?:ون|ين)?|"
                r"سائق(?:ون|ين|و)?|موظف(?:ون|ين|و)?|راكب|ركاب)(?:نا|ها|هم|ك|ا)?")
_CURRENCY = words(r"aed|usd|dirhams?|dollars?|درهم(?:ا)?|دراهم|دولار(?:ا)?")
_CONSTRAINT = words(r"needs?|requires?|depends?\s+on|limited|limits?|constraints?|capacity|"
                    r"adds?\s+(?:\w+\s+){0,2}cost|costly|expensive|difficult|unclear|"
                    r"تحتاج|يحتاج|تتطلب|يتطلب|تضيف\s+تكلف[ةه]|محدود[ةه]?|صعب[ةه]?|"
                    r"يصعب|تكلف[ةه]|تكاليف|قدرة|القدرة|طاقة|الطاقة")
_CURRENT = words(r"already|now|currently|yesterday|ago|so\s+far|last|loyal|regular|"
                 r"بالفعل|الان|حاليا|امس|الماضي|الماضية|منذ|دائم(?:ا|ة|ين)?|فعلي[ةا]?")
_STATE = words(r"profitable|cash.positive|proven|validated|approved|granted|full|filled|"
               r"successful|succeeded|sold\s+out|(?:ال)?(?:رابح|مربح|ناجح|مثبت|مؤكد|معتمد|"
               r"مكتمل|ممتلئ|مكتظ|محجوز|ممنوح)(?:[ةه]|ون|ين|ا)?|نجح(?:ت|نا|وا)?")
_IRREGULAR = words(r"became|began|bought|brought|built|came|chose|did|drove|fell|felt|found|"
                   r"gave|got|grew|held|kept|led|left|lost|made|met|paid|ran|rose|said|sold|"
                   r"sent|set|spent|stood|took|went|won|was|were|had|"
                   r"كان|كانت|اصبح|اصبحت|صار|صارت|بات|باتت|ظل|ظلت")


def normalize(text):
    from content_safety import _claim_text
    return _claim_text(str(text or ""))


def clauses(text):
    """Analysis only: never publish these clause tails as sentences."""
    value = normalize(text)
    value = re.sub(
        r"\s+[وف](?=(?:ال|لدي|لدينا|لديهم|نحن|هم|هو|هي|لم|لن|لا|قد|سوف)\b|"
        r"ال[\u0621-\u064a]+|[يتن][\u0621-\u064a]{2,}\b|[\u0621-\u064a]{2,}(?<!ا)(?:ت|نا|وا)\b)",
        ";", value,
    )
    return [s.strip() for s in re.split(r"(?<=[.!?؟])\s+|[;؛:،]|,(?!\d)|\b(?:but|however|because|although|and|ولكن|لكن)\b", value) if s.strip()]


def sentences(text):
    """Complete original sentences only; a semicolon is not a new sentence.

    Accept a redundant semicolon *after* a full stop without turning the
    following conjunction/relative tail into a new, manufactured statement.
    """
    return [part.strip(' ;؛') for part in re.split(r"(?<=[.!?؟])(?:\s+|(?=[;؛A-Z]))", text) if part.strip(' ;؛')]


def _negative_promise(value):
    """A future/absolute prediction is not a denial of an achieved state."""
    if re.match(r"^ابدا\s+ب[\u0621-\u064a]+", value):
        # Normalization makes ابدأ (start!) and أبدا (ever) identical. The
        # initial imperative plus a prepositional object is not an adverb.
        return False
    negative = re.search(r"\b(?:will|shall|would)\s+(?:never|always|not)\b|"
                         r"\b(?:no\b.{0,65}|nobody\b.{0,40})(?:will|shall)\b|"
                         r"\b(?:never|always)\b|(?<!\w)(?:لن|ابدا|دائما)(?!\w)", value)
    if not negative:
        negative = re.search(r"(?<!\w)لا\s+[يت][\u0621-\u064a]{2,}(?!\w)", value)
    if not negative:
        return False
    if re.search(r"(?<!\w)لا\s+(?:يوجد|توجد|يتوفر|تحتاج|يحتاج|تتطلب|يتطلب)(?!\w)", value):
        return False
    if re.search(r"\b(?:do\s+not|never|cannot|can't)\s+(?:assume|claim|promise|say|infer)\b|"
                 r"(?<!\w)(?:لا|لن|لم)\s+(?:نفترض|نؤكد|ندعي|نعد|تعد|تفترض|تدعي)(?!\w)", value):
        return False
    if re.search(r"\b(?:has|have|had)\s+never\b", value):
        return False
    if _RESULT.search(value) and not _COST.search(value) and not re.search(r"\b(?:will|shall)\b|(?<!\w)لن(?!\w)", value):
        return False
    return True


def negated_clause(clause):
    """Local current/past denial; an adjacent assertion cannot borrow it."""
    value = normalize(clause)
    if _negative_promise(value) or re.search(r"\bnot\s+only\b|ليس\s+فقط", value):
        return False
    uncertainty = _UNCERTAIN.search(value)
    if uncertainty:
        before, after = value[:uncertainty.start()], value[uncertainty.end():].strip(" .")
        if (not after or re.match(r"^(?:whether|if|to|ما\s+اذا|اذا|ان)\b", after)) and (
                not before.strip() or _AUX.search(before) or re.search(r"remains?|ما\s+زال|من\s*$", before)):
            return True
    if re.search(r"\bno\s+(?:new\s+|customer\s+)?(?:evidence|proof|confirmation)\b|"
                 r"(?<!\w)لا\s+(?:يوجد|توجد|يتوفر)\s+(?:اي\s+)?(?:دليل|ادلة)(?!\w)", value):
        return True
    negative = _NEGATIVE.search(value)
    if not negative:
        return False
    # An unpunctuated new subject/predicate is outside the denial's scope.
    from content_safety import _ASSERTIVE_SUBJECT
    if _ASSERTIVE_SUBJECT.search(value[negative.end():]) and not re.search(
            r"(?<!\w)(?:نفترض|ندعي|نؤكد|نعد|دليل)(?!\w)|\b(?:assume|claim|promise|evidence)\b", value):
        return False
    if re.search(r"\bif\b|(?<!\w)ان(?!\w)", value[:negative.start()]):
        return False  # A refund 'if not satisfied' is not a denial of refund.
    if re.search(r"\b(?:no|zero)\s+(?:[a-z-]+\s+){0,4}(?:costs?|fees?|charges?)\b", value):
        return False
    tail = value[negative.end():]
    tail = re.sub(r"\b(has|have|had)\s+(?:not\s+)?been\b", r"\1", tail)
    auxiliaries = [m for m in _AUX.finditer(tail) if m.group() not in {'be', 'been'}]
    leading = bool(re.match(r"^(?:no|none|nobody|not one)\b", value))
    if len(auxiliaries) > (1 if leading else 0):
        return False
    if leading and auxiliaries:
        subject = tail[:auxiliaries[0].start()]
        if re.search(r"\b\w+ed\s+\w+\s*$", subject) and not re.search(r"\b(?:who|that|you|we|they)\b", subject):
            return False
    if re.search(r"\b(?:will|shall)\b|(?<!\w)لن(?!\w)", value):
        return False
    return True


def _qualified(value, predicate):
    for match in list(_HEDGE.finditer(value)) + list(_CONDITION.finditer(value)):
        if match.start() <= predicate:
            return True
    # An until-clause, unlike a calendar bound ('until March').
    return bool(re.match(r"^until\s+\w+\s+\w+", value) and not re.match(r"^until\s+(?:next|last|this|the)\b", value))


def _research(value):
    from material_claims import _ACTION, _QUESTION
    from content_safety import _ASSERTIVE_SUBJECT
    action = re.match(_ACTION.pattern.translate(str.maketrans("أإآٱى", "ااااي")), value, re.I)
    question = (_QUESTION.search(value) or re.match(r"^(?:whether|ما\s+اذا)\b", value) or
                re.match(r"^[وف]?(?:هل|كيف|ما|ماذا|اي|متي|اين|لماذا)(?!\w)", value))
    if value.rstrip(' .').endswith(("?", "؟")) or question:
        return True
    if not action:
        return False
    first = value.split()[0].strip('.,:')
    if _RESULT.fullmatch(first) and (_CURRENCY.search(value) or _STATE.search(value) or
                                      (_QUANTITY.search(value) and len(list(_RESULT.finditer(value))) > 1)):
        return False  # Nominal assessment/rating is not an imperative verb.
    if _ASSERTIVE_SUBJECT.search(value) and not _CONDITION.search(value):
        return False
    return not re.search(r"\b(?:we|our\s+\w+|it)\s+(?:has|have|earned|received|is|was)\b", value)


def _promise(value):
    if _negative_promise(value):
        return True
    if negated_clause(value):
        return False
    if _research(value) and not re.match(r"^(?:offer|give|provide|guarantee)\b", value):
        return False
    # A nominal pricing assumption is not an asserted offer. Require its own
    # copular predicate; a hedge appended to an earlier finite claim cannot help.
    hypothesis = re.search(r"\b(?:is|are)\s+(?:an?\s+)?(?:\w+\s+){0,2}(?:hypothesis|assumption)\b", value)
    if hypothesis and not _finite(value[:hypothesis.start()]):
        return False
    offer_words = r"\b(?:free|complimentary|refund\w*|discount\w*|guarantee\w*)\b|(?<!\w)(?:مجاني[ةها]?|خصم[\u0621-\u064a]*|نضمن|مضمون[ةها]?)(?!\w)"
    if re.search(offer_words, value):
        without_research_offer = re.sub(r"\bfree(?:[ -]+no[ -]+payment)?[ -]+(?:waitlist|reservation|interest\s+form)\b|"
                                       r"(?:قائمة\s+(?:ال)?انتظار|قائمة\s+اهتمام|حجز)\s+مجاني[ةه]?", "", value)
        if re.search(offer_words, without_research_offer):
            return True
    if re.search(r"\b(?:zero|no)\s+(?:[a-z-]+\s+){0,4}(?:costs?|charges?|fees?)\b|"
                 r"(?<!\w)(?:بلا\s+مقابل|دون\s+تكلفة|بدون\s+تكلفة)(?!\w)", value):
        return True
    deadline = re.search(r"\b(?:within|under|no\s+more\s+than|by)\b|(?<!\w)(?:خلال|قبل|اكثر\s+من)(?!\w)", value)
    service = re.search(r"\b(?:deliver\w*|respond\w*|response|repair\w*|completion|wait\w*)\b|"
                        r"(?<!\w)(?:[سنيوت]*سلم[\u0621-\u064a]*|[سنيوت]*رد|اصلاح|توصيل|صيانة|انتظار)(?!\w)", value)
    duration = words(r"minutes?|hours?|days?|noon|midnight|دقيق[ةه]|دقائق|ساعة|ساعات|يوم|ايام|الظهر|الليل").search(value)
    if deadline and service and duration and not _qualified(value, min(deadline.start(), service.start())):
        return True
    benefit = re.search(r"\b(?:sav\w*|earn\w*|cut\w*|halv\w*|reduc\w*|lower\w*|retain\w*)\b|"
                        r"(?<!\w)(?:[يتن]وفر[\u0621-\u064a]*|[يتن]قلل[\u0621-\u064a]*|"
                        r"[يتن]خفض[\u0621-\u064a]*|[يتن]حتفظ)(?!\w)", value)
    if benefit and _COST.search(value) and (_QUANTITY.search(value) or re.search(r"\b(?:your|their)\b|للعميل|للسائق|للراكب", value)):
        return not _qualified(value, benefit.start())
    share = words(r"half|third|quarter|percent|percentage|نصف|ثلث|ربع|بالمئة|بالمائة").search(value)
    if _COST.search(value) and share and re.search(r"\b(?:your|their)\b|للعميل|للسائق|للراكب", value):
        predicate = min(_finite(value) or [share.start()])
        if not _qualified(value, predicate):
            return True
    reversal = words(r"back|returned|refunded|[يتنس]*رد").search(value)
    if reversal and _COST.search(value) and not _qualified(value, min(_finite(value) + [reversal.start()])):
        return True
    return False


def _finite(value):
    """Candidate predicates; a plural noun/currency token is not a verb."""
    positions = [m.start() for m in _AUX.finditer(value)] + [m.start() for m in _IRREGULAR.finditer(value)]
    for match in re.finditer(r"\b[a-z][a-z-]*(?:ed|s)\b", value):
        token = match.group()
        before, after = value[:match.start()], value[match.end():].strip()
        if not before.strip() or token == 'aed' or _RESULT.fullmatch(token) or _PEOPLE.fullmatch(token):
            continue
        if _PREPOSITION.match(after) or token.startswith('pre-'):
            continue
        if token.endswith('ed') and re.match(r"^(?:by|for|with|to|from|daily|weekly|monthly)\b", after):
            continue
        positions.append(match.start())
    # Bare/irregular predicates after a material subject and optional PP.
    for head in _RESULT.finditer(value):
        match = re.match(r"\s+(?:(?:of|for|at|from|in)\s+[\w'-]+\s+)?([a-z][a-z-]*)\b", value[head.end():])
        if match and not _FUNCTION.fullmatch(match[1]):
            positions.append(head.end() + match.start(1))
    for match in re.finditer(r"(?<!\w)[\u0621-\u064a]{3,}(?!\w)", value):
        word = match.group()
        if word.startswith('ال') or _RESULT.fullmatch(word) or _PEOPLE.fullmatch(word):
            continue
        if (word.startswith(('است','ان','ات')) or word.startswith(('ي','ت','ن'))
                or word.endswith(('ت','وا','نا')) and not word.endswith(('ات','ية'))):
            positions.append(match.start())
    return sorted(set(positions))


def ungrounded_assertion(text):
    cache = _CACHE.get()
    if cache is not None and text in cache:
        return cache[text]
    result = _ungrounded_assertion(text)
    if cache is not None and len(cache) < 1024:
        cache[text] = result
    return result


def _ungrounded_assertion(text):
    """Only material achievements/promises, not ordinary finite descriptions.

    A noun-phrase label grants no permission. Independent non-material facts,
    constraints and definitions can pass even when the model mislabels them.
    """
    from content_safety import _ACHIEVED, _BUSINESS_OBJECT, _participial_description
    for value in clauses(text):
        if _promise(value):
            return True
        if negated_clause(value) or _research(value):
            continue
        heads = list(_RESULT.finditer(value))
        finite = _finite(value)
        outcomes = [m for m in _ACHIEVED.finditer(value) if not _participial_description(value, m)
                    and not re.search(r"\bwithout\s+(?:\w+\s+(?:or|and)\s+)*$|"
                                      r"(?<!\w)(?:بلا|دون|بدون)\s+(?:[\u0621-\u064a]+\s+(?:او|و)\s+)*$", value[:m.start()])]
        positions = finite + [m.start() for m in outcomes]
        amount, currency, state = _QUANTITY.search(value), _CURRENCY.search(value), _STATE.search(value)
        if heads and (amount or state):
            positions += [m.start() for m in (amount,state) if m]
        predicate = min(positions or [len(value)])
        if _qualified(value, predicate):
            continue
        if _CONSTRAINT.search(value) and not state and not outcomes:
            continue
        # Indefinite service + passive modifier + request/method adjunct is a
        # workflow description. Quantified, current, full or named outcomes do
        # not have this shape (and must not be mistaken for modifiers).
        if heads and not value.startswith('ال') and not amount and not currency and not _CURRENT.search(value) and not re.search(
                r"بالكامل|تماما|جميع|(?<!\w)(?:كل|لدينا|لديهم|نحن)(?!\w)", value):
            if re.search(r"(?<!\w)م[\u0621-\u064a]{2,}و[\u0621-\u064a]+\s+(?:وفق|حسب|بطلب|بناء\s+علي)\b", value):
                continue
        if heads and (finite or amount or currency or state):
            if not finite and not state and not currency and amount and re.search(r"\b(?:required|needed|checklist|requirements)\b|متطلبات|مطلوب", value):
                continue
            return True
        if len(heads) > 1 and not re.search(r"متطلبات|\brequirements\b|\bchecklist\b", value):
            between = value[heads[0].end():heads[-1].start()].strip()
            if between and not _PREPOSITION.match(between):
                return True
        if heads:
            # Indefinite Arabic passive/augmented participle following a
            # material subject: a nominal predication, not a noun-phrase label.
            for match in re.finditer(r"(?<!\w)م[\u0621-\u064a]{3,}(?!\w)", value):
                token = match.group()
                participle = bool(re.match(r"م[\u0621-\u064a]{1,3}و[\u0621-\u064a]+$|م[تنس][\u0621-\u064a]{3,}$|م[\u0621-\u064a]ت[\u0621-\u064a]{2,}$", token))
                if match.start() > heads[0].end() and participle and not _qualified(value, match.start()):
                    return True
        if state and words(r"profitable|cash.positive|رابح[ةه]?|مربح[ةه]?").fullmatch(state.group()):
            return True
        if state and (_BUSINESS_OBJECT.search(value) or re.search(r"\b(?:already|pilot)\b|تجربة|منذ", value)):
            return True
        if outcomes and (_BUSINESS_OBJECT.search(value) or _PEOPLE.search(value)):
            return True
        people = _PEOPLE.search(value)
        if people and ((amount and finite) or (_CURRENT.search(value) and finite)):
            return True
        if people and amount and amount.start() < people.start() and re.search(r"(?<!\w)(?:لدي|عند)(?:نا|ها|هم|ه|كم)?(?!\w)", value[:amount.start()]):
            return True
        if re.search(r"\b(?:rel(?:y|ies|ied)|depend(?:s|ed)?)\s+on\b|(?<!\w)(?:يعتمد|تعتمد|يثق|تثق)(?!\w)", value) and (people or _CURRENT.search(value)):
            return True
        if amount and finite and (_CURRENT.search(value) or re.search(r"\b(?:last|after\s+the\s+launch)\b|الماضي|الماضية", value)):
            return True
        if currency and amount and finite:
            return True
    return False
