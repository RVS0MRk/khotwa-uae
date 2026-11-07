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

LABELS = {
    "startup_capital": ("Startup capital required", "رأس المال المطلوب"),
    "available_capital": ("Available funds", "الأموال المتاحة"),
    "funding_gap": ("Funding gap (negative = surplus)", "فجوة التمويل (السالب فائض)"),
    "one_time_costs": ("One-time expenses", "مصروفات التأسيس"),
    "working_capital": ("Working-capital buffer", "احتياطي رأس المال العامل"),
    "contingency_reserve": ("Contingency reserve", "احتياطي الطوارئ"),
    "revenue": ("Monthly revenue", "الإيراد الشهري"),
    "variable_expenses": ("Monthly variable expenses", "المصروفات المتغيرة الشهرية"),
    "fixed_expenses": ("Monthly fixed expenses", "المصروفات الثابتة الشهرية"),
    "operating_profit": ("Monthly operating profit / loss", "الربح أو الخسارة التشغيلية"),
    "contribution_per_unit": ("Contribution per unit", "مساهمة الوحدة"),
    "contribution_ratio": ("Contribution ratio (fraction)", "نسبة المساهمة (كسر عشري)"),
    "gross_profit": ("Gross profit (COGS basis)", "مجمل الربح وفق تكلفة البضاعة"),
    "gross_margin": ("Gross margin (fraction)", "نسبة مجمل الربح (كسر عشري)"),
    "break_even_units": ("Minimum whole break-even units", "أقل وحدات كاملة للتعادل"),
    "break_even_continuous_units": ("Continuous mathematical break-even units", "وحدات التعادل الرياضية"),
    "break_even_revenue": ("Whole-unit break-even revenue", "إيراد التعادل بوحدات كاملة"),
    "operating_cash": ("Operating cash after initial spend and reserve", "السيولة بعد الإنفاق الأولي والاحتياطي"),
    "monthly_cash_flow": ("Monthly net cash flow", "صافي التدفق النقدي الشهري"),
    "runway_months": ("Cash runway (months)", "المدة النقدية (شهر)"),
}


def text_style(lang):
    ar = lang == "ar"
    if ar and "KhotwaAmiri" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("KhotwaAmiri", str(Path(__file__).parent / "fonts/Amiri-Regular.ttf")))
    style = ParagraphStyle("investment", fontName="KhotwaAmiri" if ar else "Helvetica",
                           fontSize=10, leading=14, textColor=colors.HexColor("#18372f"),
                           alignment=TA_RIGHT if ar else TA_LEFT, spaceAfter=4)
    def tx(value):
        text = str(value) if value not in (None, "") else ("لم يُقدّم بعد" if ar else "Not yet provided")
        text = text.replace("−", "-").replace("×", "x").replace("÷", "/")
        return escape(get_display(arabic_reshaper.reshape(text)) if ar else text)
    return style, tx


def finance_flowables(inputs, lang="en"):
    r = calculate(inputs)
    style, tx = text_style(lang)
    ar = lang == "ar"
    out = [Paragraph(tx("ملخص الاستثمار · افتراضات المستخدم · درهم" if ar else "Investment summary · USER ASSUMPTIONS · AED"), style)]
    rows = []
    for key, labels in LABELS.items():
        value = r.get(key)
        if key == "break_even_units" and r["break_even_status"] == "unreachable":
            value = "لا يمكن الوصول إلى التعادل وفق الافتراضات الحالية" if ar else "Break-even not reachable under current assumptions"
        if key == "runway_months" and r["runway_status"] == "no_burn":
            value = "لا يوجد استنزاف نقدي شهري حالياً" if ar else "No current monthly cash burn"
        if key == "runway_months" and r["runway_status"] == "underfunded":
            value = "الإنفاق الأولي غير ممول بالكامل" if ar else "Initial spending is underfunded"
        row = [Paragraph(tx(labels[1 if ar else 0]), style), Paragraph(tx(value), style)]
        rows.append(list(reversed(row)) if ar else row)
    table = Table(rows, colWidths=[235, 235], hAlign="CENTER")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#d8ded5")), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    out.append(table)
    explanations = [
        ("Revenue = units × price. Operating profit = revenue − all variable costs − fixed costs. Contribution = price − variable cost per unit. Gross profit uses the separately entered accounting cost of goods sold.", "الإيراد = الوحدات × السعر. الربح التشغيلي = الإيراد − كل التكاليف المتغيرة − الثابتة. المساهمة = السعر − التكلفة المتغيرة للوحدة. مجمل الربح يستخدم تكلفة البضاعة المحاسبية المدخلة بشكل مستقل."),
        ("Break-even whole units round upward: fixed costs ÷ contribution per unit. Capital = one-time costs + working-capital buffer + contingency. Percentage contingency applies only to one-time expenses.", "تُقرّب وحدات التعادل لأعلى: الثابتة ÷ مساهمة الوحدة. رأس المال = التأسيس + رأس المال العامل + الطوارئ. تُحسب نسبة الطوارئ من التأسيس فقط."),
        ("Cash runway uses cash collections and payments, not accounting profit. The working-capital buffer is not deducted twice. Unknown values stay unknown. Money rounds to fils using ROUND_HALF_UP; ratios use four decimal places.", "تعتمد المدة النقدية على المقبوضات والمدفوعات لا الربح المحاسبي. لا يُخصم رأس المال العامل مرتين. تبقى القيم المجهولة مجهولة. تُقرّب النقود إلى الفلس ونسب الهوامش إلى أربع منازل."),
        ("These are mathematical illustrations, not forecasts or proof of viability. User-recorded evidence is not independently verified.", "هذه أمثلة حسابية وليست توقعات أو إثباتاً للجدوى. الأدلة المسجّلة من المستخدم لم تُتحقق مستقلاً.")]
    # Keep explanatory sentences separate so shaped Arabic never wraps from
    # the wrong visual end in ReportLab installations without optional rlbidi.
    out.extend(Paragraph(tx(sentence.strip() + "."), style) for pair in explanations
               for sentence in pair[1 if ar else 0].split(".") if sentence.strip())
    return out


def build_investment_report(payload, lang="en"):
    result = analyze(payload.get("finance", {}))
    p = payload.get("plan", {})
    notes = payload.get("notes", {})
    style, tx = text_style(lang)
    ar = lang == "ar"
    heading = ParagraphStyle("investment-heading", parent=style, fontSize=24, leading=32, spaceAfter=20, keepWithNext=True)
    output = [Paragraph(tx("خطوة | ملخص الاستثمار" if ar else "Khotwa | Investment brief"), heading)]
    state = p.get("state") or {}
    overview = p.get("idea_overview") or {}
    fields = [("Business idea", "فكرة المشروع", state.get("idea")), ("Problem hypothesis", "فرضية المشكلة", overview.get("problem")),
              ("Proposed solution", "الحل المقترح", overview.get("solution")), ("Target customer", "العميل المستهدف", state.get("target_customer")),
              ("Market assumption", "افتراض السوق", state.get("region")), ("Business model / pricing unit", "نموذج العمل ووحدة السعر", notes.get("model")),
              ("Competitive differentiation", "التميّز التنافسي", notes.get("differentiation")), ("Use of funding", "استخدام التمويل", notes.get("use_of_funds")),
              ("Recorded customer entries (user-reported)", "إدخالات العملاء المسجّلة بإقرار المستخدم", (p.get("proof_summary") or {}).get("total_responses", 0)),
              ("Funding request (user input, AED)", "طلب التمويل بإدخال المستخدم (درهم)", result["base"]["inputs"].get("funding_request")),
              ("Key risk hypothesis", "فرضية الخطر الرئيسي", (p.get("readiness_report") or {}).get("main_risk")),
              ("Next milestone", "المرحلة التالية", p.get("first_step_today"))]
    for en, arabic, value in fields:
        output += [Paragraph(tx(arabic if ar else en), ParagraphStyle("label", parent=style, textColor=colors.HexColor("#17634e"))), Paragraph(tx(str(value)[:1200] if value is not None else None), style)]
    output += [PageBreak()] + finance_flowables(result["base"]["inputs"], lang)
    output += [Spacer(1, 20), Paragraph(tx("السيناريوهات · افتراضات قابلة للتعديل" if ar else "Scenarios · editable assumptions"), heading)]
    names = [("conservative", "متحفّظ" if ar else "Conservative"), ("base", "أساسي" if ar else "Base case"), ("optimistic", "متفائل" if ar else "Optimistic")]
    rows = [[Paragraph(tx("البند" if ar else "Measure"), style)] + [Paragraph(tx(label), style) for _, label in names]]
    for metric in ("revenue", "operating_profit", "startup_capital", "funding_gap", "break_even_units", "runway_months"):
        rows.append([Paragraph(tx(LABELS[metric][1 if ar else 0]), style)] + [Paragraph(tx(result["scenarios"][key][metric]), style) for key, _ in names])
    if ar:
        rows = [list(reversed(row)) for row in rows]
    table = Table(rows, colWidths=([105, 105, 105, 155] if ar else [155, 105, 105, 105]), repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8f2ec")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7), ("LINEBELOW", (0,0), (-1,-1), .4, colors.HexColor("#d8ded5"))]))
    output.append(table)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=55, bottomMargin=50, title="Khotwa Investment Brief")
    def page(canvas, document):
        canvas.setFont("Helvetica", 9); canvas.setFillColor(colors.HexColor("#556760"));canvas.drawString(50, 25, "Khotwa | User assumptions | AED");canvas.drawRightString(A4[0]-50, 25, str(document.page))
    doc.build(output, onFirstPage=page, onLaterPages=page)
    buf.seek(0)
    return buf
