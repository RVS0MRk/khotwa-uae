"""Pure AED arithmetic. Inputs/outputs use decimal strings; no AI or persistence.

Money is rounded to fils with ROUND_HALF_UP at the input and reporting boundaries.
Intermediate arithmetic remains Decimal. Ratios use four decimal places; runway
uses two. Working capital is a cash buffer, never an extra expense in cash burn.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING, localcontext

MONEY = Decimal("0.01")
MAXIMUM = Decimal("1000000000000")
FIELDS = (
    "equipment",
    "initial_software",
    "initial_marketing",
    "other_startup",
    "licensing",
    "working_capital",
    "contingency",
    "available_capital",
    "price",
    "units",
    "variable_cost",
    "fixed_cost",
    "cogs_per_unit",
    "cash_collections",
    "cash_operating_outflow",
    "funding_request",
)
ONE_TIME = ("equipment", "initial_software", "initial_marketing", "other_startup")


class FinanceInputError(ValueError):
    def __init__(self, field):
        super().__init__(f"Invalid financial input: {field}")
        self.field = field


def parse_inputs(raw):
    if not isinstance(raw, dict) or set(raw) - set(FIELDS) - {"contingency_mode", "cash_mode", "cogs_basis"}:
        raise FinanceInputError("inputs")
    values = {}
    for key in FIELDS:
        value = raw.get(key)
        if value is None or value == "":
            values[key] = None
            continue
        if isinstance(value, bool) or not isinstance(value, (str, int, float)) or len(str(value)) > 40:
            raise FinanceInputError(key)
        try:
            number = Decimal(str(value))
            if not number.is_finite() or number < 0 or number > MAXIMUM:
                raise FinanceInputError(key)
            if key == "units" and number != number.to_integral_value():
                raise FinanceInputError(key)
            rounded = number if key == "units" else number.quantize(MONEY, rounding=ROUND_HALF_UP)
            values[key] = abs(rounded) if rounded == 0 else rounded
        except (InvalidOperation, ValueError):
            raise FinanceInputError(key) from None
    values["contingency_mode"] = raw.get("contingency_mode", "aed")
    if values["contingency_mode"] not in ("aed", "percent") or (
        values["contingency_mode"] == "percent" and (values["contingency"] or 0) > 100
    ):
        raise FinanceInputError("contingency")
    for key, default, choices in (
        ("cash_mode", "entered", ("entered", "simplified")),
        ("cogs_basis", "separate", ("separate", "subset_of_variable")),
    ):
        values[key] = raw.get(key, default)
        if values[key] not in choices:
            raise FinanceInputError(key)
    return values


def _sum(values):
    return None if any(v is None for v in values) else sum(values, Decimal(0))


def _display(value, places=MONEY):
    if value is None:
        return None
    rounded = value.quantize(places, rounding=ROUND_HALF_UP)
    return str(abs(rounded) if rounded == 0 else rounded)


def calculate(raw):
    v = parse_inputs(raw)
    with localcontext() as ctx:
        ctx.prec = 50
        one_time = _sum([v[k] for k in ONE_TIME])
        # New optional category: older records keep their known subtotal. The
        # result explicitly flags unprovided licensing, rather than claiming 0.
        if one_time is not None and v["licensing"] is not None:
            one_time += v["licensing"]
        contingency = v["contingency"]
        if v["contingency_mode"] == "percent":
            contingency = (
                (one_time * contingency / 100).quantize(MONEY, rounding=ROUND_HALF_UP)
                if one_time is not None and contingency is not None
                else None
            )
        capital = _sum([one_time, v["working_capital"], contingency])
        gap = capital - v["available_capital"] if capital is not None and v["available_capital"] is not None else None
        revenue = v["price"] * v["units"] if v["price"] is not None and v["units"] is not None else None
        variable = (
            v["variable_cost"] * v["units"] if v["variable_cost"] is not None and v["units"] is not None else None
        )
        contribution = (
            v["price"] - v["variable_cost"] if v["price"] is not None and v["variable_cost"] is not None else None
        )
        ratio = contribution / v["price"] if contribution is not None and v["price"] else None
        profit = revenue - variable - v["fixed_cost"] if None not in (revenue, variable, v["fixed_cost"]) else None
        cogs = v["cogs_per_unit"] * v["units"] if None not in (v["cogs_per_unit"], v["units"]) else None
        inconsistent_cogs = (
            v["cogs_basis"] == "subset_of_variable"
            and None not in (v["cogs_per_unit"], v["variable_cost"])
            and v["cogs_per_unit"] > v["variable_cost"]
        )
        if inconsistent_cogs:
            cogs = None
        gross = revenue - cogs if None not in (revenue, cogs) else None
        gross_ratio = gross / revenue if gross is not None and revenue else None
        continuous = whole = breakeven_revenue = None
        break_status = "unknown"
        if contribution == 0 and v["fixed_cost"] == 0:
            continuous, whole, breakeven_revenue = Decimal(0), 0, Decimal(0)
            break_status = "at_break_even"
        elif contribution is not None and contribution <= 0:
            break_status = "unreachable"
        elif contribution is not None and v["fixed_cost"] is not None:
            continuous = v["fixed_cost"] / contribution
            whole = int(continuous.to_integral_value(rounding=ROUND_CEILING))
            breakeven_revenue = Decimal(whole) * v["price"]
            break_status = "reachable"
        operating_cash = (
            v["available_capital"] - one_time - contingency
            if None not in (v["available_capital"], one_time, contingency)
            else None
        )
        collections, payments = v["cash_collections"], v["cash_operating_outflow"]
        if v["cash_mode"] == "simplified":
            collections, payments = revenue, _sum([variable, v["fixed_cost"]])
        cash_flow = collections - payments if None not in (collections, payments) else None
        cash_basis = (
            ("simplified_user_assumption" if v["cash_mode"] == "simplified" else "entered_cash_flow")
            if cash_flow is not None
            else "missing_information"
        )
        payback = one_time / cash_flow if one_time is not None and cash_flow is not None and cash_flow > 0 else None
        payback_status = (
            "estimated"
            if payback is not None
            else "no_positive_benefit" if cash_flow is not None and cash_flow <= 0 else "unknown"
        )
        runway = None
        runway_status = "unknown"
        if cash_flow is not None and operating_cash is not None:
            if operating_cash < 0:
                runway_status = "underfunded"
            elif cash_flow >= 0:
                runway_status = "no_burn"
            else:
                runway_status = "burning"
                runway = operating_cash / -cash_flow
        result = {
            "revenue": revenue,
            "variable_expenses": variable,
            "fixed_expenses": v["fixed_cost"],
            "operating_profit": profit,
            "contribution_per_unit": contribution,
            "contribution_ratio": ratio,
            "cogs": cogs,
            "gross_profit": gross,
            "gross_margin": gross_ratio,
            "one_time_costs": one_time,
            "working_capital": v["working_capital"],
            "contingency_reserve": contingency,
            "startup_capital": capital,
            "available_capital": v["available_capital"],
            "funding_gap": gap,
            "operating_cash": operating_cash,
            "monthly_cash_flow": cash_flow,
            "runway_months": runway,
            "payback_months": payback,
            "effective_cash_collections": collections,
            "effective_cash_payments": payments,
            "break_even_continuous_units": continuous,
            "break_even_revenue": breakeven_revenue,
        }
        result = {
            k: _display(
                value,
                (
                    Decimal("0.0001")
                    if k in ("contribution_ratio", "gross_margin", "break_even_continuous_units")
                    else MONEY
                ),
            )
            for k, value in result.items()
        }
        rounded_fields = [k for k in FIELDS if k != "units" and v[k] is not None and Decimal(str(raw[k])) != v[k]]
        result.update(
            rounded_fields=rounded_fields,
            break_even_units=whole,
            break_even_status=break_status,
            runway_status=runway_status,
            cash_flow_basis=cash_basis,
            payback_status=payback_status,
            warnings=(["licensing_not_provided"] if v["licensing"] is None else [])
            + (["cogs_exceeds_variable"] if inconsistent_cogs else [])
            + ["rounded_input:" + k for k in rounded_fields],
            missing=[k for k in FIELDS if v[k] is None],
            currency="AED",
            source="user_assumptions",
            rounding="Money: nearest fil, ROUND_HALF_UP. Ratios: 4 decimals. Whole units: ceiling.",
            inputs={
                k: str(int(val)) if k == "units" and val is not None else str(val) if isinstance(val, Decimal) else val
                for k, val in v.items()
            },
        )
        return result


def analyze(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("inputs", {}), dict):
        raise FinanceInputError("inputs")
    base = payload.get("inputs", {})
    result = {"base": calculate(base), "scenarios": {}, "sensitivity": []}
    scenarios = payload.get("scenarios", {})
    if not isinstance(scenarios, dict) or set(scenarios) - {"conservative", "base", "optimistic"}:
        raise FinanceInputError("scenarios")
    defaults = scenario_inputs(base)
    for name in ("conservative", "base", "optimistic"):
        result["scenarios"][name] = calculate(scenarios.get(name, defaults[name]))
    baseline_profit = result["base"]["operating_profit"]
    impacts = {}
    for field in ("units", "price", "variable_cost", "fixed_cost"):
        baseline = parse_inputs(base)[field]
        if baseline is None:
            continue
        for percent in (-10, 10):
            altered = dict(base)
            comparison = (
                discrete_units(baseline, percent)
                if field == "units"
                else baseline * (Decimal(1) + Decimal(percent) / 100)
            )
            altered[field] = str(comparison)
            calculated = calculate(altered)
            # Report the actual rounded input used by the engine, including
            # cent-sized price/cost changes that round back to the baseline.
            comparison = Decimal(calculated["inputs"][field])
            impact = (
                Decimal(calculated["operating_profit"]) - Decimal(baseline_profit)
                if baseline_profit is not None and calculated["operating_profit"] is not None
                else None
            )
            actual_percent = (comparison - baseline) / baseline * 100 if baseline else None
            entry = {
                "field": field,
                "percent": percent,
                "baseline": str(baseline),
                "comparison": str(comparison),
                "actual_percent": _display(actual_percent),
                "discrete": field == "units",
                "profit_impact": _display(impact),
                "result": calculated,
            }
            result["sensitivity"].append(entry)
            if impact is not None:
                impacts[field] = max(impacts.get(field, Decimal(0)), abs(impact))
    result["sensitivity"].sort(
        key=lambda e: abs(Decimal(e["profit_impact"])) if e["profit_impact"] is not None else Decimal(-1), reverse=True
    )
    largest = max(impacts.values(), default=Decimal(0))
    result["sensitivity_leaders"] = (
        [field for field, value in impacts.items() if value == largest] if largest > 0 else []
    )
    stages = payload.get("allocations", [None] * 6)
    if not isinstance(stages, list) or len(stages) != 6:
        raise FinanceInputError("allocations")
    amounts = [parse_inputs({"available_capital": amount})["available_capital"] for amount in stages]
    allocation = _sum(amounts)
    capital = parse_inputs(base)["available_capital"]
    result["allocation"] = {
        "total": _display(allocation),
        "known_total": _display(sum((a for a in amounts if a is not None), Decimal(0))),
        "over_budget": capital is not None and sum((a for a in amounts if a is not None), Decimal(0)) > capital,
        "remaining": (
            _display(capital - sum((a for a in amounts if a is not None), Decimal(0))) if capital is not None else None
        ),
        "unallocated_stages": sum(a is None for a in amounts),
    }
    return result


def discrete_units(baseline, percent):
    """A non-zero operational change, labelled with its real percentage in output."""
    changed = (baseline * (Decimal(1) + Decimal(percent) / 100)).to_integral_value(rounding=ROUND_HALF_UP)
    if changed == baseline:
        changed = max(Decimal(0), baseline + (1 if percent > 0 else -1))
    return changed


def scenario_inputs(raw):
    parsed = parse_inputs(raw)
    scenarios = {}
    for name, percent in (("conservative", -20), ("base", 0), ("optimistic", 20)):
        inputs = dict(raw)
        if percent and parsed["units"] is not None:
            inputs["units"] = str(discrete_units(parsed["units"], percent))
        scenarios[name] = inputs
    return scenarios
