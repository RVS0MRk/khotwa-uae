"""Independent Round 2 arithmetic examples, including 3,000 seeded cases."""

import random
import unittest
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from finance import analyze, calculate
from financial_report import format_value
from test_finance import BASE


class RoundTwoFinanceTests(unittest.TestCase):
    def test_discrete_sensitivity_small_and_large_volumes(self):
        for units in (1, 2, 3, 100, 1000000):
            with self.subTest(units=units):
                result = analyze({"inputs": dict(BASE, units=str(units))})
                cases = [s for s in result["sensitivity"] if s["field"] == "units"]
                for s in cases:
                    baseline, comparison = Decimal(s["baseline"]), Decimal(s["comparison"])
                    self.assertNotEqual(baseline, comparison)
                    self.assertEqual(comparison, comparison.to_integral_value())
                    self.assertEqual(
                        Decimal(s["actual_percent"]),
                        ((comparison - baseline) / baseline * 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP),
                    )
                if units == 3:
                    self.assertEqual(sorted(int(s["comparison"]) for s in cases), [2, 4])

    def test_zero_unit_sensitivity_honestly_labels_undefined_percent(self):
        cases = [s for s in analyze({"inputs": dict(BASE, units="0")})["sensitivity"] if s["field"] == "units"]
        self.assertEqual(sorted(int(s["comparison"]) for s in cases), [0, 1])
        self.assertTrue(all(s["actual_percent"] is None for s in cases))

    def test_cash_flow_modes_and_missing_information(self):
        detailed = calculate(BASE)
        self.assertEqual(detailed["cash_flow_basis"], "entered_cash_flow")
        self.assertEqual(detailed["monthly_cash_flow"], "-600.00")
        raw = dict(BASE, cash_collections="", cash_operating_outflow="")
        self.assertEqual(calculate(raw)["cash_flow_basis"], "missing_information")
        simple = calculate(dict(raw, cash_mode="simplified"))
        self.assertEqual(simple["monthly_cash_flow"], "1800.00")
        self.assertEqual(simple["cash_flow_basis"], "simplified_user_assumption")
        self.assertEqual(simple["runway_status"], "no_burn")
        self.assertIsNone(simple["inputs"]["cash_collections"])
        missing = calculate(dict(raw, cash_mode="simplified", price=""))
        self.assertIsNone(missing["monthly_cash_flow"])

    def test_simplified_burning_runway(self):
        r = calculate(dict(BASE, cash_mode="simplified", units="10"))
        self.assertEqual((r["monthly_cash_flow"], r["runway_months"]), ("-900.00", "0.89"))

    def test_negative_zero_and_rounding(self):
        r = calculate(dict(BASE, equipment="-0.00", price="-0", variable_cost="0", fixed_cost="0"))
        self.assertEqual(r["inputs"]["equipment"], "0.00")
        self.assertEqual(r["operating_profit"], "0.00")
        self.assertEqual(format_value("revenue", "-0.00"), "0.00 AED")
        self.assertEqual(format_value("gross_margin", "-0.0000"), "0%")
        self.assertEqual(format_value("revenue", "5000.505"), "5,000.51 AED")
        self.assertEqual(format_value("revenue", "-3200.25", "ar"), "-3,200.25 AED")

    def test_accounting_cogs_basis(self):
        separate = calculate(dict(BASE, cogs_per_unit="25"))
        self.assertIsNotNone(separate["gross_margin"])
        subset = calculate(dict(BASE, cogs_per_unit="25", cogs_basis="subset_of_variable"))
        self.assertIn("cogs_exceeds_variable", subset["warnings"])
        self.assertIsNone(subset["gross_margin"])
        self.assertEqual(subset["operating_profit"], separate["operating_profit"])
        self.assertNotIn("cogs_exceeds_variable", calculate(dict(BASE, cogs_basis="subset_of_variable"))["warnings"])

    def test_payback_uses_cash_benefit_and_initial_spend(self):
        r = calculate(dict(BASE, cash_collections="5000", cash_operating_outflow="4500"))
        self.assertEqual((r["payback_months"], r["payback_status"]), ("4.00", "estimated"))
        self.assertNotEqual(r["monthly_cash_flow"], r["operating_profit"])
        self.assertEqual(calculate(dict(BASE, cash_mode="simplified"))["payback_months"], "1.11")

    def test_payback_edge_cases(self):
        for receipts in ("0", "4600"):
            r = calculate(dict(BASE, cash_collections=receipts))
            self.assertEqual(r["payback_status"], "no_positive_benefit")
            self.assertIsNone(r["payback_months"])
        self.assertEqual(calculate(dict(BASE, cash_collections=""))["payback_status"], "unknown")
        zero = dict(
            BASE, equipment="0", initial_software="0", initial_marketing="0", other_startup="0", cash_collections="5000"
        )
        self.assertEqual(calculate(zero)["payback_months"], "0.00")

    def test_optional_licensing_once_and_old_records(self):
        legacy = calculate(BASE)
        self.assertEqual(legacy["startup_capital"], "3200.00")
        self.assertIn("licensing_not_provided", legacy["warnings"])
        self.assertIsNone(legacy["inputs"]["licensing"])
        explicit = calculate(dict(BASE, licensing="0"))
        self.assertEqual(explicit["startup_capital"], legacy["startup_capital"])
        self.assertNotIn("licensing_not_provided", explicit["warnings"])
        entered = calculate(dict(BASE, licensing="100"))
        self.assertEqual(entered["one_time_costs"], "2100.00")
        self.assertEqual(entered["startup_capital"], "3310.00")

    def test_default_scenarios_independent_meaningful_and_missing(self):
        for units, expected in (("3", ["2", "3", "4"]), ("100", ["80", "100", "120"]), ("0", ["0", "0", "1"])):
            raw = dict(BASE, units=units)
            r = analyze({"inputs": raw})
            self.assertEqual([s["inputs"]["units"] for s in r["scenarios"].values()], expected)
            self.assertEqual(raw["units"], units)
        r = analyze({"inputs": {}})
        self.assertTrue(all(s["inputs"]["units"] is None for s in r["scenarios"].values()))

    def test_sensitivity_sorted_and_ties(self):
        r = analyze({"inputs": dict(BASE, variable_cost="0")})
        impacts = [abs(Decimal(s["profit_impact"])) for s in r["sensitivity"]]
        self.assertEqual(impacts, sorted(impacts, reverse=True))
        self.assertEqual(set(r["sensitivity_leaders"]), {"price", "units"})
        self.assertEqual(analyze({"inputs": {}})["sensitivity_leaders"], [])

    def test_seeded_independent_exact_arithmetic_3000_cases(self):
        rng = random.Random(2107)
        fils = lambda: Decimal(rng.randrange(0, 1000001)) / 100
        for case in range(3000):
            price, variable, fixed = fils(), fils(), fils()
            units = rng.choice([0, 1, 2, 3, rng.randrange(4, 1000001)])
            setup, licence, reserve, funds = fils(), fils(), fils(), fils()
            receipts, payments = fils(), fils()
            raw = {
                "equipment": str(setup),
                "initial_software": "0",
                "initial_marketing": "0",
                "other_startup": "0",
                "licensing": str(licence),
                "working_capital": "0",
                "contingency": str(reserve),
                "available_capital": str(funds),
                "price": str(price),
                "variable_cost": str(variable),
                "fixed_cost": str(fixed),
                "units": str(units),
                "cash_collections": str(receipts),
                "cash_operating_outflow": str(payments),
            }
            r = calculate(raw)
            expected = {
                "revenue": units * price,
                "operating_profit": units * (price - variable) - fixed,
                "startup_capital": setup + licence + reserve,
                "monthly_cash_flow": receipts - payments,
            }
            for key, value in expected.items():
                self.assertEqual(Decimal(r[key]), value, (case, key))
            if price > variable:
                self.assertEqual(
                    r["break_even_units"],
                    int((fixed / (price - variable)).to_integral_value(rounding=ROUND_CEILING)),
                    case,
                )
            if receipts > payments:
                expected_payback = ((setup + licence) / (receipts - payments)).quantize(
                    Decimal(".01"), rounding=ROUND_HALF_UP
                )
                self.assertEqual(Decimal(r["payback_months"]), expected_payback, case)

    def test_display_consistency_20000_cases(self):
        rng = random.Random(2208)
        cent = Decimal(".01")
        for case in range(20000):
            raw = dict(
                BASE,
                equipment=str(Decimal(rng.randrange(10000000)) / 1000),
                licensing=str(Decimal(rng.randrange(100000)) / 100),
                contingency=str(Decimal(rng.randrange(10000)) / 100),
                units=str(rng.randrange(1000001)),
            )
            r = calculate(raw)
            d = lambda key: Decimal(r[key])
            self.assertEqual(
                d("startup_capital"), d("one_time_costs") + d("working_capital") + d("contingency_reserve"), case
            )
            self.assertEqual(d("funding_gap"), d("startup_capital") - d("available_capital"), case)
            self.assertEqual(
                d("operating_cash"), d("available_capital") - d("one_time_costs") - d("contingency_reserve"), case
            )
            reserve = (d("one_time_costs") * Decimal(raw["contingency"]) / 100).quantize(cent, rounding=ROUND_HALF_UP)
            self.assertEqual(d("contingency_reserve"), reserve, case)
            self.assertEqual(r["inputs"]["units"], str(int(raw["units"])), case)
            self.assertEqual(d("revenue") - d("variable_expenses") - d("fixed_expenses"), d("operating_profit"))

    def test_rounding_zero_contribution_and_partial_allocation(self):
        zero = calculate(dict(BASE, price="20", variable_cost="20", fixed_cost="0", equipment="1.005"))
        self.assertEqual((zero["break_even_status"], zero["break_even_units"]), ("at_break_even", 0))
        self.assertEqual(zero["inputs"]["equipment"], "1.01")
        self.assertIn("rounded_input:equipment", zero["warnings"])
        allocation = analyze(
            {"inputs": {"available_capital": "1000"}, "allocations": ["100", None, "50", None, None, None]}
        )["allocation"]
        self.assertEqual(
            allocation,
            {
                "total": None,
                "known_total": "150.00",
                "remaining": "850.00",
                "unallocated_stages": 4,
                "over_budget": False,
            },
        )

    def test_four_operating_inputs_do_not_invent_startup_spending(self):
        r = calculate(
            {
                "price": "30",
                "units": "100",
                "variable_cost": "12",
                "fixed_cost": "500",
                "cash_mode": "simplified",
                "available_capital": "3000",
            }
        )
        self.assertEqual((r["revenue"], r["operating_profit"], r["break_even_units"]), ("3000.00", "1300.00", 28))
        self.assertIsNone(r["runway_months"])
        self.assertIsNone(r["payback_months"])
        self.assertEqual((r["runway_status"], r["payback_status"]), ("unknown", "unknown"))


if __name__ == "__main__":
    unittest.main()
