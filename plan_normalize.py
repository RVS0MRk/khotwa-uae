"""Model structure, sentence validation and bilingual plan recovery."""

import re
from html import unescape
from copy import deepcopy
from scoring import normalize_scores
from content_safety import safe_text, MISSING
from plan_utils import _int, _money, _sync_path_costs, _format_money, _target_customer


def _segment_names(idea, target, category, lang, personas=None):
    """Keep specific model segments; fill missing ones from the business context."""
    ar = lang == "ar"
    generic = {
        "people with the problem",
        "small business buyers",
        "potential repeat users",
        "مستخدمون لديهم المشكلة",
        "مشترون من الشركات الصغيرة",
        "عملاء محتملون متكررون",
    }
    names = []
    for person in personas or []:
        name = person.get("name", "") if isinstance(person, dict) else ""
        if (
            isinstance(name, str)
            and name.strip()
            and name.lower().strip() not in generic
            and name not in names
            and _language_matches(name, lang)
        ):
            names.append(name.strip())
    # A model-inferred target must not override the founder's business/category.
    context = f"{idea} {category}"
    groups = [
        (
            r"car.?wash|غسيل سيارات",
            ["Residential car owners", "Office and facility managers", "Fleet operators"],
            ["مالكو السيارات السكنية", "مديرو المكاتب والمرافق", "مشغلو الأساطيل"],
        ),
        (
            r"car|vehicle|driv|commut|ergonom|سيار|مركب|قياد",
            ["Daily commuters", "Ride-hailing drivers", "Fleet / company vehicle managers"],
            ["المتنقلون يومياً", "سائقو خدمات نقل الركاب", "مديرو الأساطيل وسيارات الشركات"],
        ),
        (
            r"food|cater|meal|طعام|وجبات",
            ["Busy households", "Office lunch buyers", "Small event organisers"],
            ["الأسر المشغولة", "مشترو وجبات المكاتب", "منظمو الفعاليات الصغيرة"],
        ),
        (
            r"tutor|educat|learn|تعليم|دروس",
            ["Students needing subject support", "Parents choosing learning support", "Adults learning new skills"],
            ["طلاب يحتاجون دعماً دراسياً", "أولياء أمور يبحثون عن دعم تعليمي", "بالغون يتعلمون مهارات جديدة"],
        ),
        (
            r"digital|software|technolog|تقني|رقمي",
            ["Independent professionals", "Small business operators", "Teams managing recurring workflows"],
            ["المهنيون المستقلون", "مشغلو الشركات الصغيرة", "فرق تدير أعمالاً متكررة"],
        ),
        (
            r"touris|hospitality|travel|سياح|سفر",
            ["First-time visitors", "Families planning short trips", "Local accommodation operators"],
            ["زوار للمرة الأولى", "عائلات تخطط لرحلات قصيرة", "مشغلو أماكن الإقامة المحلية"],
        ),
    ]
    fallback = None
    for pattern, en, arabic in groups:
        if re.search(pattern, context, re.I):
            fallback = arabic if ar else en
            break
    if fallback is None:
        subject = target.strip() if target and target.lower().strip() not in generic else idea.strip()
        subject = subject or category or ("الفكرة المقترحة" if ar else "the proposed service")
        fallback = (
            [f"أفراد يبحثون عن {subject}", f"أصحاب أعمال يحتاجون إلى {subject}", f"جهات تشتري {subject} لفرقها"]
            if ar
            else [
                f"Individuals seeking {subject}",
                f"Business owners needing {subject}",
                f"Teams purchasing {subject} together",
            ]
        )
    for name in fallback:
        if name not in names:
            names.append(name)
    return names[:3]


def _execution_risk(idea, category, lang):
    context = f"{idea} {category}"
    if re.search(r"social.?media|content|marketing|محتوى|تواصل اجتماعي|تسويق", context, re.I):
        en = (
            "Content-production capacity, client approval delays and delivery consistency need testing.",
            "Test a sample content calendar and approval workflow with prospective clients.",
        )
        ar = (
            "تحتاج قدرة إنتاج المحتوى وتأخر موافقات العملاء واتساق التسليم إلى اختبار.",
            "اختبر نموذج جدول محتوى ومسار الموافقات مع عملاء محتملين.",
        )
    elif re.search(r"food|cater|meal|restaurant|طعام|وجبة|وجبات|مطعم", context, re.I):
        en = (
            "Meal preparation capacity, timing and consistent delivery need testing.",
            "Map a sample order and preparation schedule without preparing or selling food.",
        )
        ar = (
            "تحتاج قدرة إعداد الوجبات وتوقيتها واتساق التسليم إلى اختبار.",
            "ضع جدولاً افتراضياً للطلبات والإعداد دون تجهيز الطعام أو بيعه.",
        )
    elif re.search(
        r"app\b|software|digital|platform|tool|website|no.?code|AI.?powered|رقمي|تطبيق|برمج|منصة|موقع|ذكاء اصطناعي",
        context,
        re.I,
    ):
        en = (
            "Development effort, data handling, AI output reliability and customer support need testing.",
            "Test a prototype walkthrough, privacy approach and support workflow with prospective users.",
        )
        ar = (
            "تحتاج جهود التطوير والتعامل مع البيانات وموثوقية مخرجات الذكاء الاصطناعي ودعم العملاء إلى اختبار.",
            "اختبر شرحاً لنموذج أولي ونهج الخصوصية ومسار الدعم مع مستخدمين محتملين.",
        )
    elif re.search(r"mobile|car.?wash|delivery|clean|متنقل|غسيل|توصيل|تنظيف", context, re.I):
        en = (
            "Travel time, scheduling and service logistics need testing.",
            "Test a mock route and appointment schedule without operating.",
        )
        ar = (
            "تحتاج أوقات التنقل والمواعيد ولوجستيات الخدمة إلى اختبار.",
            "اختبر مساراً وجدول مواعيد افتراضيين دون تشغيل.",
        )
    else:
        en = (
            f"Delivery capacity and quality consistency for {idea} need testing.",
            "Map one sample delivery workflow and identify bottlenecks before operating.",
        )
        ar = (
            f"تحتاج القدرة على تقديم {idea} واتساق الجودة إلى اختبار.",
            "حدد نموذجاً لمسار تقديم العرض ونقاط التعطل قبل التشغيل.",
        )
    return ar if lang == "ar" else en


def _persona_hypothesis(idea, category, index, lang):
    """Distinct, unverified segment hypotheses when model details are absent or generic."""
    context = f"{idea} {category}"
    if re.search(r"food|cater|meal|restaurant|طعام|وجبة|وجبات|مطعم", context, re.I):
        en = [
            (
                "Convenient meals at a predictable time",
                "Home cooking or takeaway",
                "Household and neighbourhood groups",
                "On a busy day, what meal option do you choose and why?",
            ),
            (
                "Reliable group lunch ordering",
                "Individual orders or office canteens",
                "Office administrators and workplace groups",
                "How does your team arrange lunch now, and what goes wrong?",
            ),
            (
                "Flexible portions and timing for a small event",
                "Self-catering or an existing caterer",
                "Event planners and community organisers",
                "What is hardest about arranging food for a small event?",
            ),
        ]
        ar = [
            (
                "وجبات مريحة في وقت متوقع",
                "الطهي المنزلي أو الطلبات الجاهزة",
                "مجموعات الأسر والأحياء",
                "في يوم مزدحم، كيف تختار وجبتك ولماذا؟",
            ),
            (
                "طلب غداء جماعي موثوق",
                "طلبات فردية أو مقصف العمل",
                "منسقو المكاتب ومجموعات العمل",
                "كيف يرتب فريقك الغداء الآن، وما الصعوبة المتكررة؟",
            ),
            (
                "كميات ومواعيد مرنة لفعالية صغيرة",
                "التحضير الذاتي أو شركة تموين قائمة",
                "منظمو الفعاليات والمجتمعات",
                "ما أصعب جزء في ترتيب الطعام لفعالية صغيرة؟",
            ),
        ]
    elif re.search(
        r"website|software|digital|online|platform|app\b|no.?code|tech|موقع|تقني|رقمي|برمج|منصة|تطبيق", context, re.I
    ):
        en = [
            (
                "A practical online presence they can update",
                "Social media pages or do-it-yourself site builders",
                "Local business groups and owner interviews",
                "How do you currently update your online presence, and what slows you down?",
            ),
            (
                "Faster handling of customer enquiries",
                "Manual messages or an outside agency",
                "Sector networks and manager interviews",
                "Where do online customer enquiries get lost or delayed today?",
            ),
            (
                "Reliable digital workflows and support",
                "Spreadsheets or disconnected tools",
                "Professional networks and workflow interviews",
                "Which recurring task would you most want to simplify, and what do you use now?",
            ),
        ]
        ar = [
            (
                "حضور رقمي عملي يسهل تحديثه",
                "صفحات التواصل أو أدوات إنشاء المواقع ذاتياً",
                "مجموعات الأعمال المحلية ومقابلات المالكين",
                "كيف تحدّث حضورك الرقمي الآن، وما الذي يبطئك؟",
            ),
            (
                "معالجة أسرع لاستفسارات العملاء",
                "الرسائل اليدوية أو وكالة خارجية",
                "شبكات القطاع ومقابلات المديرين",
                "أين تتأخر استفسارات العملاء الرقمية أو تضيع اليوم؟",
            ),
            (
                "مسارات عمل رقمية موثوقة ودعم مناسب",
                "الجداول أو الأدوات المنفصلة",
                "شبكات المهنيين ومقابلات سير العمل",
                "أي مهمة متكررة تريد تبسيطها، وما أداتك الحالية؟",
            ),
        ]
    elif re.search(r"service|wash|clean|repair|maintenance|delivery|خدمة|غسيل|تنظيف|صيانة|توصيل", context, re.I):
        en = [
            (
                "A service appointment that fits their schedule",
                "Doing the task themselves or visiting a provider",
                "Neighbourhood groups and direct interviews",
                "When did scheduling this service last cause difficulty?",
            ),
            (
                "Predictable service quality for a workplace",
                "An existing contractor or ad hoc staff",
                "Facility and operations manager interviews",
                "How do you assess a service provider's reliability now?",
            ),
            (
                "Coordinated service across several locations",
                "Separate bookings with current providers",
                "Fleet or multi-site operator interviews",
                "What is the main coordination problem across locations?",
            ),
        ]
        ar = [
            (
                "موعد خدمة يناسب جدولهم",
                "تنفيذ المهمة ذاتياً أو زيارة مزود قائم",
                "مجموعات الأحياء ومقابلات مباشرة",
                "متى سببت لك مواعيد هذه الخدمة صعوبة آخر مرة؟",
            ),
            (
                "جودة خدمة متوقعة في موقع العمل",
                "متعهد قائم أو موظفون حسب الحاجة",
                "مقابلات مديري المرافق والعمليات",
                "كيف تقيّم موثوقية مزود الخدمة حالياً؟",
            ),
            (
                "تنسيق الخدمة بين مواقع متعددة",
                "حجوزات منفصلة لدى مزودين قائمين",
                "مقابلات مشغلي الأساطيل أو المواقع المتعددة",
                "ما أكبر مشكلة تنسيق بين المواقع؟",
            ),
        ]
    else:
        en = [
            (
                "A clearer way to solve the proposed problem",
                "Their current product or self-service approach",
                "Direct interviews in the selected segment",
                "What did you try most recently to solve this problem?",
            ),
            (
                "A practical option that fits their budget",
                "An existing supplier or doing without",
                "Relevant community and professional groups",
                "What would make switching from your current option worthwhile?",
            ),
            (
                "A dependable repeatable experience",
                "Informal referrals or another provider",
                "Interviews with repeat users or buyers",
                "What would make you return to the same provider?",
            ),
        ]
        ar = [
            (
                "طريقة أوضح لحل المشكلة المقترحة",
                "المنتج الحالي أو الحل الذاتي",
                "مقابلات مباشرة مع الشريحة المختارة",
                "ما آخر طريقة جربتها لحل هذه المشكلة؟",
            ),
            (
                "خيار عملي يناسب الميزانية",
                "مورد قائم أو الاستغناء عن الحل",
                "مجموعات المجتمع والمهنيين المناسبة",
                "ما الذي يجعل تغيير خيارك الحالي مجدياً؟",
            ),
            (
                "تجربة موثوقة قابلة للتكرار",
                "إحالات غير رسمية أو مزود آخر",
                "مقابلات مع مستخدمين أو مشترين متكررين",
                "ما الذي يدفعك للعودة إلى المزود نفسه؟",
            ),
        ]
    return (ar if lang == "ar" else en)[index % 3]


def _normalize_scores(raw, idea, lang):
    return normalize_scores(raw, idea, lang)


def _template_plan(plan, inputs, lang):
    """One authoritative user profile with separately labelled AI estimates."""
    if not isinstance(plan, dict):
        raise ValueError("Invalid plan")
    # Evidence is never accepted from the model, even as unsolicited fields.
    for key in ("proof_summary", "proof_rows", "customer_evidence", "evidence"):
        plan.pop(key, None)
    report = plan.get("readiness_report") or {}
    score = _normalize_scores(plan.get("opportunity_score"), str(inputs.get("idea") or ""), lang)
    plan["opportunity_score"] = score
    idea = str(inputs.get("idea") or "").strip()
    category = str(inputs.get("category") or "").strip()
    budget = max(0, _int(inputs.get("budget")))
    plan["state"] = {
        "idea": idea,
        "category": category,
        "idea_source": (
            "ai_suggestion_selected" if inputs.get("idea_source") == "ai_suggestion_selected" else "user_input"
        ),
        "target_customer": str(report.get("target_customer") or ""),
        "region": str(inputs.get("region") or "UAE-wide"),
        "context": str(inputs.get("context") or "Not sure"),
        "customer_type": str(inputs.get("user_type") or ""),
        "user_budget_aed": budget,
        "suggested_test_price_aed": max(0, _int(plan.get("suggested_test_price_aed"))),
        "estimated_test_cost_aed": max(0, _int(report.get("estimated_first_test_cost_aed"))),
        "opportunity_score": score,
        "decision": str((plan.get("decision_engine") or {}).get("decision") or ""),
        "first_action": str(plan.get("first_step_today") or ""),
        "evidence": {"status": "not_validated", "responses": 0},
    }
    plan["_region"] = plan["state"]["region"]
    plan["_context"] = plan["state"]["context"]
    plan["_category"] = category
    plan["_budget"] = budget
    plan["_user_type"] = plan["state"]["customer_type"]
    report["idea"] = idea
    plan["readiness_report"] = report
    plan["do_not_start_with"] = (
        ["تجنب الإنفاق الكبير قبل اختبار الطلب؛ تحقق من الموافقات المطلوبة قبل البيع أو التشغيل التجاري."]
        if lang == "ar"
        else [
            "Avoid major irreversible costs before demand evidence; verify required approvals before payment or commercial operation."
        ]
    ) + [x for x in (plan.get("do_not_start_with") or []) if not re.search(r"licen|permit|ترخيص|رخصة", str(x), re.I)][
        :4
    ]
    plan["instead_do"] = (
        ["مقابلات العملاء، وقائمة انتظار أو حجز بلا دفع."]
        if lang == "ar"
        else ["Interview customers and collect no-payment reservations or waitlist signups."]
    ) + [
        x
        for x in (plan.get("instead_do") or [])
        if not re.search(r"pre.?order|deposit|paid|payment|طلب مسبق|عربون|دفع", str(x), re.I)
    ][
        :3
    ]
    # The model cannot provide customer evidence. It exists only in Proof Mode.
    overview = plan.get("idea_overview") or {}
    overview["evidence"] = (
        "لم تُجمع أدلة من العملاء بعد. هذه فرضية للاختبار."
        if lang == "ar"
        else "No customer evidence collected yet. This is a hypothesis to test."
    )
    overview["impact"] = (
        "منفعة محتملة للاختبار؛ اسأل العملاء عما إذا كان العرض قد يساعدهم."
        if lang == "ar"
        else "Potential benefit to test: ask customers whether the offer could help them."
    )
    plan["idea_overview"] = overview
    # Treat every generated claim as a hypothesis. Discard unsupported evidence
    # and categorical legal statements, wherever the model placed them.
    evidence_claim = re.compile(
        r"\b(survey(?:ed|s)?|interviews? suggest|research shows|customers? (?:said|reported|prefer|are interested)|\d+(?:\.\d+)?\s*%|conversion rate|pre.?orders? received|strong demand|demand appears|proven|validated|promising|shows promise|strong (?:idea|opportunity)|weak (?:idea|opportunity)|viable|high.potential)\b|استطلاع|أظهرت المقابلات|طلب قوي|واعد|مثبت|٪|%",
        re.I,
    )
    legal_claim = re.compile(
        r"\b(?:licen[cs]\w*|permits?|fines?|tax(?:es)?|VAT|registration|insurance|fees?|approvals?|government|municipal|municipality|ministry|department|authority)\b|water[ -]?use|waste[ -]?disposal|ترخيص|تراخيص|رخص|تصريح|تصاريح|غرام|ضريب|تأمين|موافق|وزارة|بلدية|استخدام المياه|التخلص من النفايات",
        re.I,
    )
    unsafe_test = re.compile(
        r"\b(?:free|micro|paid|operational|real|small)\s+(?:wash(?:es)?|pilot|service)|\b(?:run|start|schedule|perform|provide|deliver|launch)\b.{0,35}\b(?:wash(?:es)?|pilot|service|operation)|deposit|pre.?orders?|accept payments?|charge customers?|buy.{0,35}(?:equipment|inventory)|purchase.{0,35}(?:equipment|inventory)|تجربة مدفوعة|غسيل مجاني|تشغيل تجاري|عربون|دفعة مقدمة|طلبات مسبقة|شراء.{0,35}(?:معدات|مخزون)",
        re.I,
    )
    cost_claim = re.compile(
        r"\b(?:AED\s*\d|\d[\d,]*\s*AED|under\s+AED|(?:equipment|setup|rental|pilot).{0,35}\bcosts?\b|supplier.{0,35}\bquotes?\b)\b|درهم\s*\d|\d[\d,]*\s*درهم",
        re.I,
    )

    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, str):
            for _ in range(10):
                decoded = unescape(value)
                if decoded == value:
                    break
                value = decoded
            value = re.sub(r"<br\s*/?>|</(?:p|div|li)>", " ", value, flags=re.I)
            value = re.sub(r"<[^>]*>", "", value)
            value = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", value)
            value = re.sub(r"\\([\\`*_{}\[\]()#+.!>|~-])", r"\1", value)
            value = re.sub(r"[`*_#~|]|&(?:#[xX]?[0-9a-fA-F]+|[A-Za-z]+);", "", value)
            value = " ".join(value.split())
            if value.startswith(("{", "[")) or re.search(r'"[^"\n]+"\s*:', value):
                return "افتراض للتخطيط يحتاج إلى اختبار." if lang == "ar" else "Planning assumption to test."
            if legal_claim.search(value):
                return (
                    "المتطلبات التنظيمية غير مؤكدة. تحقق من تصنيف النشاط وأي موافقات مطلوبة لدى الجهة الرسمية المختصة قبل التشغيل."
                    if lang == "ar"
                    else "Regulatory requirements have not been verified. Check the official activity classification and any required approvals with the relevant UAE authority before operating."
                )
            if unsafe_test.search(value):
                return (
                    "ابدأ بمقابلات العملاء وقائمة انتظار بلا دفع. بعد تأكيد التراخيص والموافقات المطلوبة، نفّذ أصغر تجربة عملية مناسبة."
                    if lang == "ar"
                    else "Start with interviews and a no-payment waitlist. After confirming that required licences and approvals are in place, run the smallest practical pilot."
                )
            if evidence_claim.search(value):
                return (
                    "لم تُجمع أدلة من العملاء بعد. هذه فرضية للاختبار."
                    if lang == "ar"
                    else "No customer evidence collected yet. This is an assumption to test."
                )
            if cost_claim.search(value):
                return (
                    "تقدير تقريبي بالذكاء الاصطناعي — تحقق من عروض الأسعار المحلية."
                    if lang == "ar"
                    else "Rough AI estimate — verify with local supplier quotes."
                )
        return value

    for key in list(plan):
        if key not in ("state", "_region", "_context", "_category", "_budget", "_user_type"):
            plan[key] = clean(plan[key])
    # Source identifiers are metadata, not prose for the Markdown cleaner.
    plan["opportunity_score"]["source"] = score["source"]
    for key in ("local_fit", "clear_customer", "low_starting_cost", "easy_first_step", "growth_potential"):
        plan["opportunity_score"][key]["source"] = score[key]["source"]
    plan["small_test_plan"] = (
        {
            "intro": "اختبر الطلب من دون تشغيل أو دفع قبل التحقق الرسمي.",
            "points": [
                "حدد شريحة عميل واحدة",
                "قابل خمسة عملاء محتملين عن المشكلة والبدائل الحالية",
                "اختبر العرض برسالة واتساب أو صفحة بسيطة",
                "اجمع نوايا شراء أو حجوزات بلا دفع",
                "راجع النتائج قبل الإنفاق",
            ],
        }
        if lang == "ar"
        else {
            "intro": "Test demand without operating or taking payment before official checks.",
            "points": [
                "Choose one customer segment",
                "Interview five potential customers about the problem and current alternatives",
                "Test the offer with a WhatsApp message or landing page",
                "Collect stated purchase intent or no-payment waitlist signups",
                "Review the results before spending",
            ],
        }
    )
    day_rows = (
        [
            (
                "حدد العميل المستهدف",
                "اكتب فرضية عن شريحة واحدة ومشكلتها",
                "بطاقة فرضية لشريحة واحدة",
                "تتضمن البطاقة المشكلة والبديل الحالي وسؤالاً للاختبار",
                "1–2 ساعة · تقدير",
            ),
            (
                "رتب مقابلات العملاء",
                "ادعُ خمسة أشخاص من الشريحة واسأل من يوافق عن بدائله الحالية",
                "سجل دعوات وأي ملاحظات من مقابلات تمت",
                "لا تُحسب مقابلة إلا إذا حدثت فعلاً؛ يمكن استكمالها لاحقاً",
                "2–4 ساعات · تقدير",
            ),
            (
                "اختبر العرض",
                "جهز رسالة أو صفحة بسيطة واطلب رأياً بلا بيع",
                "نسخة واحدة من رسالة العرض",
                "سجل ردوداً فعلية إن وصلت، وإلا دوّن غياب الردود",
                "1–3 ساعات · تقدير",
            ),
            (
                "اجمع نوايا بلا دفع",
                "اعرض قائمة انتظار أو حجزاً بلا دفع على المهتمين",
                "سجل نوايا أو حجوزات بلا دفع",
                "ميّز الاهتمام عن النية والحجز ولا تفترض تحقق الطلب",
                "مدة متغيرة",
            ),
            (
                "راجع الأدلة",
                "قارن الردود والاعتراضات ومخاوف السعر",
                "ملخص للأدلة والفجوات",
                "اذكر ما سُجل فعلاً وما لم يُعرف بعد",
                "1–2 ساعة · تقدير",
            ),
            (
                "تحقق من المتطلبات",
                "راجع تصنيف النشاط والموافقات المحتملة لدى الجهة الرسمية قبل أي تشغيل",
                "قائمة متطلبات وأسئلة للتحقق الرسمي",
                "لا تبدأ تجربة تشغيلية قبل تأكيد المتطلبات اللازمة",
                "مدة متغيرة",
            ),
            (
                "اتخذ القرار",
                "قرر الاستمرار أو التعديل أو التوقف وفق الأدلة المتاحة",
                "مذكرة قرار للخطوة التالية",
                "يرتبط القرار بالأدلة المسجلة والفجوات الباقية",
                "1 ساعة · تقدير",
            ),
        ]
        if lang == "ar"
        else [
            (
                "Define target customer",
                "Write a hypothesis about one segment and its problem",
                "One segment hypothesis card",
                "The card states the problem, current alternative and a test question",
                "1–2h · estimate",
            ),
            (
                "Arrange customer interviews",
                "Invite five people in the segment and ask those who agree about current alternatives",
                "Outreach log and notes from any completed interviews",
                "Count a conversation only if it actually happened; continue later if needed",
                "2–4h · estimate",
            ),
            (
                "Test the offer",
                "Prepare one message or simple page and ask for feedback without selling",
                "One draft offer message",
                "Record actual responses if received; otherwise note the lack of replies",
                "1–3h · estimate",
            ),
            (
                "Collect no-payment intent",
                "Offer a no-payment waitlist or reservation to interested people",
                "Intent or no-payment reservation log",
                "Separate interest, intent and reservation; do not assume demand is proven",
                "Time varies",
            ),
            (
                "Review evidence",
                "Compare responses, objections and price concerns",
                "Evidence and gaps summary",
                "State what is actually recorded and what remains unknown",
                "1–2h · estimate",
            ),
            (
                "Verify requirements",
                "Check activity classification and possible approvals with the official authority before operating",
                "Official-check questions and requirements list",
                "Do not start an operational test before confirming what is required",
                "Time varies",
            ),
            (
                "Decide",
                "Choose continue, adjust or stop based on available evidence",
                "Next-step decision memo",
                "Tie the decision to recorded evidence and remaining gaps",
                "1h · estimate",
            ),
        ]
    )
    plan["seven_day_plan"] = [
        {
            "day": i + 1,
            "focus": focus,
            "action": action,
            "output": output,
            "time_needed": time_needed,
            "success_check": success,
        }
        for i, (focus, action, output, success, time_needed) in enumerate(day_rows)
    ]
    plan["decision_engine"] = {
        "decision": "تحقق أكثر" if lang == "ar" else "Validate more",
        "reason": (
            "قرار قبل جمع الأدلة: تحقق من الطلب والمتطلبات الرسمية أولاً."
            if lang == "ar"
            else "Pre-evidence decision: customer demand and official requirements still need verification."
        ),
        "next_test_action": (
            "قابل خمسة عملاء محتملين واجمع نوايا بلا دفع."
            if lang == "ar"
            else "Interview five potential customers and collect no-payment intent."
        ),
        "risk_level": "Medium",
        "recommended_test_budget_aed": "",
    }
    plan["readiness_report"]["idea"] = idea
    names = _segment_names(
        idea, str(plan["readiness_report"].get("target_customer") or ""), category, lang, plan.get("customer_personas")
    )
    model_personas = plan.get("customer_personas") or []

    def specific_detail(value):
        return (
            isinstance(value, str)
            and len(value.strip()) >= 18
            and not re.search(
                r"solving (?:their|the) current problem|direct outreach and interviews|how do you solve (?:this|the) problem|حل المشكلة الحالية|تواصل مباشر ومقابلات|كيف تحل المشكلة الآن|no customer evidence|planning assumption",
                value,
                re.I,
            )
        )

    personas = []
    for index, name in enumerate(names):
        need, alternative, channel, question = _persona_hypothesis(idea, category, index, lang)
        source = (
            model_personas[index] if index < len(model_personas) and isinstance(model_personas[index], dict) else {}
        )
        cares = (
            source.get("cares_about")
            if specific_detail(source.get("cares_about")) and _language_matches(source.get("cares_about"), lang, idea)
            else need
        )
        reach = (
            source.get("reach_through")
            if specific_detail(source.get("reach_through"))
            and _language_matches(source.get("reach_through"), lang, idea)
            else channel
        )
        ask = (
            source.get("ask")
            if specific_detail(source.get("ask")) and _language_matches(source.get("ask"), lang, idea)
            else question
        )
        personas.append(
            {
                "name": name,
                "cares_about": cares,
                "potential_need": need,
                "why_benefit": (
                    f"قد تكون بديلاً عن {alternative} إذا كانت {need} مهمة لهم؛ هذا افتراض للاختبار."
                    if lang == "ar"
                    else f"May replace {alternative} if {need.lower()} matters to this segment; test this assumption."
                ),
                "current_alternative": alternative,
                "reach_through": reach,
                "ask": ask,
                "source": "ai_assumption",
            }
        )
    plan["customer_personas"] = personas
    risk_names = (
        ["طلب العملاء", "التكلفة / المال", "الثقة / التبني", "التنفيذ", "الأنظمة / الامتثال"]
        if lang == "ar"
        else ["Customer Demand", "Cost / Financial", "Trust / Adoption", "Execution", "Regulation / Compliance"]
    )
    risk_reasons = (
        [
            "لا توجد أدلة عملاء مسجّلة في وضع الإثبات.",
            "التكاليف المقدرة غير مؤكدة.",
            "يجب اختبار مخاوف الثقة المحتملة.",
            "تحتاج قدرة التنفيذ إلى اختبار.",
            "المتطلبات الدقيقة غير مؤكدة وتعتمد على النشاط والإمارة.",
        ]
        if lang == "ar"
        else [
            "No customer evidence is recorded in Proof Mode.",
            "Estimated costs are unverified.",
            "Potential trust concerns should be tested.",
            "Execution capacity needs testing.",
            "Exact requirements are unverified and depend on the activity and emirate.",
        ]
    )
    risk_fixes = (
        [
            "أجر مقابلات وسجّل نوايا بلا دفع.",
            "تحقق من عروض الأسعار المحلية قبل الإنفاق.",
            "اسأل العملاء عن أسباب التردد.",
            "اختبر جدولاً افتراضياً بلا تشغيل فعلي.",
            "تحقق من تصنيف النشاط والموافقات المطلوبة لدى الجهة الرسمية المختصة.",
        ]
        if lang == "ar"
        else [
            "Interview customers and record no-payment intent.",
            "Verify local supplier quotes before spending.",
            "Ask customers about reasons for hesitation.",
            "Test a mock schedule without operating.",
            "Verify the activity classification and required approvals with the relevant official authority.",
        ]
    )
    risk_reasons[3], risk_fixes[3] = _execution_risk(idea, category, lang)
    risk_reasons[0] = (
        f"حاجة الشريحة المقترحة إلى {idea} لم تُتحقق بعد."
        if lang == "ar"
        else f"The proposed segment's need for {idea} is unverified."
    )
    risk_reasons[1] = (
        f"وقت وتكلفة تقديم {idea} ما زالا تقديرين."
        if lang == "ar"
        else f"Time and delivery costs for {idea} are still estimates."
    )
    risk_reasons[2] = (
        f"أسباب ثقة العملاء بعرض {idea} أو ترددهم تحتاج إلى اختبار."
        if lang == "ar"
        else f"Reasons to trust or hesitate about {idea} need testing."
    )
    if re.search(
        r"website|software|digital|AI.?powered|no.?code|موقع|تقني|رقمي|ذكاء اصطناعي", f"{idea} {category}", re.I
    ):
        risk_reasons[2] = (
            "تحتاج ثقة العملاء في حماية بياناتهم ودقة المخرجات الرقمية إلى اختبار."
            if lang == "ar"
            else "Customer trust in data handling and digital output quality needs testing."
        )
        risk_fixes[2] = (
            "اعرض نموذجاً أولياً واسأل عن الخصوصية والدقة والدعم."
            if lang == "ar"
            else "Show a prototype and ask about privacy, accuracy and support."
        )
    risk_levels = [
        "Unknown",
        "Unknown",
        "Medium" if re.search(r"health|food|AI|data|صحة|طعام|ذكاء|بيانات", f"{idea} {category}", re.I) else "Unknown",
        "Medium",
        "Unknown",
    ]
    plan["risk_radar"] = [
        {"name": name, "level": level, "reason": reason, "fix": fix, "source": "ai_assumption"}
        for name, level, reason, fix in zip(risk_names, risk_levels, risk_reasons, risk_fixes)
    ]
    plan["do_not_start_with"] = (
        ["لا تشغّل الخدمة أو تقبل الدفع قبل التحقق من المتطلبات الرسمية.", "لا تشترِ معدات كبيرة قبل ظهور أدلة طلب."]
        if lang == "ar"
        else [
            "Do not operate or accept payment before verifying official requirements.",
            "Do not buy major equipment before demand evidence.",
        ]
    )
    plan["instead_do"] = (
        ["قابل عملاء محتملين.", "اجمع حجوزات أو تسجيلات بلا دفع.", "تحقق من تصنيف النشاط والموافقات المطلوبة رسمياً."]
        if lang == "ar"
        else [
            "Interview potential customers.",
            "Collect no-payment reservations or waitlist signups.",
            "Verify the activity classification and required approvals officially.",
        ]
    )
    plan["validation_before_spending"] = (
        [
            "ميّز بين الاهتمام ونية الشراء والحجز بلا دفع والدفع الفعلي.",
            "اجمع أدلة فعلية من وضع الإثبات فقط.",
            "تحقق من التكاليف والمتطلبات الرسمية قبل الإنفاق.",
        ]
        if lang == "ar"
        else [
            "Separate interest, stated intent, no-payment reservations, and actual payment.",
            "Use only Proof Mode entries as customer evidence.",
            "Verify cost estimates and official requirements before spending.",
        ]
    )
    plan["validation_questions"] = (
        [
            "كيف تحل هذه المشكلة الآن؟",
            "متى استخدمت بديلاً آخر؟",
            "ما الذي يجعلك تفكر في عرض جديد؟",
            "ما أبرز مخاوفك بشأن السعر أو الثقة؟",
            "هل تريد الانضمام إلى قائمة انتظار بلا دفع؟",
        ]
        if lang == "ar"
        else [
            "How do you solve this problem today?",
            "When did you last use an alternative?",
            "What would make you consider a new offer?",
            "What price or trust concern would stop you?",
            "Would you join a no-payment waitlist?",
        ]
    )
    report = plan["readiness_report"]
    report["target_customer"] = _target_customer(report.get("target_customer") or names[0], lang)
    report["main_risk"] = (
        "إنفاق المال قبل وجود أدلة عملاء أو تحقق رسمي."
        if lang == "ar"
        else "Spending before customer evidence or official checks."
    )
    report["next_step"] = (
        "قابل العملاء وسجّل نوايا بلا دفع؛ هذه توصية للتحقق وليست متطلباً مثبتاً."
        if lang == "ar"
        else "Interview leads and record no-payment intent; this is a recommended test, not a proven requirement."
    )
    report["what_not_to_start_with"] = (
        "التشغيل أو الدفع قبل التحقق الرسمي." if lang == "ar" else "Operation or payment before official checks."
    )
    report["estimated_first_test_cost_aed"] = max(0, _int(report.get("estimated_first_test_cost_aed")))
    plan["state"]["target_customer"] = report["target_customer"]
    plan["state"]["target_customer_source"] = "user_input" if inputs.get("user_type") else "ai_assumption"
    if inputs.get("user_type"):
        customer_labels = {
            "students": ("Students", "الطلاب"),
            "families": ("Families / households", "العائلات"),
            "tourists": ("Tourists / visitors", "السياح"),
            "professionals": ("Professionals", "المهنيون"),
            "small_businesses": ("Small businesses", "الشركات الصغيرة"),
            "residents": ("Residents", "السكان"),
            "online_customers": ("Online customers", "العملاء عبر الإنترنت"),
        }
        selected = customer_labels.get(inputs["user_type"])
        if selected:
            report["target_customer"] = selected[1 if lang == "ar" else 0]
            plan["state"]["target_customer"] = report["target_customer"]
    plan["state"]["estimated_test_cost_aed"] = report["estimated_first_test_cost_aed"]
    plan["founder_passport"] = {
        "status": "جاهز للتحقق، لا للتشغيل" if lang == "ar" else "Ready to validate, not operate",
        "first_action": "",
        "next_step": report["next_step"],
    }
    original_steps = plan.get("steps") or []
    # A breakdown for a differently ordered plan cannot price these new steps.
    step_costs = [None] * 7
    if isinstance(original_steps, list) and len(original_steps) == 7:
        step_costs = [
            _money(step.get("estimated_cost_aed")) if isinstance(step, dict) else None for step in original_steps
        ]
    plan["steps"] = [
        {
            "step_number": i + 1,
            "action": action,
            "description": description,
            "estimated_cost_aed": step_costs[i],
            "timeline_days": days,
            "who_to_contact": contact,
            "location": plan["state"]["region"],
        }
        for i, (action, description, days, contact) in enumerate(
            (
                [
                    ("مقابلات العملاء", "قابل عملاء مستهدفين وسجّل المشكلة والبدائل الحالية.", 3, "عملاء محتملون"),
                    ("اختبار الاهتمام", "أنشئ صفحة أو قائمة انتظار بلا دفع.", 2, "عملاء محتملون"),
                    ("مراجعة الأدلة", "قارن النوايا والاعتراضات والحجوزات بلا دفع.", 1, "عملاء محتملون"),
                    (
                        "تحقق رسمي",
                        "تحقق من تصنيف النشاط والموافقات المطلوبة لدى الجهة الرسمية المختصة.",
                        1,
                        "الجهة الرسمية المختصة",
                    ),
                    (
                        "جهز أصغر تجربة قانونية",
                        "جهز خطة فقط بعد التحقق من المتطلبات؛ لا تشغّل الخدمة بعد.",
                        2,
                        "شركاء محتملون",
                    ),
                    (
                        "نفّذ تجربة إذا سُمح بها",
                        "بعد تأكيد التراخيص والموافقات المطلوبة، نفّذ أصغر تجربة عملية مناسبة.",
                        2,
                        "عملاء التجربة",
                    ),
                    ("راجع وقرر", "راجع أدلة التجربة وقرر الخطوة التالية.", 1, "فريق المشروع"),
                ]
                if lang == "ar"
                else [
                    (
                        "Conduct targeted interviews",
                        "Ask target users about the problem and their current alternatives.",
                        3,
                        "Potential customers",
                    ),
                    (
                        "Create interest or waitlist test",
                        "Use a landing page or no-payment waitlist.",
                        2,
                        "Potential customers",
                    ),
                    (
                        "Review evidence",
                        "Compare stated intent, objections, and no-payment reservations.",
                        1,
                        "Potential customers",
                    ),
                    (
                        "Verify official requirements",
                        "Check the activity classification and required approvals with the relevant official authority.",
                        1,
                        "Relevant official authority",
                    ),
                    (
                        "Prepare smallest lawful pilot",
                        "Prepare a plan only after official checks; do not operate yet.",
                        2,
                        "Potential partners",
                    ),
                    (
                        "Run pilot if permitted",
                        "After confirming that required licences and approvals are in place, run the smallest practical pilot.",
                        2,
                        "Pilot participants",
                    ),
                    ("Review and decide", "Review actual pilot evidence before the next phase.", 1, "Founder team"),
                ]
            )
        )
    ]
    _sync_path_costs(plan)
    cost_risk = plan["risk_radar"][1]
    if plan["total_estimated_cost_aed"] is not None:
        cost_risk["level"] = "High" if plan["estimated_budget_gap_aed"] > 0 else "Medium"
        cost_risk["reason"] = (
            f"تقدير المسار {plan['total_estimated_cost_aed']:,.0f} درهم مقابل ميزانية أدخلها المستخدم قدرها {budget:,.0f} درهم؛ تحقق من عروض الأسعار."
            if lang == "ar"
            else f"The path estimate is AED {plan['total_estimated_cost_aed']:,.0f} against the user-entered AED {budget:,.0f} budget; verify quotes."
        )
    plan["estimate_note"] = (
        "تقدير تقريبي بالذكاء الاصطناعي — تحقق من عروض الأسعار المحلية والمتطلبات قبل الإنفاق."
        if lang == "ar"
        else "Planning estimate — verify costs and requirements before spending."
    )
    plan["first_customer_tip"] = (
        "ابحث عن ثلاثة عملاء محتملين لديهم نية واضحة؛ لا تعتبرهم عملاء دافعين قبل حدوث دفع فعلي وبعد التحقق الرسمي."
        if lang == "ar"
        else "Find three strong leads; do not call them paying customers until an actual payment occurs after official checks."
    )
    plan["pitches"] = (
        {
            "ten_sec": f"أختبر فكرة {idea} مع عملاء محتملين في {plan['state']['region']}.",
            "thirty_sec": "أجري مقابلات وأختبر قائمة انتظار بلا دفع قبل أي تشغيل أو إنفاق كبير.",
            "whatsapp": f"مرحباً، أختبر فكرة {idea}. كيف تحل هذه المشكلة اليوم؟",
            "instagram": f"نختبر فكرة {idea}. ما البديل الذي تستخدمه الآن؟",
        }
        if lang == "ar"
        else {
            "ten_sec": f"I am testing {idea} with potential customers in {plan['state']['region']}.",
            "thirty_sec": "I am interviewing potential customers and testing a no-payment waitlist before operating or spending heavily.",
            "whatsapp": f"Hi, I am testing {idea}. How do you solve this problem today?",
            "instagram": f"Testing {idea}. What alternative do you use now?",
        }
    )
    suggested_price = plan["state"]["suggested_test_price_aed"]
    if suggested_price:
        plan["pitches"]["thirty_sec"] += (
            f" مثال لسعر تمهيدي: {suggested_price:,} درهم (افتراض ذكاء اصطناعي للاختبار بلا دفع)."
            if lang == "ar"
            else f" Example introductory price: AED {suggested_price:,} (AI ASSUMPTION for a no-payment interest test)."
        )
    plan["first_step_today"] = (
        f"تحدث اليوم إلى خمسة عملاء محتملين حول {idea} واسألهم عن بدائلهم الحالية، من دون طلب دفع."
        if lang == "ar"
        else f"Talk to five potential customers about {idea} today; ask about their current alternatives without taking payment."
    )
    plan["whatsapp_message"] = (
        f"مرحباً، أختبر فكرة {idea} في {plan['state']['region']}. كيف تحل هذه المشكلة حالياً؟ وهل ترغب في الانضمام إلى قائمة انتظار بلا دفع؟"
        if lang == "ar"
        else f"Hi, I am testing {idea} in {plan['state']['region']}. How do you solve this today, and would you join a no-payment waitlist?"
    )
    plan["state"]["opportunity_score"] = plan.get("opportunity_score") or {}
    plan["state"]["first_action"] = str(plan.get("first_step_today") or "")
    plan["state"]["decision"] = str((plan.get("decision_engine") or {}).get("decision") or "")
    plan["readiness_report"]["best_first_action"] = plan["state"]["first_action"]
    if isinstance(plan.get("steps"), list):
        plan["total_timeline_days"] = sum(
            max(0, _int(step.get("timeline_days"))) for step in plan["steps"] if isinstance(step, dict)
        )
    if isinstance(plan.get("founder_passport"), dict):
        plan["founder_passport"]["first_action"] = plan["state"]["first_action"]
    return plan


def _normalize_plan(plan, inputs, lang):
    from plan_content import normalize_plan

    result = normalize_plan(plan, inputs, lang, _template_plan, _sync_path_costs)
    if result["state"].get("target_customer_source") == "ai_assumption":
        target = _target_customer(result["state"]["target_customer"], lang)
        result["state"]["target_customer"] = target
        result["readiness_report"]["target_customer"] = target
    return result


_BILINGUAL_PATHS = {
    "summary": "summary",
    "problem": "idea_overview.problem",
    "target_user": "idea_overview.target_user",
    "solution": "idea_overview.solution",
    "why_market": "idea_overview.why_market",
    "first_customer_channel": "readiness_report.first_customer_channel",
    "target_customer": "readiness_report.target_customer",
}


def _plan_path(plan, path):
    value = plan
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _set_plan_path(plan, path, value):
    parts = path.split(".")
    owner = plan
    for part in parts[:-1]:
        owner = owner.setdefault(part, {})
    owner[parts[-1]] = value


def _language_matches(value, lang, idea=""):
    text = str(value or "").replace(str(idea or ""), "") if idea else str(value or "")
    arabic = len(re.findall(r"[\u0600-\u06ff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return arabic > 0 and arabic * 3 >= latin if lang == "ar" else latin > 0 and latin * 3 >= arabic


def _plan_language_fallback(key, plan, lang):
    """Truthful localized copy when the model omits a bilingual field."""
    state = plan.get("state") or {}
    idea = state.get("idea") or ""
    target = state.get("target_customer") or ("عملاء محتملون" if lang == "ar" else "potential customers")
    if not _language_matches(target, lang, idea):
        target = _segment_names(idea, "", state.get("category", ""), lang)[0]
    region = state.get("region") or ("الإمارات" if lang == "ar" else "the UAE")
    ar = lang == "ar"
    values = {
        "summary": (
            f"اقتراح لاختبار فكرة {idea} مع {target} في {region}؛ لم يُتحقق من الطلب بعد."
            if ar
            else f"A plan to test {idea} with {target} in {region}; demand is not yet verified."
        ),
        "problem": (
            "المشكلة المحددة لدى هذه الشريحة فرضية تحتاج إلى مقابلات مع العملاء."
            if ar
            else "The specific customer problem is a hypothesis to test in interviews."
        ),
        "target_user": target,
        "solution": (
            f"قد تساعد فكرة {idea} هذه الشريحة؛ اختبر المنفعة قبل التشغيل."
            if ar
            else f"The proposed {idea} may help this segment; test the value before operating."
        ),
        "why_market": (
            f"اختار المستخدم سوق {region}؛ ما زال الطلب المحلي يحتاج إلى اختبار."
            if ar
            else f"The founder selected {region}; local demand still needs testing."
        ),
        "first_customer_channel": (
            "تواصل مباشر مع الشريحة المختارة لإجراء مقابلات بلا بيع."
            if ar
            else "Direct outreach to the selected segment for interviews, without selling."
        ),
        "target_customer": target,
    }
    if key in values:
        return values[key]
    dimension = key.rsplit("_", 1)[0]
    dimension_label = (
        {
            "local_fit": "ملاءمة الفكرة",
            "clear_customer": "وضوح العميل",
            "low_starting_cost": "تكلفة البدء",
            "easy_first_step": "سهولة الخطوة الأولى",
            "growth_potential": "إمكانات النمو",
        }.get(dimension, dimension)
        if ar
        else dimension.replace("_", " ")
    )
    if key.endswith("_reason"):
        return (
            f"تقييم مبدئي لبند {dimension_label} في فكرة {idea}؛ الأدلة الخاصة به غير كافية."
            if ar
            else f"Preliminary assessment of {dimension_label} for {idea}; evidence for this dimension is limited."
        )
    return (
        "تحقق من هذا البند مع الشريحة المختارة قبل الإنفاق."
        if ar
        else "Check this dimension with the selected segment before spending."
    )


def _compose_pitches(plan, lang):
    from plan_content import compose_pitches

    compose_pitches(plan, lang)


def _apply_plan_language(plan, bilingual, lang):
    source = bilingual.get(lang) if isinstance(bilingual, dict) else {}
    if not isinstance(source, dict):
        source = {}
    idea = (plan.get("state") or {}).get("idea") or ""
    fallback_used = False
    for key, path in _BILINGUAL_PATHS.items():
        original = _plan_path(plan, path)
        candidate = source.get(key)
        if isinstance(candidate, str) and candidate.strip() and len(candidate) <= 1200:
            candidate = safe_text(candidate, lang)
            same_numbers = sorted(re.findall(r"\d+(?:[.,]\d+)*", candidate.replace(idea, ""))) == sorted(
                re.findall(r"\d+(?:[.,]\d+)*", str(original or "").replace(idea, ""))
            )
            unsafe = re.search(
                r"<[^>]+>|\b(?:proven|validated|research shows|identified leads|guaranteed)\b|طلب مثبت|عملاء مؤكدون",
                candidate,
                re.I,
            )
            if same_numbers and not unsafe and _language_matches(candidate, lang, idea):
                _set_plan_path(plan, path, candidate)
                continue
        if key == "target_customer" and (plan.get("state") or {}).get("target_customer_source") == "user_input":
            continue
        if isinstance(original, str) and _language_matches(original, lang, idea):
            continue
        _set_plan_path(plan, path, _plan_language_fallback(key, plan, lang))
        fallback_used = True
    if (plan.get("state") or {}).get("target_customer_source") == "ai_assumption":
        plan["state"]["target_customer"] = plan["readiness_report"].get("target_customer", "")
    _compose_pitches(plan, lang)
    plan["_localization_status"] = "fallback" if fallback_used else "complete"
    plan["_content_lang"] = lang


def _safeguard_plan(plan, lang):
    # Filtering is per sentence at normalization; do not discard neighbouring
    # model reasoning or an entire regulatory field here.
    return deepcopy(plan)
