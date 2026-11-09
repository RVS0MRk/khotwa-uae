"""Financial PDF flowables. All figures are recalculated from user assumptions."""

import io
from pathlib import Path
from html import escape
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from finance import analyze, calculate
from content_safety import export_plan
from decimal import Decimal, ROUND_HALF_UP

LABELS = {
    "startup_capital": ("Startup capital required", "رأس المال المطلوب"),
    "available_capital": ("Available funds", "الأموال المتاحة"),
    "funding_gap": ("Funding position", "وضع التمويل"),
    "one_time_costs": ("One-time expenses", "مصروفات التأسيس"),
    "working_capital": ("Working-capital buffer", "احتياطي رأس المال العامل"),
    "contingency_reserve": ("Contingency reserve", "احتياطي الطوارئ"),
    "revenue": ("Monthly revenue", "الإيراد الشهري"),
    "variable_expenses": ("Monthly variable expenses", "المصروفات المتغيرة الشهرية"),
    "fixed_expenses": ("Monthly fixed expenses", "المصروفات الثابتة الشهرية"),
    "operating_profit": ("Monthly operating profit / loss", "الربح أو الخسارة التشغيلية"),
    "contribution_per_unit": ("Contribution per unit", "مساهمة الوحدة"),
    "contribution_ratio": ("Contribution margin ratio", "نسبة هامش المساهمة"),
    "gross_profit": ("Gross profit (COGS basis)", "مجمل الربح وفق تكلفة البضاعة"),
    "gross_margin": ("Gross margin", "نسبة مجمل الربح"),
    "break_even_units": ("Minimum whole break-even units", "أقل وحدات كاملة للتعادل"),
    "break_even_continuous_units": ("Continuous mathematical break-even units", "وحدات التعادل الرياضية"),
    "break_even_revenue": ("Whole-unit break-even revenue", "إيراد التعادل بوحدات كاملة"),
    "operating_cash": ("Operating cash after initial spend and reserve", "السيولة بعد الإنفاق الأولي والاحتياطي"),
    "monthly_cash_flow": ("Monthly net cash flow", "صافي التدفق النقدي الشهري"),
    "payback_months": ("Simple payback estimate (months)", "تقدير الاسترداد البسيط (شهر)"),
    "runway_months": ("Cash runway (months)", "المدة النقدية (شهر)"),
}


def text_style(lang):
    ar = lang == "ar"
    if ar and "KhotwaAmiri" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("KhotwaAmiri", str(Path(__file__).parent / "fonts/Amiri-Regular.ttf")))
    style = ParagraphStyle(
        "investment",
        fontName="KhotwaAmiri" if ar else "Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#18372f"),
        alignment=TA_RIGHT if ar else TA_LEFT,
        spaceAfter=4,
    )

    def tx(value):
        text = str(value) if value not in (None, "") else ("لم يُقدّم بعد" if ar else "Not yet provided")
        text = text.replace("−", "-").replace("×", "x").replace("÷", "/")
        return escape(get_display(arabic_reshaper.reshape(text)) if ar else text)

    return style, tx


def format_value(key, value, lang="en"):
    """Presentation never changes a calculation or converts unknown to zero."""
    if value is None:
        return "غير معلوم" if lang == "ar" else "Unknown"
    n = Decimal(str(value))
    if n == 0:
        n = abs(n)
    if key in ("contribution_ratio", "gross_margin"):
        return f"{n * 100:,.2f}".rstrip("0").rstrip(".") + "%"
    if key in ("break_even_units", "units"):
        return f"{n:,.0f}" + (" وحدة" if lang == "ar" else " units")
    if key in ("runway_months", "payback_months", "break_even_continuous_units"):
        return f"{abs(n) if n == 0 else n:,.2f}"
    rounded = n.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{abs(rounded) if rounded == 0 else rounded:,.2f} AED"


def result_value(key, r, lang):
    ar = lang == "ar"
    if key == "funding_gap" and r.get(key) is not None:
        gap = Decimal(r[key])
        label = ("عجز " if gap > 0 else "فائض ") if ar else ("Shortfall " if gap > 0 else "Surplus ")
        return label + format_value(key, abs(gap), lang)
    if key == "break_even_units" and r["break_even_status"] == "unreachable":
        return "التعادل غير قابل للوصول" if ar else "Break-even not reachable"
    if key == "runway_months":
        if r["runway_status"] == "no_burn":
            return "لا يوجد استنزاف نقدي شهري حالياً" if ar else "No current monthly cash burn"
        if r["runway_status"] == "underfunded":
            return "الإنفاق الأولي غير ممول بالكامل" if ar else "Initial spending underfunded"
    if key == "payback_months" and r["payback_status"] == "no_positive_benefit":
        return "لا توجد منفعة نقدية موجبة" if ar else "No positive net cash benefit"
    return format_value(key, r.get(key), lang)


def finance_flowables(inputs, lang="en"):
    r = calculate(inputs)
    style, tx = text_style(lang)
    ar = lang == "ar"
    heading = ParagraphStyle(
        "section", parent=style, fontSize=17, leading=24, spaceBefore=12, spaceAfter=12, keepWithNext=True
    )
    out = [
        Paragraph(tx("النتائج المالية · افتراضات المستخدم" if ar else "Financial results · user assumptions"), heading)
    ]
    rows = [[Paragraph(tx(x), style) for x in (("الحساب", "النتيجة") if ar else ("Calculation", "Result"))]]
    for key, labels in LABELS.items():
        rows.append([Paragraph(tx(labels[1 if ar else 0]), style), Paragraph(tx(result_value(key, r, lang)), style)])
    if ar:
        rows = [list(reversed(row)) for row in rows]
    table = Table(rows, colWidths=[235, 235], hAlign="CENTER", repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f2ec")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8ded5")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    out.append(table)
    basis = r["cash_flow_basis"]
    basis_text = {
        "entered_cash_flow": (
            "Cash basis: separately entered receipts and payments.",
            "الأساس النقدي: المقبوضات والمدفوعات المدخلة بشكل مستقل.",
        ),
        "simplified_user_assumption": (
            "Cash basis: user-selected simplified estimate; revenue collected and variable plus fixed expenses paid in the same month.",
            "الأساس النقدي: تقدير مبسط اختاره المستخدم لتحصيل الإيراد وسداد المتغيرة والثابتة في الشهر نفسه.",
        ),
        "missing_information": (
            "Cash basis: unavailable due to missing information.",
            "الأساس النقدي: غير متاح لنقص المعلومات.",
        ),
    }[basis]
    explanations = [
        basis_text,
        (
            "Payback = one-time spending / positive monthly net cash benefit. Held cash buffers are excluded. Constant-cash estimate; excludes changing cash flows and time value of money.",
            "الاسترداد = مصروفات التأسيس ÷ المنفعة النقدية الشهرية الموجبة دون الاحتياطيات النقدية. تقدير ثابت دون تغير التدفقات أو القيمة الزمنية للنقود.",
        ),
        (
            "Revenue = units x price. Operating profit = revenue - variable expenses - fixed expenses. Gross profit uses separately entered COGS.",
            "الإيراد = الوحدات × السعر. الربح التشغيلي = الإيراد − المتغيرة − الثابتة. مجمل الربح يستخدم تكلفة البضاعة المدخلة.",
        ),
        (
            "Whole break-even units round upward. Capital = one-time spending + working capital + contingency; cash buffers are not deducted twice.",
            "تُقرّب وحدات التعادل لأعلى. رأس المال = التأسيس + رأس المال العامل + الطوارئ دون خصم الاحتياطيات مرتين.",
        ),
        (
            "These are mathematical illustrations, not forecasts or proof of viability. Recorded evidence is user-reported, not independently verified.",
            "هذه أمثلة حسابية وليست توقعات أو إثباتاً للجدوى. الأدلة المسجلة إقرار من المستخدم دون تحقق مستقل.",
        ),
    ]
    if "licensing_not_provided" in r["warnings"]:
        explanations.insert(
            0,
            (
                "Licensing not provided: capital is the known subtotal excluding unprovided licensing. Existing records retain their subtotal. Do not duplicate licensing within Other costs.",
                "لم يُدخل الترخيص: رأس المال مجموع جزئي يستثني الترخيص غير المقدم. تحتفظ السجلات القديمة بمجموعها. لا تكرر الترخيص ضمن التكاليف الأخرى.",
            ),
        )
    if "cogs_exceeds_variable" in r["warnings"]:
        explanations.insert(
            0,
            (
                "Inconsistent COGS subset exceeds variable costs. Gross profit and margin withheld until corrected.",
                "تكلفة البضاعة المختارة جزءاً من المتغيرة تتجاوزها. حُجب مجمل الربح والهامش حتى التصحيح.",
            ),
        )
    out.append(Spacer(1, 12))
    out.extend(
        Paragraph(tx(sentence.strip() + "."), style)
        for pair in explanations
        for sentence in pair[1 if ar else 0].split(".")
        if sentence.strip()
    )
    return out


def build_investment_report(payload, lang="en"):
    result = analyze(payload.get("finance", {}))
    p = export_plan(payload.get("plan", {}))
    notes = payload.get("notes", {})
    style, tx = text_style(lang)
    ar = lang == "ar"
    heading = ParagraphStyle(
        "investment-heading", parent=style, fontSize=24, leading=32, spaceAfter=20, keepWithNext=True
    )
    output = [Paragraph(tx("خطوة | ملخص الاستثمار" if ar else "Khotwa | Investment brief"), heading)]
    state = p.get("state") or {}
    overview = p.get("idea_overview") or {}
    fields = [
        ("Business idea", "فكرة المشروع", state.get("idea")),
        ("Problem hypothesis", "فرضية المشكلة", overview.get("problem")),
        ("Proposed solution", "الحل المقترح", overview.get("solution")),
        ("Target customer", "العميل المستهدف", state.get("target_customer")),
        (
            "Market assumption",
            "افتراض السوق",
            (
                {"Abu Dhabi": "أبوظبي", "Dubai": "دبي", "Sharjah": "الشارقة", "UAE-wide": "الإمارات"}.get(
                    state.get("region"), state.get("region")
                )
                if ar
                else state.get("region")
            ),
        ),
        ("Business model / pricing unit", "نموذج العمل ووحدة السعر", notes.get("model")),
        ("Competitive differentiation", "التميّز التنافسي", notes.get("differentiation")),
        ("Use of funding", "استخدام التمويل", notes.get("use_of_funds")),
        (
            "Recorded customer entries (user-reported)",
            "إدخالات العملاء المسجّلة بإقرار المستخدم",
            (p.get("proof_summary") or {}).get("total_responses", 0),
        ),
        (
            "Funding request (user input, AED)",
            "طلب التمويل بإدخال المستخدم (درهم)",
            format_value("funding_request", result["base"]["inputs"].get("funding_request"), lang),
        ),
        ("Key risk hypothesis", "فرضية الخطر الرئيسي", (p.get("readiness_report") or {}).get("main_risk")),
        ("Next milestone", "المرحلة التالية", p.get("first_step_today")),
    ]
    missing = []
    for en, arabic, value in fields:
        if value in (None, "", "Unknown", "غير معلوم"):
            missing.append(arabic if ar else en)
            continue
        output += [
            Paragraph(
                tx(arabic if ar else en),
                ParagraphStyle("label", parent=style, textColor=colors.HexColor("#17634e"), keepWithNext=True),
            ),
            Paragraph(tx(str(value)[:1200]), style),
        ]
    if missing:
        output.append(Paragraph(tx(("لم يُقدّم بعد: " if ar else "Not yet provided: ") + ", ".join(missing)), style))
    output += [PageBreak()] + finance_flowables(result["base"]["inputs"], lang)
    output += [
        Spacer(1, 20),
        Paragraph(tx("السيناريوهات · افتراضات قابلة للتعديل" if ar else "Scenarios · editable assumptions"), heading),
    ]
    names = [
        ("conservative", "متحفّظ" if ar else "Conservative"),
        ("base", "أساسي" if ar else "Base case"),
        ("optimistic", "متفائل" if ar else "Optimistic"),
    ]
    rows = [[Paragraph(tx("البند" if ar else "Measure"), style)] + [Paragraph(tx(label), style) for _, label in names]]
    for metric in (
        "revenue",
        "operating_profit",
        "startup_capital",
        "funding_gap",
        "break_even_units",
        "runway_months",
    ):
        rows.append(
            [Paragraph(tx(LABELS[metric][1 if ar else 0]), style)]
            + [Paragraph(tx(result_value(metric, result["scenarios"][key], lang)), style) for key, _ in names]
        )
    if ar:
        rows = [list(reversed(row)) for row in rows]
    table = Table(rows, colWidths=([105, 105, 105, 155] if ar else [155, 105, 105, 105]), repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f2ec")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8ded5")),
            ]
        )
    )
    output.append(table)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=55, bottomMargin=50, title="Khotwa Investment Brief"
    )

    def page(canvas, document):
        canvas.setFont("KhotwaAmiri" if ar else "Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#556760"))
        footer = "خطوة | افتراضات المستخدم | AED" if ar else "Khotwa | User assumptions | AED"
        if ar:
            canvas.drawRightString(A4[0] - 50, 25, get_display(arabic_reshaper.reshape(footer)))
            canvas.drawString(50, 25, str(document.page))
        else:
            canvas.drawString(50, 25, footer)
            canvas.drawRightString(A4[0] - 50, 25, str(document.page))

    doc.build(output, onFirstPage=page, onLaterPages=page)
    buf.seek(0)
    return buf
