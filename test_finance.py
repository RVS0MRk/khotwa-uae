"""Independent expected results for the Decimal financial contract."""

import unittest
from finance import calculate, analyze, FinanceInputError

BASE = dict(
    equipment="1000",
    initial_software="200",
    initial_marketing="300",
    other_startup="500",
    working_capital="1000",
    contingency="10",
    contingency_mode="percent",
    available_capital="3000",
    price="50",
    units="100",
    variable_cost="20",
    fixed_cost="1200",
    cogs_per_unit="15",
    cash_collections="4000",
    cash_operating_outflow="4600",
)


class FinanceTests(unittest.TestCase):
    def test_expected_example(self):
        r = calculate(BASE)
        for key, expected in dict(
            revenue="5000.00",
            variable_expenses="2000.00",
            operating_profit="1800.00",
            contribution_per_unit="30.00",
            contribution_ratio="0.6000",
            gross_profit="3500.00",
            gross_margin="0.7000",
            one_time_costs="2000.00",
            contingency_reserve="200.00",
            startup_capital="3200.00",
            funding_gap="200.00",
            operating_cash="800.00",
            monthly_cash_flow="-600.00",
            runway_months="1.33",
            break_even_units=40,
            break_even_revenue="2000.00",
        ).items():
            self.assertEqual(r[key], expected, key)

    def test_zero_sales(self):
        r = calculate(dict(BASE, units="0"))
        self.assertEqual((r["revenue"], r["operating_profit"], r["gross_margin"]), ("0.00", "-1200.00", None))

    def test_zero_price(self):
        r = calculate(dict(BASE, price="0"))
        self.assertIsNone(r["contribution_ratio"])
        self.assertEqual(r["break_even_status"], "unreachable")

    def test_zero_variable_cost(self):
        self.assertEqual(calculate(dict(BASE, variable_cost="0"))["operating_profit"], "3800.00")

    def test_zero_and_negative_contribution(self):
        for price in ("20", "10"):
            r = calculate(dict(BASE, price=price))
            self.assertEqual(r["break_even_status"], "unreachable")
            self.assertIsNone(r["break_even_units"])

    def test_zero_fixed_cost(self):
        self.assertEqual(calculate(dict(BASE, fixed_cost="0"))["break_even_units"], 0)

    def test_positive_and_neutral_cash_flow(self):
        for collected in ("4600", "5000"):
            r = calculate(dict(BASE, cash_collections=collected))
            self.assertEqual(r["runway_status"], "no_burn")
            self.assertIsNone(r["runway_months"])

    def test_cash_timing_is_independent_of_accounting_profit(self):
        r = calculate(BASE)
        self.assertEqual(r["operating_profit"], "1800.00")
        self.assertEqual(r["monthly_cash_flow"], "-600.00")

    def test_insufficient_initial_cash(self):
        r = calculate(dict(BASE, available_capital="100"))
        self.assertEqual(r["runway_status"], "underfunded")
        self.assertIsNone(r["runway_months"])

    def test_missing_values_are_not_zero(self):
        r = calculate({})
        for key in ("revenue", "operating_profit", "startup_capital", "funding_gap", "runway_months"):
            self.assertIsNone(r[key], key)
        self.assertIsNone(calculate(dict(BASE, equipment=""))["startup_capital"])
        self.assertEqual(calculate(dict(BASE, equipment="0"))["startup_capital"], "2100.00")

    def test_invalid_numbers(self):
        for value in ("NaN", "Infinity", "-1", "text", True, [], {}, "1e100"):
            with self.subTest(value=value), self.assertRaises(FinanceInputError):
                calculate(dict(BASE, price=value))
        with self.assertRaises(FinanceInputError):
            calculate(dict(BASE, units="1.5"))

    def test_very_large_values(self):
        r = calculate(dict(BASE, price="1000000000000", units="1000000000000"))
        self.assertEqual(r["revenue"], "1000000000000000000000000.00")

    def test_rounding_to_fils(self):
        r = calculate(dict(BASE, price="10.005", variable_cost="0.10", units="3"))
        self.assertEqual(r["revenue"], "30.03")
        self.assertEqual(r["contribution_per_unit"], "9.91")

    def test_whole_unit_ceiling(self):
        r = calculate(dict(BASE, fixed_cost="100", price="40", variable_cost="10"))
        self.assertEqual(
            (r["break_even_units"], r["break_even_revenue"], r["break_even_continuous_units"]), (4, "160.00", "3.3333")
        )

    def test_scenarios_do_not_mutate_each_other(self):
        scenarios = {"conservative": dict(BASE, units="10"), "base": dict(BASE), "optimistic": dict(BASE, units="200")}
        r = analyze({"inputs": BASE, "scenarios": scenarios})
        self.assertEqual([r["scenarios"][k]["operating_profit"] for k in scenarios], ["-900.00", "1800.00", "4800.00"])
        self.assertEqual(BASE["units"], "100")

    def test_sensitivity_independent_changes(self):
        r = analyze({"inputs": BASE})
        down = next(v for v in r["sensitivity"] if v["field"] == "price" and v["percent"] == -10)
        self.assertEqual(down["result"]["operating_profit"], "1300.00")
        up = next(v for v in r["sensitivity"] if v["field"] == "units" and v["percent"] == 10)
        self.assertEqual(up["result"]["operating_profit"], "2100.00")

    def test_allocation_warns_even_when_other_stages_unknown(self):
        r = analyze({"inputs": BASE, "allocations": ["4000", "", "", "", "", ""]})
        self.assertTrue(r["allocation"]["over_budget"])
        self.assertEqual(r["allocation"]["known_total"], "4000.00")
        self.assertIsNone(r["allocation"]["total"])

    def test_contingency_amount_and_percent_validation(self):
        self.assertEqual(calculate(dict(BASE, contingency="500", contingency_mode="aed"))["startup_capital"], "3500.00")
        with self.assertRaises(FinanceInputError):
            calculate(dict(BASE, contingency="101"))


if __name__ == "__main__":
    unittest.main()
