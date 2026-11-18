"""Deterministic publication permission, independent of model verdict labels.

There is no external-achievement attestation input in Khotwa. Model text can
describe a proposal, ask a question or recommend research; it cannot supply its
own evidence. Reuse the existing material-claim ontology, with grammatical
predication checks rather than extending lists of commercial success phrases.
User statements and calculated projections have separate source-bound paths.
"""
import re

POLICY_VERSION = "v225-1"

_NEGATIVE = re.compile(r"\b(?:not|never|no|none|nobody)\b|(?<!\w)(?:لم|لن|لا|ليس|ليست|غير)(?!\w)", re.I)
_AUX = re.compile(r"\b(?:is|are|was|were|has|have|had|does|do|did)\b", re.I)
_MODAL = re.compile(r"\b(?:if|unless|until|whether|can|may|might|could|would|should|will|shall|proposed|suggested|potential|preliminary|provisional|targets?|aims?|plans?|hypothes\w*|assum\w*)\b|(?<!\w)(?:اذا|لو|حتي|هل|قد|ربما|سوف|يمكن|مقترح\w*|محتمل\w*|مبديي|مبدئي|افتراض\w*|فرضية)(?!\w)", re.I)
_PREPOSITION = re.compile(r"^(?:in|on|at|for|from|to|by|with|of|through|via|about|before|after|and|or)\b", re.I)


def clauses(text):
    from content_safety import _claim_text, _CLAUSE_BOUNDARY
    # The existing ontology/clause rules remain unchanged. Arabic wa-clauses
    # with an explicit new pronoun/negation start their own scope as well.
    normalized = _claim_text(text)
    normalized = re.sub(r"\s+و(?=(?:لدينا|لديهم|نحن|لم|لن|لا)\b)", ";", normalized)
    return [c.strip() for c in _CLAUSE_BOUNDARY.split(normalized) if c.strip()]


def negated_clause(clause):
    """A local denial; never a paragraph-wide 'not'/'if' exemption."""
    from content_safety import _claim_text, _ASSERTIVE_SUBJECT, _ACHIEVED, _possessive_stem
    value = _claim_text(clause)
    if re.search(r"\bnot\s+only\b|ليس\s+فقط", value):
        return False
    negative = _NEGATIVE.search(value)
    if not negative:
        # Epistemic negatives qualify this predicate, not a neighbouring
        # assertion. Require the uncertainty to finish the clause.
        return bool(re.search(r"\b(?:is|are|was|were|remains?)\s+(?:an?\s+)?(?:assumption(?:\s+to\s+(?:test|check|verify))?|unknown|unverified|unproven|unconfirmed)(?:\s+(?:yet|still))?[.!?]?$", value))
    # A new affirmative subject/predicate cannot borrow an earlier denial.
    for subject in _ASSERTIVE_SUBJECT.finditer(value):
        if subject.start() > negative.end() and not _NEGATIVE.search(value[subject.start():subject.end()]):
            return False
    following_aux = list(_AUX.finditer(value, negative.end()))
    leading_negative_subject = bool(re.match(r"^(?:no|none|nobody|not one)\b", value))
    if len(following_aux) > (1 if leading_negative_subject else 0):
        return False
    if leading_negative_subject and following_aux:
        subject = value[negative.end():following_aux[0].start()]
        # 'No advertising needed demand is proven' has a completed negative
        # predicate followed by a NEW affirmative subject, not a negative NP.
        # Relative modifiers ('people you interviewed') remain inside the NP.
        for completed in re.finditer(r"\b([a-z-]+)\s+[a-z]+ed\b", subject):
            if (not completed[1].endswith("ly") and
                    not re.search(r"\b(?:who|whom|that|you|we|they)\b", subject[:completed.end()])):
                return False
    for outcome in _ACHIEVED.finditer(value):
        prefix = value[:outcome.start()]
        if outcome.group().startswith("و") and outcome.start() > negative.end():
            return False
        owner = re.search(r"([\u0621-\u064a]+)\s+$", prefix)
        if owner and _possessive_stem(owner[1]) != owner[1] and owner.start() > negative.end():
            return False
    return True


def ungrounded_assertion(text):
    """Reject achieved/declarative predicates without a source or local modality.

    A noun_phrase/planning verdict is deliberately not an argument. These are
    conservative grammatical checks: uncertainty is omitted rather than being
    certified by a model. No function returns externally_verified evidence.
    """
    from content_safety import _ACHIEVED, _BUSINESS_OBJECT, _participial_description, _directive_guarded, _outcome_guarded, _ASSERTIVE_SUBJECT
    from material_claims import _ACTION, _QUESTION
    for clause in clauses(text):
        if not clause:
            continue
        if negated_clause(clause):
            continue
        if clause.endswith(("?", "؟")) or _QUESTION.search(clause) or _directive_guarded(clause):
            continue
        action = re.match(_ACTION.pattern.translate(str.maketrans("أإآٱى", "ااااي")), clause, re.I)
        if action and not _ASSERTIVE_SUBJECT.search(clause):
            continue
        # Modality must belong to this clause, before the predicate. A marker
        # in a neighbouring clause never authorizes an assertion here.
        modal = _MODAL.search(clause)
        outcomes = [m for m in _ACHIEVED.finditer(clause)
                    if not _participial_description(clause, m) and not _outcome_guarded(clause, m.start())]
        aux = _AUX.search(clause)
        finite = []
        for verb in re.finditer(r"\b[a-z][a-z-]*(?:ed|s)\b", clause):
            before, after = clause[:verb.start()].strip(), clause[verb.end():].strip()
            if not before:
                continue
            if after.startswith("/"):
                continue
            if verb.group() == "aed" and re.search(r"\d\s*$", before):
                continue  # Currency following a figure, not an '-ed' verb.
            # The morphology scan includes the whole hyphenated word, while
            # the existing participle policy checks its verb run ('ordered').
            if verb.group().startswith("pre-") and any(
                    m.start() == verb.start() + 4 and _participial_description(clause, m)
                    for m in _ACHIEVED.finditer(clause)):
                continue
            if not re.search(r"\w", after):
                if verb.group().endswith("ed") and not _participial_description(clause, verb):
                    finite.append(verb)
                continue
            if _PREPOSITION.match(after):
                continue
            if before.endswith("pre-") or (verb.group().endswith("ed") and _participial_description(clause, verb)):
                continue
            following = after.split()[0]
            if re.fullmatch(r"can|may|might|could|would|should|will|shall|is|are|was|were|has|have|had", following):
                continue
            if len(before.split()) > 1 and (following.endswith(("ly", "ing", "ed"))):
                continue
            if len(before.split()) <= 6:
                finite.append(verb)
        predicate = min([m.start() for m in outcomes + finite] + ([aux.start()] if aux else []) + [len(clause)])
        if modal and modal.start() <= predicate:
            continue
        # Existing prospective/research qualifiers, scoped locally. They do
        # not include arbitrary 'not' or a verifier's label.
        if re.search(r"\b(?:needs?|requires?|depends?|limits?|testing|explor\w*|welcome|plausible|untested)\b|تحتاج|يعتمد|تعتمد|تتيح|تسمح|^نختبر\s", clause):
            continue
        # An explicitly uncertain assumption is the object of the predicate,
        # rather than an assertion that its subject achieved a business result.
        if not outcomes and re.search(r"\b(?:an?|the)\s+(?:unverified|untested|proposed)\s+(?:[\w/-]+\s+){0,5}(?:assumption|hypothesis)\b", clause):
            continue
        if outcomes or aux:
            return True
        # Generic English predication: subject + inflected finite verb. Check
        # morphology, not commercial verb names ('holds', 'supplies', etc.).
        if finite:
            return True
        for match in re.finditer(r"\b[a-z]+s\s+(?:of\s+[a-z-]+\s+)?([a-z-]+)\s+(?:all\s+)?[a-z]+s\b", clause):
            if re.search(r"\bor\b", clause[:match.start()]):
                continue
            verb = match[1]
            if not _PREPOSITION.match(verb) and not verb.endswith(("ing", "ed", "ly")):
                return True
        # Subject/predicate relations between material nouns do not become
        # harmless because a new, unlisted verb was used.
        objects = list(_BUSINESS_OBJECT.finditer(clause))
        for first, second in zip(objects, objects[1:]):
            between = clause[first.end():second.start()].strip()
            if between and not _PREPOSITION.match(between) and not re.fullmatch(r"[\s/-]*", between):
                if re.search(r"[a-z]+", between) and len(between.split()) <= 3:
                    return True
        arabic = re.findall(r"[\u0621-\u064a]+", clause)
        if len(arabic) >= 2 and objects:
            # Finite-prefix/past-suffix morphology; plain service/topic noun
            # fragments remain possible, but assertions need explicit scope.
            for index, word in enumerate(arabic[:2]):
                if len(word) >= 4 and not word.startswith("ال"):
                    augmented = (word.startswith(("است", "ان", "ات")) or len(word) == 4 and word.startswith("ا")
                                 or len(word) >= 5 and word.startswith("ا") and word[2] == "ت")
                    present = (word.startswith(("ي", "ت", "ن", "و")) or augmented) and not word.endswith(("ة", "ات", "ية", "ي"))
                    present |= index == 0 and word.startswith(("ي", "ت")) and bool(_BUSINESS_OBJECT.fullmatch(arabic[1]))
                    past = word.endswith(("ت", "وا")) and not word.endswith("ات")
                    if present or past:
                        return True
            # Unqualified nominal participial predicates (e.g. an approved
            # request), independent of any specific approval/outcome wording.
            if objects and re.fullmatch(r"م[\u0621-\u064a]{3,}", arabic[-1]) and not arabic[-1].endswith(("ي", "ية", "ة")):
                return True
    return False
