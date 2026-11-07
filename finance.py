"""Pure AED arithmetic. Inputs/outputs use decimal strings; no AI or persistence.

Money is rounded to fils with ROUND_HALF_UP at the input and reporting boundaries.
Intermediate arithmetic remains Decimal. Ratios use four decimal places; runway
uses two. Working capital is a cash buffer, never an extra expense in cash burn.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING, localcontext

MONEY = Decimal("0.01")
MAXIMUM = Decimal("1000000000000")
FIELDS = ("equipment", "initial_software", "initial_marketing", "other_startup",
          "working_capital", "contingency", "available_capital", "price", "units",
          "variable_cost", "fixed_cost", "cogs_per_unit", "cash_collections",
          "cash_operating_outflow", "funding_request")
ONE_TIME = ("equipment", "initial_software", "initial_marketing", "other_startup")


class FinanceInputError(ValueError):
    def __init__(self, field):
        super().__init__(f"Invalid financial input: {field}")
        self.field = field


def parse_inputs(raw):
    if not isinstance(raw, dict) or set(raw) - set(FIELDS) - {"contingency_mode"}:
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
            values[key] = number if key == "units" else number.quantize(MONEY, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            raise FinanceInputError(key) from None
    values["contingency_mode"] = raw.get("contingency_mode", "aed")
    if values["contingency_mode"] not in ("aed", "percent") or (values["contingency_mode"] == "percent" and (values["contingency"] or 0) > 100):
        raise FinanceInputError("contingency")
    return values


def _sum(values):
    return None if any(v is None for v in values) else sum(values, Decimal(0))


def _display(value, places=MONEY):
    return None if value is None else str(value.quantize(places, rounding=ROUND_HALF_UP))


def calculate(raw):
    v = parse_inputs(raw)
    with localcontext() as ctx:
        ctx.prec = 50
        one_time = _sum([v[k] for k in ONE_TIME])
        contingency = v["contingency"]
        if v["contingency_mode"] == "percent":
            contingency = one_time * contingency / 100 if one_time is not None and contingency is not None else None
        capital = _sum([one_time, v["working_capital"], contingency])
        gap = capital - v["available_capital"] if capital is not None and v["available_capital"] is not None else None
        revenue = v["price"] * v["units"] if v["price"] is not None and v["units"] is not None else None
        variable = v["variable_cost"] * v["units"] if v["variable_cost"] is not None and v["units"] is not None else None
        contribution = v["price"] - v["variable_cost"] if v["price"] is not None and v["variable_cost"] is not None else None
        ratio = contribution / v["price"] if contribution is not None and v["price"] else None
        profit = revenue - variable - v["fixed_cost"] if None not in (revenue, variable, v["fixed_cost"]) else None
        cogs = v["cogs_per_unit"] * v["units"] if None not in (v["cogs_per_unit"], v["units"]) else None
        gross = revenue - cogs if None not in (revenue, cogs) else None
        gross_ratio = gross / revenue if gross is not None and revenue else None
        continuous = whole = breakeven_revenue = None
        break_status = "unknown"
        if contribution is not None and contribution <= 0:
            break_status = "unreachable"
        elif contribution is not None and v["fixed_cost"] is not None:
            continuous = v["fixed_cost"] / contribution
            whole = int(continuous.to_integral_value(rounding=ROUND_CEILING))
            breakeven_revenue = Decimal(whole) * v["price"]
            break_status = "reachable"
        operating_cash = v["available_capital"] - one_time - contingency if None not in (v["available_capital"], one_time, contingency) else None
        cash_flow = v["cash_collections"] - v["cash_operating_outflow"] if None not in (v["cash_collections"], v["cash_operating_outflow"]) else None
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
        result = {"revenue": revenue, "variable_expenses": variable, "fixed_expenses": v["fixed_cost"],
                  "operating_profit": profit, "contribution_per_unit": contribution,
                  "contribution_ratio": ratio, "cogs": cogs, "gross_profit": gross, "gross_margin": gross_ratio,
                  "one_time_costs": one_time, "working_capital": v["working_capital"], "contingency_reserve": contingency,
                  "startup_capital": capital, "available_capital": v["available_capital"], "funding_gap": gap,
                  "operating_cash": operating_cash, "monthly_cash_flow": cash_flow, "runway_months": runway,
                  "break_even_continuous_units": continuous, "break_even_revenue": breakeven_revenue}
        result = {k: _display(value, Decimal("0.0001") if k in ("contribution_ratio", "gross_margin", "break_even_continuous_units") else MONEY) for k, value in result.items()}
        result.update(break_even_units=whole, break_even_status=break_status, runway_status=runway_status,
                      missing=[k for k in FIELDS if v[k] is None], currency="AED", source="user_assumptions",
                      rounding="Money: nearest fil, ROUND_HALF_UP. Ratios: 4 decimals. Whole units: ceiling.",
                      inputs={k: str(val) if isinstance(val, Decimal) else val for k, val in v.items()})
        return result


def analyze(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("inputs", {}), dict):
        raise FinanceInputError("inputs")
    base = payload.get("inputs", {})
    result = {"base": calculate(base), "scenarios": {}, "sensitivity": []}
    scenarios = payload.get("scenarios", {})
    if not isinstance(scenarios, dict) or set(scenarios) - {"conservative", "base", "optimistic"}:
        raise FinanceInputError("scenarios")
    for name in ("conservative", "base", "optimistic"):
        result["scenarios"][name] = calculate(scenarios.get(name, base))
    for field in ("units", "price", "variable_cost", "fixed_cost"):
        if base.get(field) in (None, ""):
            continue
        for percent in (-10, 10):
            altered = dict(base)
            number = Decimal(str(base[field])) * (Decimal(1) + Decimal(percent) / 100)
            altered[field] = str(number.to_integral_value(rounding=ROUND_HALF_UP) if field == "units" else number)
            result["sensitivity"].append({"field": field, "percent": percent, "result": calculate(altered)})
    stages = payload.get("allocations", [None] * 6)
    if not isinstance(stages, list) or len(stages) != 6:
        raise FinanceInputError("allocations")
    amounts = [parse_inputs({"available_capital": amount})["available_capital"] for amount in stages]
    allocation = _sum(amounts)
    capital = parse_inputs(base)["available_capital"]
    result["allocation"] = {"total": _display(allocation), "known_total": _display(sum((a for a in amounts if a is not None), Decimal(0))), "over_budget": capital is not None and sum((a for a in amounts if a is not None), Decimal(0)) > capital,
                            "remaining": _display(capital - allocation) if capital is not None and allocation is not None else None}
    return result
