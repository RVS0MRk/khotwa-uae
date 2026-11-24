"""Small grammatical shape checks, not a claim verifier or a verb dictionary.

An unfamiliar English base-form verb can introduce a determined object. Arabic
command morphology includes short/hollow and defective forms and attached و/ف.
Ambiguous forms still face clause-local material-risk and publication checks.
"""
import re

_EN_SUBJECT = re.compile(r"^(?:i|we|you|he|she|it|they|this|that|these|those|the|a|an|our|my|your|their|its|there)\b", re.I)
_EN_OBJECT = re.compile(r"^(?:a|an|the|your|one|two|three|four|five|six|seven|eight|nine|ten|\d+|some|each|several|whether|how|for|with|about|into|against)\b", re.I)
_AR = r"[\u0621-\u064a]"


def command_shape(value):
    """Recognise bounded imperative constructions without a business word list.

    This is intentionally not a blanket 'any first word is a verb' rule. It
    excludes overt subjects, English inflected verbs and Arabic past-person
    suffixes; callers must also reject embedded unqualified assertions.
    """
    value = re.sub(r"^(?:then\s+|ثم\s+)", "", value.strip(), flags=re.I)
    pair = value.split(None, 1)
    if len(pair) != 2:
        return False
    first, rest = pair
    if re.fullmatch(r"[a-z][a-z-]+", first, re.I):
        if _EN_SUBJECT.match(value) or first.endswith(("s", "ed", "ing")):
            return False
        # Consonant stems and productive -ate/-ise/-ize forms can take an
        # object. Past irregulars are checked by the calling form validator.
        return bool(_EN_OBJECT.match(rest))
    if not re.fullmatch(_AR + r"{2,7}", first):
        return False
    # An attached conjunction is not part of the command root. Keep the
    # surface form too: the و in وعد is a root, not invariably a conjunction.
    candidates = [first]
    if first[0] in "وف" and len(first) > 2:
        candidates.append(first[1:])
    for token in candidates:
        if token in {"تم", "قد", "لم", "لن", "لا", "من", "في", "ما", "هو", "هي", "هم"}:
            continue
        form_three = len(token) == 4 and token[1] == "ا"
        # Reflexive Form V is orthographically ambiguous with the perfect.
        # An immediate time adjunct + prepositional complement establishes a
        # bounded instruction ('speak today to ...'), not a VSO achievement.
        if re.fullmatch(r'ت[\u0621-\u064a]{3,4}', token) and re.match(r'^(?:اليوم|الان)\s+(?:الي|مع|عن|في|ب)\b', rest):
            return True
        if (token.startswith(("ال", "ن", "ي", "ت")) and not form_three) or token.endswith(("نا", "وا", "ات", "ت", "ون", "ين", "ة")):
            continue
        # A construct-state nominal subject followed by its definite genitive
        # ('week of the opening ...') cannot establish an ambiguous command.
        objects = rest.split()
        # A definite subject followed by a second, indefinite object is VSO,
        # not a command plus its noun phrase. Case is frequently unmarked in
        # Arabic: a geminate perfect must not become an imperative exception.
        if (len(objects) > 1 and objects[0].startswith('ال') and objects[0] not in {'الي','الان','اليوم'} and
                not objects[1].startswith(('ال','وال','فال','ب','ل','ك')) and
                not re.match(r'^(?:علي|الي|عن|مع|من|في|قبل|بعد|دون)$',objects[1]) and
                not objects[1].endswith('ا')):
            continue
        if len(token) > 3 and len(objects) > 1 and objects[1].startswith("ال") and not objects[0].startswith(("ال", "ب", "ل")) and not objects[0].endswith("ا"):
            continue
        # Short jussive stems (زر، قل، خذ، بع، سر، عد، قس، رد) need an
        # explicit object/adjunct; this rule is morphological, not their list.
        if len(token) == 2 and re.match(r"^(?:ال|ب|ل|علي|عن|الي|دون|فقط|ثلاث|اربع|خمس|اثن|رأي|راي)", rest):
            return True
        # Prothetic alif: triliteral/augmented/defective command. A completed
        # past-person suffix above cannot borrow this exception.
        if token.startswith("ا") and len(token) in range(3, 7) and "ا" not in token[1:] and not token.endswith(("ا", "ي")):
            return True
        # Form II (geminate spelling) and Form III with direct object.
        if ((len(token) == 3 and token[1] == token[2]) or
                (len(token) == 4 and token[1] == "ا")) and re.match(r"^(?:ال|ب|ل|مع|عن)", rest):
            return True
    return False


def name_shape(text, normalized, predicates):
    """Conservative, bounded short-label grammar, including proper-name pairs.

    A provider's noun label cannot admit sentence-shaped names. This does not
    authenticate a name or close every semantic noun-phrase failure mode.
    """
    value = normalized.strip(" .")
    tokens = value.split()
    if not tokens or len(tokens) > 12 or re.search(r"[!?؟;؛:،,\n{}\[\]]", text.strip().rstrip(':')):
        return False
    if re.search(r"\b(?:we|our|you|your|they|their|i|my|will|shall|never|already)\b|"
                 r"(?<!\w)(?:نحن|لدينا|عندنا|نضمن|سوف|بالفعل|دائما)(?!\w)", value):
        return False
    # True proper-name pairs are not finite English -s/-ed verbs. Preserve
    # James Woods and Maya Reed; 'Cedar attracts buyers' is not that shape.
    raw_tokens = text.strip(" .").split()
    proper_pair = len(raw_tokens) == 2 and all(re.fullmatch(r"[A-Z][a-z]+", w) for w in raw_tokens)
    if proper_pair:
        return not re.search(r"\b(?:Is|Are|Has|Have|Was|Were|Had|Won|Sold|Paid|Guaranteed|Profitable)\b", text)
    # Arabic personal names commonly start with ن/ي/ت and include particles;
    # do not mistake that alone for a verb. An initial definite/article noun,
    # possessive nominal sentence, or VSO perfect before a definite subject is
    # handled by the caller/remaining strict predicates.
    arabic_pair = len(tokens) <= 2 and all(re.fullmatch(_AR + "+", w) for w in tokens)
    if arabic_pair and not re.search(r"(?<!\w)(?:ال)?(?:مربح|ممتلئ|مضمون|ناجح|مثبت|مؤكد)(?!\w)", value):
        return not re.search(r"^\S+(?:ت|نا|وا)\s+ال|^(?:لدي|عند)", value)
    if tokens[0].isascii():
        for position in list(predicates):
            tail = value[position:].strip(' .:')
            match = re.match(r'([a-z-]+)(.*)',tail,re.I)
            if not match:
                continue
            token, following = match[1], match[2].strip()
            # A final plural in a multiword noun label is not an independent
            # verb; an earlier finite 'attracts/has/earned' still rejects it.
            nominal_modifier = tokens[0].endswith(('er','or','ment','ion','ity','ness','al','ive'))
            final_plural = (len(tokens) >= 3 or len(tokens)==2 and nominal_modifier) and not following and token.endswith('s')
            agent_plural = (len(token) >= 7 and token.endswith(('ers','ors','als','ants','ents','ists')) and
                            re.match(r'^(?:in|of|for|near|at|with|without|about|under|over|between)\b', following))
            noun_coordination = token.endswith('s') and following.startswith(('/', '&'))
            if final_plural or agent_plural or noun_coordination:
                predicates.remove(position)
    if len(tokens) == 2 and tokens[0].isascii() and tokens[0].endswith(("al", "ive", "ary", "ous")) and tokens[1].endswith("s"):
        predicates = [p for p in predicates if value[p:].strip(" .") != tokens[1]]
    return not predicates
