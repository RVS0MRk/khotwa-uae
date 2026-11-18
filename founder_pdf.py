"""Founder PDF layout, RTL shaping and chart rendering."""

import os, io, re, urllib.request, logging
from html import escape
from copy import deepcopy
from plan_utils import _int, _money, _sync_path_costs
from plan_normalize import _normalize_plan, _apply_plan_language, _segment_names
from content_safety import export_plan
from disclosures import AI_DISCLOSURE, PROOF_DISCLOSURE, TRANSLATION_NOTICE

logger = logging.getLogger(__name__)


def _format_money(value, decimals=2):
    from financial_report import format_value

    return format_value("money", value).removesuffix(" AED")


FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


AMIRI_PATH = os.path.join(FONT_DIR, "Amiri-Regular.ttf")


_ARABIC_READY = None


def ensure_arabic_font():
    global _ARABIC_READY
    if _ARABIC_READY is not None:
        return _ARABIC_READY
    try:
        if not os.path.exists(AMIRI_PATH):
            raise FileNotFoundError("Bundled Arabic PDF font is missing")
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        pdfmetrics.registerFont(TTFont("Amiri", AMIRI_PATH))
        pdfmetrics.registerFontFamily("Amiri", normal="Amiri", bold="Amiri", italic="Amiri", boldItalic="Amiri")
        _ARABIC_READY = True
    except Exception as e:
        logger.error("Arabic font setup failed: %s", type(e).__name__)
        _ARABIC_READY = False
    return _ARABIC_READY


def shape_ar(text):
    """Reshape + bidi Arabic text so it renders correctly in PDF."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


def _pdf_text(text):
    """Use portable punctuation before shaping or handing text to ReportLab."""
    text = str(text)
    text = re.sub(r"[\u2010-\u2015\u2212\ufe63\uff0d\u25a0]", "-", text)
    return text.translate(
        str.maketrans(
            {
                "\u00a0": " ",
                "\u202f": " ",
                "\u00ad": "",
                "‘": "'",
                "’": "'",
                "“": '"',
                "”": '"',
                "…": "...",
                "✓": "+",
                "✗": "-",
                "✔": "+",
                "✘": "-",
                "•": "-",
                "\ufffd": "?",
            }
        )
    )


def _localize_pdf_plan(original, lang):
    """Localize application-owned planning copy without translating business names.

    Proof entries, prices, scores, user inputs and custom model text stay intact.
    The same bilingual defaults used by /generate also own the PDF defaults.
    """
    if original.get("_canonical_id"):
        alternate = original.get("_alternate_plan")
        use_alternate = (isinstance(alternate, dict) and alternate.get("_presentation_lang") == lang
                         and alternate.get("_canonical_id") == original["_canonical_id"])
        p = deepcopy(alternate if use_alternate else original)
        for key in ("opportunity_score", "state", "proof_summary", "_financial_inputs"):
            if key in original:
                p[key] = deepcopy(original[key])
        p.pop("_alternate_plan", None)
        return _sync_path_costs(p)
    alternate = original.get("_alternate_plan") if isinstance(original, dict) else None
    use_alternate = isinstance(alternate, dict) and alternate.get("_content_lang") == lang
    source = alternate if use_alternate else original
    p = deepcopy(source)
    if use_alternate:
        # Proof Mode is edited after generation. Keep the latest browser state
        # while using the matching-language text from the original response.
        for key in ("proof_summary", "_financial_inputs"):
            if key in original:
                p[key] = deepcopy(original[key])
        current_score = original.get("opportunity_score") or {}
        translated_score = p.get("opportunity_score") or {}
        for key in ("total", "clear_customer"):
            if key == "total" and key in current_score:
                translated_score[key] = current_score[key]
            elif key == "clear_customer" and isinstance(current_score.get(key), dict):
                translated_score.setdefault(key, {})["score"] = current_score[key].get("score", 0)
        p["opportunity_score"] = translated_score
        if isinstance(original.get("state"), dict):
            p.setdefault("state", {})["evidence"] = deepcopy(original["state"].get("evidence", {}))
    p = _sync_path_costs(p)
    p.pop("_alternate_plan", None)
    if lang == "ar" and not use_alternate and p.get("_content_lang") != "ar":
        # Legacy callers can request an Arabic PDF from an English plan that
        # predates bilingual generation. Localize prose conservatively.
        _apply_plan_language(p, {}, "ar")
    if use_alternate and _int((p.get("proof_summary") or {}).get("total_responses")):
        proof = p["proof_summary"]
        count = _int(proof["total_responses"])
        paid = _int(proof.get("actual_payments")) + _int(proof.get("repeat_customers"))
        decision = p.setdefault("decision_engine", {})
        decision["decision"] = (
            ("راجع أدلة التجربة" if paid else "تحقق أكثر")
            if lang == "ar"
            else ("Review pilot evidence" if paid else "Validate more")
        )
        decision["reason"] = (
            f"سُجلت {count} إدخالات في وضع الإثبات؛ راجع قوتها قبل اتخاذ قرار."
            if lang == "ar"
            else f"{count} entries are recorded in Proof Mode; review their strength before deciding."
        )
        decision["next_test_action"] = (
            "راجع الأدلة وتحقق من المتطلبات الرسمية قبل أي تجربة تشغيلية."
            if lang == "ar"
            else "Review the evidence and verify official requirements before any operational test."
        )
        p.setdefault("state", {})["decision"] = decision["decision"]
    if lang != "ar":
        return p
    state, report = p.get("state") or {}, p.get("readiness_report") or {}
    inputs = {
        "idea": state.get("idea") or report.get("idea") or p.get("business_name_suggestion", ""),
        "idea_source": state.get("idea_source", "user_input"),
        "category": state.get("category") or p.get("_category", ""),
        "region": state.get("region") or p.get("_region", "UAE-wide"),
        "context": state.get("context") or p.get("_context", "Not sure"),
        "user_type": state.get("customer_type") or p.get("_user_type", ""),
        "budget": state.get("user_budget_aed", p.get("_budget", 0)),
    }
    defaults = _normalize_plan(deepcopy(p), inputs, "ar")
    for key in (
        "small_test_plan",
        "seven_day_plan",
        "validation_questions",
        "validation_before_spending",
        "do_not_start_with",
        "instead_do",
        "founder_passport",
        "first_step_today",
        "whatsapp_message",
        "estimate_note",
    ):
        if key in defaults:
            p[key] = defaults[key]
    # Actions here are the app's seven standard steps; preserve amounts/timing.
    if len(p.get("steps") or []) == 7:
        for step, translated in zip(p["steps"], defaults["steps"]):
            step.update({key: translated[key] for key in ("action", "description")})
    report = p.setdefault("readiness_report", {})
    for key in ("best_first_action", "main_risk", "next_step", "what_not_to_start_with"):
        report[key] = defaults["readiness_report"][key]
    if not report.get("first_customer_channel") or report.get("first_customer_channel") in (
        "Direct outreach and interviews",
        "Direct outreach",
        "WhatsApp",
        "Interviews",
    ):
        report["first_customer_channel"] = "تواصل مباشر ومقابلات العملاء"
    p["risk_radar"] = defaults["risk_radar"]
    if _int((p.get("proof_summary") or {}).get("total_responses")):
        p["risk_radar"][0]["reason"] = "راجع ردود العملاء المسجلة في وضع الإثبات؛ الاهتمام وحده لا يثبت الطلب."
        count = _int(p["proof_summary"]["total_responses"])
        p.setdefault("idea_overview", {})[
            "evidence"
        ] = f"تم تسجيل {count} من ردود العملاء في وضع الإثبات؛ الاهتمام وحده لا يثبت الطلب."
    else:
        p["decision_engine"] = defaults["decision_engine"]
        p.setdefault("idea_overview", {})["evidence"] = defaults["idea_overview"]["evidence"]
    target = str(report.get("target_customer") or "")
    english_names = _segment_names(inputs["idea"], target, inputs["category"], "en")
    arabic_names = _segment_names(inputs["idea"], target, inputs["category"], "ar")
    segment_labels = dict(zip(english_names, arabic_names))
    p["customer_personas"] = defaults["customer_personas"]
    for persona in p["customer_personas"]:
        persona["name"] = segment_labels.get(persona["name"], persona["name"])
    for holder in (report, p.get("state", {})):
        holder["target_customer"] = segment_labels.get(holder.get("target_customer"), holder.get("target_customer", ""))
    return p


def _chart_ar(text):
    # New Matplotlib uses libraqm for shaping/bidi; older versions need it here.
    # Feeding already reversed text to libraqm reverses it a second time.
    from matplotlib.ft2font import FT2Font

    return text if hasattr(FT2Font, "_layout") else shape_ar(text)


def make_score_chart(sc, ar=False):
    """Horizontal bar chart of the 5 score categories -> PNG bytes."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names_en = {
        "local_fit": "Personal / Idea Fit",
        "clear_customer": "Customer Need",
        "low_starting_cost": "Starting Cost",
        "easy_first_step": "Ease of Testing",
        "growth_potential": "Growth Potential",
    }
    keys = list(names_en.keys())
    vals = [_int((sc.get(k) or {}).get("score", 0)) for k in keys]
    labels = [names_en[k] for k in keys]
    font_options = {}
    if ar:
        from matplotlib.font_manager import FontProperties

        font_options = {"fontproperties": FontProperties(fname=AMIRI_PATH)}
        labels = [
            _chart_ar(name)
            for name in ("ملاءمة الفكرة", "حاجة العملاء", "تكلفة البداية", "سهولة الاختبار", "إمكانات النمو")
        ]
    fig, ax = plt.subplots(figsize=(5.2, 2.4), dpi=150)
    y = range(len(labels))
    ax.barh(list(y), vals, color="#378ADD", height=0.6)
    ax.set_xlim(0, 5)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9, **font_options)
    ax.invert_yaxis()
    ax.set_xticks([0, 1, 2, 3, 4, 5])
    ax.tick_params(axis="x", labelsize=8)
    for i, v in enumerate(vals):
        assessed = type((sc.get(keys[i]) or {}).get("score")) in (int, float)
        label = f"{v}/5" if assessed else (_chart_ar("لم يُقيّم") if ar else "Not assessed")
        ax.text(v + 0.1, i, label, va="center", fontsize=9, color="#1a1a2e", **font_options)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    plt.tight_layout()
    b = io.BytesIO()
    plt.savefig(b, format="png", bbox_inches="tight")
    plt.close(fig)
    b.seek(0)
    return b


def make_steps_charts(steps, ar=False):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    font_options = {}
    if ar:
        from matplotlib.font_manager import FontProperties

        font_options = {"fontproperties": FontProperties(fname=AMIRI_PATH)}
    labels = [_chart_ar(f"خطوة {s.get('step_number','')}") if ar else f"Step {s.get('step_number','')}" for s in steps]
    days = [_int(s.get("timeline_days", 0)) for s in steps]
    costs = [_money(s.get("estimated_cost_aed")) for s in steps]
    costs_known = bool(costs) and all(value is not None for value in costs)
    # timeline bar
    fig1, ax1 = plt.subplots(figsize=(2.9, 2.2), dpi=150)
    ax1.bar(labels, days, color="#378ADD")
    ax1.set_title(_chart_ar("مدة كل خطوة (أيام)") if ar else "Timeline per step (days)", fontsize=9, **font_options)
    if ar:
        for label in ax1.get_xticklabels():
            label.set_fontproperties(font_options["fontproperties"])
    ax1.tick_params(labelsize=7)
    plt.setp(ax1.get_xticklabels(), rotation=30, ha="right")
    for s in ["top", "right"]:
        ax1.spines[s].set_visible(False)
    plt.tight_layout()
    b1 = io.BytesIO()
    plt.savefig(b1, format="png", bbox_inches="tight")
    plt.close(fig1)
    b1.seek(0)
    # cost donut
    fig2, ax2 = plt.subplots(figsize=(2.9, 2.2), dpi=150)
    pal = ["#534AB7", "#1D9E75", "#D85A30", "#378ADD", "#BA7517"]
    if costs_known and sum(costs) > 0:
        ax2.pie(costs, colors=pal, wedgeprops=dict(width=0.42))
    else:
        label = (
            ("التكلفة المقدرة: 0 درهم" if ar else "Estimated cost: 0 AED")
            if costs_known
            else ("التكاليف غير مقدرة" if ar else "Costs not estimated")
        )
        ax2.text(
            0.5,
            0.5,
            _chart_ar(label) if ar else label,
            ha="center",
            va="center",
            transform=ax2.transAxes,
            **font_options,
        )
        ax2.set_axis_off()
    ax2.set_title(
        _chart_ar("تفصيل التكلفة المقدرة (درهم)") if ar else "Estimated cost breakdown (AED)",
        fontsize=9,
        **font_options,
    )
    plt.tight_layout()
    b2 = io.BytesIO()
    plt.savefig(b2, format="png", bbox_inches="tight")
    plt.close(fig2)
    b2.seek(0)
    return b1, b2


def build_pdf(p, lang="en"):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image,
        Frame,
        PageTemplate,
        BaseDocTemplate,
        KeepTogether,
    )
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT

    from pdf_text import Paragraph

    localized = _localize_pdf_plan(p, lang)
    localized["_export_lang"] = lang
    p = export_plan(localized)
    ar = lang == "ar"
    font_ok = ensure_arabic_font() if ar else False
    if ar and not font_ok:
        raise RuntimeError("Bundled Arabic font unavailable")
    BASE = "Amiri" if (ar and font_ok) else "Helvetica"
    BOLD = "Amiri" if (ar and font_ok) else "Helvetica-Bold"
    align = TA_RIGHT if ar else TA_LEFT

    fixed_labels = {
        "USER INPUT": "إدخال المستخدم",
        "AI SUGGESTION SELECTED BY USER": "اقتراح ذكاء اصطناعي اختاره المستخدم",
        "AI ASSUMPTION": "افتراض ذكاء اصطناعي",
        "AI ESTIMATE": "تقدير ذكاء اصطناعي",
        "RECOMMENDED ACTION": "إجراء موصى به",
        "Medium": "متوسط",
        "High": "مرتفع",
        "Low": "منخفض",
        "Unknown": "غير محدد",
        "Ready to test": "جاهز للاختبار",
        "Validate more": "تحقق أكثر",
        "Review pilot evidence": "راجع أدلة التجربة",
        "AED": "درهم",
        "Services & Maintenance": "الخدمات والصيانة",
        "Food & Catering": "الطعام والتموين",
        "Agriculture & Farming": "الزراعة",
        "Retail & Trading": "التجزئة والتجارة",
        "Tourism & Hospitality": "السياحة والضيافة",
        "Technology & Digital": "التقنية والخدمات الرقمية",
        "Handicrafts & Arts": "الحرف والفنون",
        "Health & Wellness": "الصحة والعافية",
        "Education & Tutoring": "التعليم والدروس",
        "Other": "أخرى",
        "Local service or digital": "خدمة محلية أو رقمية",
        "Local service": "خدمة محلية",
        "Not sure": "غير محدد",
        "UAE-wide": "جميع أنحاء الإمارات",
        "Abu Dhabi": "أبوظبي",
    }

    def tx(s):
        s = _pdf_text(s)
        if ar:
            for english, arabic in fixed_labels.items():
                s = re.sub(r"\b" + re.escape(english) + r"\b", arabic, s)
        return escape(s)

    NAVY = colors.HexColor("#1a1a2e")
    BLUE = colors.HexColor("#378ADD")
    GREY = colors.HexColor("#666666")
    LIGHT = colors.HexColor("#f7f7f5")

    buf = io.BytesIO()

    def header_band(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 22 * mm, A4[0], 22 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(BOLD, 12)
        title = shape_ar(_pdf_text("خطوة — من الفكرة إلى الخطوة الأولى")) if ar else "Khotwa - From idea to first step"
        if ar:
            canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 14 * mm, title)
        else:
            canvas.drawString(15 * mm, A4[1] - 14 * mm, title)
        canvas.setFillColor(colors.HexColor("#cccccc"))
        canvas.setFont(BASE, 8)
        canvas.drawRightString(A4[0] - 15 * mm, 10 * mm, f"{doc.page}")
        canvas.restoreState()

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        topMargin=22 * mm,
        bottomMargin=12 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        title="خطوة — تقرير الخطوة الأولى" if ar else "Khotwa - Founder First-Step Report",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="band", frames=[frame], onPage=header_band)])

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "h1", fontName=BOLD, textColor=NAVY, fontSize=20, leading=26, spaceAfter=8, alignment=align, splitLongWords=1
    )
    sub = ParagraphStyle("sub", fontName=BASE, textColor=GREY, fontSize=11, leading=15, spaceAfter=14, alignment=align)
    h2 = ParagraphStyle("h2", fontName=BOLD, textColor=NAVY, fontSize=13, spaceBefore=10, spaceAfter=6, alignment=align, keepWithNext=True)
    body = ParagraphStyle(
        "body", fontName=BASE, fontSize=10, leading=15, spaceAfter=3, alignment=align, splitLongWords=1
    )
    small = ParagraphStyle(
        "small", fontName=BASE, fontSize=9.2, textColor=GREY, leading=13, alignment=align, splitLongWords=1
    )
    table_head = ParagraphStyle("table_head", parent=small, textColor=colors.white)

    L = {
        "en": dict(
            report="Khotwa Founder First-Step Report",
            score="Preliminary Opportunity Score",
            decision="Decision",
            exec="Executive summary",
            idea="Business idea",
            target="Target customer",
            first="First step today",
            risk="Main risk",
            next="Next step",
            d7="First 7 days",
            day="Day",
            focus="Focus",
            action="Action",
            vq="5 customer validation questions",
            wa="WhatsApp test message",
            stp="Small test plan before spending",
            rr="Founder readiness report",
            best="Best first action",
            testcost="First test cost",
            notstart="What not to start with",
            channel="First customer channel",
            fuller="The fuller path (when you're ready)",
            total="Total cost",
            timeline="Estimated timeline",
            res="Suggested official resources to check",
            note="Regulatory requirements have not been verified. Check the official activity classification and any required approvals with the relevant UAE authority before operating.",
            strong="Based mainly on assumptions — customer evidence is still required.",
            medium="Based mainly on assumptions — customer evidence is still required.",
            weak="Based mainly on assumptions — customer evidence is still required.",
            deng="Founder decision",
            pm="Proof mode summary",
            pm_int="Interested",
            pm_maybe="Maybe",
            pm_avg="Average entered price (AED)",
            pm_pre="No-payment reservations",
            pm_concern="Top concern",
            pm_none="No customer feedback entered yet. Use the 10-person test to validate demand.",
            donot="Do not start with",
            instead="Instead, do this first",
            nexttest="Next test action",
            testbudget="Suggested test budget (estimate)",
            bys="Before you spend",
            bys_plan="Your budget",
            bys_test="Estimated first test",
            bys_save="Budget remaining after test",
            passport="Founder passport",
            pp_status="Status",
            pp_first="First action",
            personas="Potential customer segments (AI assumptions)",
            risks="Risk radar",
            pitches="Pitch ideas",
            cares="Cares about",
            reach="Reach through",
            ask="Ask",
        ),
        "ar": dict(
            report="خطوة — تقرير الخطوة الأولى للمؤسس",
            score="درجة الفرصة المبدئية",
            decision="القرار",
            exec="الملخص التنفيذي",
            idea="فكرة المشروع",
            target="العميل المستهدف",
            first="خطوتك الأولى اليوم",
            risk="الخطر الرئيسي",
            next="الخطوة التالية",
            d7="أول 7 أيام",
            day="اليوم",
            focus="التركيز",
            action="الإجراء",
            vq="5 أسئلة للتحقق من العملاء",
            wa="رسالة واتساب للاختبار",
            stp="خطة اختبار صغيرة قبل الإنفاق",
            rr="تقرير جاهزية المؤسس",
            best="أفضل إجراء أول",
            testcost="تكلفة الاختبار الأول",
            notstart="ما لا تبدأ به",
            channel="قناة أول عميل",
            fuller="المسار الكامل (عندما تكون جاهزاً)",
            total="التكلفة الإجمالية",
            timeline="المدة المقدرة",
            res="مصادر رسمية مقترحة للمراجعة",
            note="المتطلبات التنظيمية غير مؤكدة. تحقق من تصنيف النشاط والموافقات المطلوبة لدى الجهة الإماراتية المختصة قبل التشغيل.",
            strong="تعتمد أساساً على افتراضات — ما زلنا بحاجة إلى أدلة العملاء.",
            medium="تعتمد أساساً على افتراضات — ما زلنا بحاجة إلى أدلة العملاء.",
            weak="تعتمد أساساً على افتراضات — ما زلنا بحاجة إلى أدلة العملاء.",
            deng="قرار المؤسس",
            pm="ملخص وضع الإثبات",
            pm_int="مهتم",
            pm_maybe="ربما",
            pm_avg="متوسط السعر المدخل (درهم)",
            pm_pre="حجوزات بلا دفع",
            pm_concern="أبرز قلق",
            pm_none="لم تُدخل ملاحظات العملاء بعد. استخدم اختبار الـ10 أشخاص للتحقق من الطلب.",
            donot="لا تبدأ بـ",
            instead="بدلاً من ذلك، ابدأ بـ",
            nexttest="إجراء الاختبار التالي",
            testbudget="ميزانية اختبار مقترحة (تقدير)",
            bys="قبل أن تنفق",
            bys_plan="ميزانيتك",
            bys_test="تكلفة الاختبار المقدرة",
            bys_save="الميزانية المتبقية بعد الاختبار",
            passport="جواز المؤسس",
            pp_status="الحالة",
            pp_first="أول إجراء",
            personas="شرائح عملاء محتملة (افتراضات)",
            risks="رادار المخاطر",
            pitches="أفكار العرض",
            cares="يهتم بـ",
            reach="الوصول عبر",
            ask="اسأل",
        ),
    }[lang if lang in ("en", "ar") else "en"]

    sc = p.get("opportunity_score", {}) or {}
    total = sc.get("total")
    score_label = f"{total} / 25" if type(total) is int else ("غير مكتمل" if ar else "Incomplete")
    decision = (p.get("decision_engine") or {}).get("decision") or L["medium"]
    r = p.get("readiness_report", {}) or {}
    state = p.get("state", {}) or {}

    def kv(rows):
        data = [
            [
                Paragraph(tx(k), ParagraphStyle("k", parent=body, fontName=BOLD)),
                Paragraph(tx(v) if v not in (None, "") else "-", body),
            ]
            for k, v in rows
        ]
        if ar:
            data = [[c2, c1] for c1, c2 in data]
            t = Table(data, colWidths=[None, 50 * mm])
        else:
            t = Table(data, colWidths=[50 * mm, None])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#eeeeee")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return t

    E = []
    # ---- PAGE 1 ----
    E.append(Paragraph(tx(AI_DISCLOSURE["ar" if ar else "en"]), small))
    E.append(Paragraph(tx(PROOF_DISCLOSURE["ar" if ar else "en"]), small))
    if p.get("_source_lang") and p["_source_lang"] != lang and p.get("_localization_status") == "fallback":
        E.append(Paragraph(tx(TRANSLATION_NOTICE[lang]), small))
    E.append(Spacer(1, 8))
    E.append(
        Paragraph(tx("اسم تجاري مقترح · افتراض ذكاء اصطناعي" if ar else "Suggested brand name · AI ASSUMPTION"), small)
    )
    E.append(Paragraph(tx(p.get("business_name_suggestion") or state.get("idea") or ""), h1))
    E.append(Paragraph(tx(p.get("summary", "")), sub))
    # score block: number + chart side by side
    try:
        chart_img = Image(make_score_chart(sc, ar), width=110 * mm, height=50 * mm)
    except Exception as e:
        logger.error("Score chart failed: %s", type(e).__name__)
        chart_img = Paragraph("", body)
    score_size = 30 if type(total) is int else 22
    score_para = Paragraph(
        f'<font size={score_size} color="#17634e">{score_label}</font><br/><br/><b>{tx(L["decision"])}:</b> {tx(decision)}',
        body,
    )
    sb = (
        Table([[score_para, chart_img]], colWidths=[55 * mm, doc.width - 55 * mm])
        if not ar
        else Table([[chart_img, score_para]], colWidths=[doc.width - 55 * mm, 55 * mm])
    )
    sb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    E.append(Paragraph(tx(L["score"]), h2))
    E.append(sb)
    E.append(
        Paragraph(
            tx(
                (p.get("_proof_presentation") or {}).get("text", "")
            ),
            small,
        )
    )
    E.append(Paragraph(tx(
        (f"تغطية التقييم: {sc.get('assessed_count', 0)} من 5. " if ar else
         f"Assessment coverage: {sc.get('assessed_count', 0)} of 5. ") +
        (("النتيجة غير مكتملة؛ لا نقاط للمعلومات المفقودة." if ar else
          "Incomplete assessment; missing information earns no points.") if total is None else
         ("درجة مبدئية وليست احتمال نجاح تجاري." if ar else
          "Provisional assessment, not a probability of business success."))
    ), small))
    E.append(Spacer(1, 8))
    E.append(Paragraph(tx(L["exec"]), h2))
    overview = p.get("idea_overview") or {}
    idea_source = (
        "AI SUGGESTION SELECTED BY USER" if state.get("idea_source") == "ai_suggestion_selected" else "USER INPUT"
    )
    E.append(
        kv(
            [
                (L["idea"] + " (" + idea_source + ")", state.get("idea") or r.get("idea") or p.get("summary", "")),
                ("الملخص (AI ASSUMPTION)" if ar else "Summary (AI ASSUMPTION)", p.get("summary", "")),
                ("المشكلة (AI ASSUMPTION)" if ar else "Problem (AI ASSUMPTION)", overview.get("problem", "")),
                ("الحل (AI ASSUMPTION)" if ar else "Solution (AI ASSUMPTION)", overview.get("solution", "")),
                (
                    "سبب اختيار السوق (AI ASSUMPTION)" if ar else "Why this market (AI ASSUMPTION)",
                    overview.get("why_market", ""),
                ),
                ("الفئة" if ar else "Category", state.get("category") or p.get("_category", "")),
                ("السوق" if ar else "Market", state.get("region") or p.get("_region", "")),
                ("نوع المشروع" if ar else "Business context", state.get("context") or p.get("_context", "")),
                (
                    L["target"]
                    + (" (USER INPUT)" if state.get("target_customer_source") == "user_input" else " (AI ASSUMPTION)"),
                    state.get("target_customer") or r.get("target_customer", ""),
                ),
                (L["first"], p.get("first_step_today", "")),
                (L["risk"], r.get("main_risk", "")),
                (L["next"], r.get("next_step", "")),
            ]
        )
    )
    # decision engine card
    de = p.get("decision_engine", {}) or {}
    if de.get("decision"):
        E.append(Spacer(1, 8))
        E.append(Paragraph(tx(L["deng"]), h2))
        extra = ""
        if de.get("risk_level"):
            extra += f'{tx(L["risk"])}: {tx(de.get("risk_level"))}  '
        if de.get("recommended_test_budget_aed"):
            extra += tx(f'{L["testbudget"]}: {_format_money(de.get("recommended_test_budget_aed"))} AED (AI ESTIMATE)')
        dec_tbl = Table(
            [
                [
                    Paragraph(
                        f'<b>{tx(de.get("decision",""))}</b><br/>{tx(de.get("reason",""))}<br/><font color="#666666">{tx(L["nexttest"])}: {tx(de.get("next_test_action",""))}</font><br/><font color="#666666">{extra}</font>',
                        body,
                    )
                ]
            ],
            colWidths=[None],
        )
        dec_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4ff")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#2f6fed")),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        E.append(dec_tbl)
    # Before You Spend card
    budget = _int(state.get("user_budget_aed", p.get("_budget", 0)))
    test_cost = _int(state.get("estimated_test_cost_aed", r.get("estimated_first_test_cost_aed", 0)))
    protected = max(0, budget - test_cost)
    if budget > 0:
        E.append(Spacer(1, 8))
        estimated = (
            f"{_format_money(test_cost)} AED (AI ESTIMATE)"
            if test_cost
            else ("لم تُقدّر بعد" if ar else "Not estimated yet")
        )
        remaining = f'{tx(L["bys_save"])}: <b>{tx(_format_money(protected) + " AED")}</b>' if test_cost else ""
        bys_tbl = Table(
            [
                [
                    Paragraph(
                        f'{tx(L["bys_plan"] + " (USER INPUT)")}: <b>{tx(_format_money(budget) + " AED")}</b><br/>{tx(L["bys_test"])}: <b>{tx(estimated)}</b><br/><font color="#0a7a3c">{remaining}</font>',
                        body,
                    )
                ]
            ],
            colWidths=[None],
        )
        bys_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e7f8ee")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#1d9e75")),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        E.append(KeepTogether([Paragraph(tx(L["bys"]), h2), bys_tbl]))
    # Founder Passport
    pp = p.get("founder_passport", {}) or {}
    E.append(Spacer(1, 8))
    E.append(Paragraph(tx(L["passport"]), h2))
    E.append(
        kv(
            [
                (L["idea"], r.get("idea") or p.get("summary", "")),
                (L["pp_status"], pp.get("status", "Ready to test")),
                (L["pp_first"], pp.get("first_action") or p.get("first_step_today", "")),
                (L["score"], score_label),
                (L["decision"], de.get("decision", "")),
                (L["channel"], r.get("first_customer_channel", "")),
                (
                    L["testcost"],
                    (
                        f"{_format_money(r.get('estimated_first_test_cost_aed'))} AED (AI ESTIMATE)"
                        if r.get("estimated_first_test_cost_aed") not in (None, "")
                        else "-"
                    ),
                ),
                (L["next"], pp.get("next_step") or r.get("next_step", "")),
            ]
        )
    )
    E.append(Spacer(1, 10))

    # ---- PAGE 2 ----
    E.append(Paragraph(tx(L["d7"]), h2))
    drows = [
        [
            Paragraph(tx(L["day"]), table_head),
            Paragraph(tx(L["focus"]), table_head),
            Paragraph(tx(L["action"]), table_head),
        ]
    ]
    for d in p.get("seven_day_plan", []):
        detail = tx(d.get("action", ""))
        if d.get("success_check"):
            detail += "<br/>" + tx(("النجاح: " if ar else "Success: ") + str(d["success_check"]))
        drows.append(
            [Paragraph(tx(d.get("day", "")), small), Paragraph(tx(d.get("focus", "")), small), Paragraph(detail, small)]
        )
    if ar:
        drows = [list(reversed(r0)) for r0 in drows]
    dt = Table(
        drows,
        colWidths=([None, 40 * mm, 14 * mm] if ar else [14 * mm, 40 * mm, None]),
        repeatRows=1,
        rowSplitRange=(2, -1),
    )
    dt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    E.append(dt)
    E.append(Spacer(1, 10))
    E.append(Paragraph(tx(L["vq"]), h2))
    for i, q in enumerate(p.get("validation_questions", []), 1):
        E.append(Paragraph(tx(f"{i}. {q}"), body))
    E.append(Spacer(1, 8))
    E.append(Paragraph(tx(L["wa"]), h2))
    E.append(Paragraph(tx(p.get("whatsapp_message", "")), body))
    E.append(Spacer(1, 8))
    tp = p.get("small_test_plan", {}) or {}
    E.append(Paragraph(tx(L["stp"]), h2))
    if tp.get("intro"):
        E.append(Paragraph(tx(tp["intro"]), body))
    for pt in tp.get("points", []):
        E.append(Paragraph(tx(f"• {pt}"), body))
    E.append(Spacer(1, 10))

    # ---- PAGE 3: PROOF MODE SUMMARY ----
    E.append(Paragraph(tx(L["pm"]), h2))
    pm = p.get("proof_summary", {}) or {}
    if pm and _int(pm.get("total_responses", 0)) > 0:
        E.append(
            kv(
                [
                    (L["pm_int"], f"{_int(pm.get('interested'))}/{_int(pm.get('total_responses'))}"),
                    (L["pm_maybe"], f"{_int(pm.get('maybe'))}/{_int(pm.get('total_responses'))}"),
                    (L["pm_avg"], f"{_format_money(pm.get('avg_price'))} AED"),
                    (L["pm_pre"], f"{_int(pm.get('no_payment_reservations'))}/{_int(pm.get('total_responses'))}"),
                    ("دفع فعلي" if ar else "Actual payments", str(_int(pm.get("actual_payments")))),
                    ("عملاء متكررون" if ar else "Repeat customers", str(_int(pm.get("repeat_customers")))),
                    (L["pm_concern"], pm.get("top_concern", "-")),
                    (L["decision"], (p.get("_proof_presentation") or {}).get("text", "-")),
                ]
            )
        )
    else:
        E.append(Paragraph(tx(L["pm_none"]), body))
    E.append(Spacer(1, 10))

    # ---- CUSTOMER HYPOTHESES AND RISKS ----
    E.append(Paragraph(tx(L["personas"]), h2))
    for per in (p.get("customer_personas", []) or [])[:3]:
        E.append(Paragraph(f'<b>{tx(per.get("name", "") + " (AI ASSUMPTION)")}</b>', body))
        E.append(Paragraph(f'{tx(L["cares"])}: {tx(per.get("cares_about",""))}', small))
        if per.get("current_alternative"):
            E.append(
                Paragraph(
                    f'{tx("البديل الحالي المحتمل" if ar else "Possible current alternative")}: {tx(per["current_alternative"])}',
                    small,
                )
            )
        if per.get("why_benefit"):
            E.append(
                Paragraph(
                    f'{tx("لماذا قد يستفيد" if ar else "Why they might benefit")}: {tx(per["why_benefit"])}', small
                )
            )
        E.append(Paragraph(f'{tx(L["reach"])}: {tx(per.get("reach_through",""))}', small))
        E.append(Paragraph(f'{tx(L["ask"])}: {tx(per.get("ask",""))}', small))
        E.append(Spacer(1, 4))
    E.append(Spacer(1, 6))
    E.append(Paragraph(tx(L["risks"]), h2))
    rr_rows = [
        [
            Paragraph(tx(L["risk"]), table_head),
            Paragraph(tx(L["pp_status"]), table_head),
            Paragraph(tx(L["cares"]), table_head),
            Paragraph(tx(L["instead"]), table_head),
        ]
    ]
    for rk in p.get("risk_radar", []) or []:
        rr_rows.append(
            [
                Paragraph(tx(rk.get("name", "")), small),
                Paragraph(tx(rk.get("level", "")), small),
                Paragraph(tx(rk.get("reason", "")), small),
                Paragraph(tx(rk.get("fix", "")), small),
            ]
        )
    if len(rr_rows) > 1:
        if ar:
            rr_rows = [list(reversed(r0)) for r0 in rr_rows]
        rrt = Table(rr_rows, colWidths=([None, 52 * mm, 18 * mm, 28 * mm] if ar else [28 * mm, 18 * mm, 52 * mm, None]))
        rrt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        E.append(rrt)
    E.append(Spacer(1, 10))

    # ---- PAGE 5: READINESS ----
    E.append(Paragraph(tx(L["rr"]), h2))
    E.append(
        kv(
            [
                (L["idea"] + " (" + idea_source + ")", r.get("idea", "")),
                (
                    L["target"]
                    + (" (USER INPUT)" if state.get("target_customer_source") == "user_input" else " (AI ASSUMPTION)"),
                    r.get("target_customer", ""),
                ),
                (L["best"] + " (RECOMMENDED ACTION)", r.get("best_first_action", "")),
                (
                    L["testcost"],
                    (
                        f"{_format_money(r.get('estimated_first_test_cost_aed'))} AED (AI ESTIMATE)"
                        if r.get("estimated_first_test_cost_aed") not in (None, "")
                        else "-"
                    ),
                ),
                (L["notstart"], r.get("what_not_to_start_with", "")),
                (L["risk"] + " (AI ASSUMPTION)", r.get("main_risk", "")),
                (L["channel"], r.get("first_customer_channel", "")),
                (L["next"] + " (RECOMMENDED ACTION)", r.get("next_step", "")),
                (
                    "أدلة العملاء" if ar else "CUSTOMER EVIDENCE",
                    (p.get("idea_overview") or {}).get("evidence") or L["pm_none"],
                ),
            ]
        )
    )
    E.append(
        kv(
            [
                (
                    "تكلفة المسار المقدرة" if ar else "Estimated setup / test-path cost",
                    (
                        f"{_format_money(p['total_estimated_cost_aed'])} AED (AI ESTIMATE)"
                        if p["total_estimated_cost_aed"] is not None
                        else ("لم تُقدّر بعد" if ar else "Not estimated yet")
                    ),
                ),
                (
                    "الفجوة المقدرة" if ar else "Estimated gap",
                    (
                        f"{_format_money(p['estimated_budget_gap_aed'])} AED"
                        if p["estimated_budget_gap_aed"] is not None
                        else ("غير متاحة" if ar else "Not available")
                    ),
                ),
            ]
        )
    )
    dns = p.get("do_not_start_with", []) or []
    ins = p.get("instead_do", []) or []
    if dns:
        E.append(Spacer(1, 8))
        E.append(Paragraph(tx(L["donot"]), h2))
        for x in dns:
            E.append(Paragraph(tx(f"\u2717 {x}"), body))
    if ins:
        E.append(Spacer(1, 6))
        E.append(Paragraph(tx(L["instead"]), h2))
        for x in ins:
            E.append(Paragraph(tx(f"\u2713 {x}"), body))
    E.append(Paragraph(tx(L["res"]), h2))
    region = p.get("_region", "")
    authority = (
        (
            "تم / دائرة التنمية الاقتصادية في أبوظبي (ADDED)"
            if ar
            else "TAMM / Abu Dhabi Department of Economic Development (ADDED)"
        )
        if region in ("Abu Dhabi", "Al Ain")
        else ("الجهة الإماراتية المختصة" if ar else "Relevant UAE authority")
    )
    for nm in [
        (
            "معلومات الأعمال لدى حكومة الإمارات - u.ae/en/information-and-services/business"
            if ar
            else "UAE Government business information - u.ae/en/information-and-services/business"
        ),
        authority,
    ]:
        E.append(Paragraph(tx(f"• {nm}"), body))
    E.append(Paragraph(tx(L["note"]), small))
    E.append(Spacer(1, 10))

    # ---- PAGE 5: FULLER PATH ----
    E.append(Paragraph(tx(L["fuller"]), h2))
    setup_value = p.get("total_estimated_cost_aed")
    setup_text = (
        f"{_format_money(setup_value)} AED (AI ESTIMATE)"
        if setup_value is not None
        else ("لم تُقدّر بعد" if ar else "Not estimated yet")
    )
    E.append(
        Paragraph(
            tx(f"{('تكلفة الإعداد المقترحة (تقدير)' if ar else 'Suggested setup cost (estimate)')}: {setup_text}"), body
        )
    )
    days = _int(p.get("total_timeline_days"))
    E.append(
        Paragraph(
            tx(
                f"{L['timeline']}: {days} {('يوم' if days == 1 else 'أيام') if ar else ('day' if days == 1 else 'days')} ("
                + ("تقدير تخطيطي" if ar else "planning estimate")
                + ")"
            ),
            body,
        )
    )
    gap_value = p["estimated_budget_gap_aed"]
    gap_text = f"{_format_money(gap_value)} AED" if gap_value is not None else ("غير متاحة" if ar else "Not available")
    E.append(Paragraph(tx(f"{('الفجوة المقدرة' if ar else 'Estimated gap')}: {gap_text}"), body))
    if gap_value is not None and gap_value > 0:
        E.append(
            Paragraph(
                tx("تحقق من الطلب قبل زيادة إنفاقك." if ar else "Validate demand before increasing your spending."),
                body,
            )
        )
    E.append(
        Paragraph(
            tx(
                "تقدير تخطيطي — تحقق من التكاليف والمتطلبات قبل الإنفاق."
                if ar
                else "Planning estimate — verify costs and requirements before spending."
            ),
            small,
        )
    )
    if setup_value is None:
        E.append(
            Paragraph(
                tx(
                    "التكاليف غير متاحة لأن تقديراً واحداً أو أكثر للخطوات مفقود. احصل على عروض أسعار مناسبة قبل وضع ميزانية التنفيذ."
                    if ar
                    else "Costs are unavailable because one or more step estimates are missing. Obtain relevant quotes before setting an execution budget."
                ),
                small,
            )
        )
    E.append(Spacer(1, 6))
    try:
        c1, c2 = make_steps_charts(p.get("steps", []), ar)
        imgs = Table([[Image(c1, width=80 * mm, height=52 * mm), Image(c2, width=80 * mm, height=52 * mm)]])
        imgs.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        E.append(imgs)
        E.append(Spacer(1, 8))
    except Exception as e:
        logger.error("Steps charts failed: %s", type(e).__name__)
    srows = [
        [
            Paragraph(tx("#"), table_head),
            Paragraph(tx(L["action"]), table_head),
            Paragraph(tx("AED · AI ESTIMATE"), table_head),
            Paragraph(tx(L["day"]), table_head),
        ]
    ]
    for s in p.get("steps", []):
        srows.append(
            [
                Paragraph(tx(s.get("step_number", "")), small),
                Paragraph(f'<b>{tx(s.get("action",""))}</b><br/>{tx(s.get("description",""))}', small),
                Paragraph(
                    (
                        _format_money(s.get("estimated_cost_aed"))
                        if s.get("estimated_cost_aed") is not None
                        else tx("غير مقدرة" if ar else "Not estimated")
                    ),
                    small,
                ),
                Paragraph(tx(s.get("timeline_days", "")), small),
            ]
        )
    if ar:
        srows = [list(reversed(r0)) for r0 in srows]
    st = Table(
        srows,
        colWidths=([14 * mm, 22 * mm, None, 10 * mm] if ar else [10 * mm, None, 22 * mm, 14 * mm]),
        repeatRows=1,
        rowSplitRange=(2, -1),
    )
    st.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    E.append(st)

    if isinstance(p.get("_financial_inputs"), dict):
        from financial_report import finance_flowables

        E.append(PageBreak())
        E.extend(finance_flowables(p["_financial_inputs"], lang))
    doc.build(E)
    buf.seek(0)
    return buf
