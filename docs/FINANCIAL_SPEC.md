# Financial calculation contract

The authoritative implementation is `finance.py`. It performs no network calls and stores no data. `/finance`, both PDF types and Advisor context use its results. The browser formats decimal strings and uses Number only for display and chart widths, never as the authoritative monetary engine.

## Inputs and units

All money is AED. `units` is a non-negative whole number per month; price, variable cost and COGS must describe the same founder-defined selling unit. Null or blank is unknown. Explicit zero is accepted. NaN, infinity, booleans, negative numbers, unknown fields and inputs greater than AED 1 trillion are rejected. The upper bound is a computational limit, not a suggested business assumption.

Money inputs and reports round to 0.01 AED using Decimal ROUND_HALF_UP. Intermediate calculations use 50-digit Decimal precision. Ratios and continuous break-even units report four decimals; runway reports two. Whole break-even units use ROUND_CEILING. Results are serialized as strings, except whole-unit counts and status fields.

## Formulas

| Output | Method |
|---|---|
| Monthly revenue | units × selling price |
| Monthly variable expenses | units × variable cost per unit |
| Contribution per unit | price − all variable cost per unit |
| Contribution ratio | contribution / price; unknown if price is zero |
| Gross profit | revenue − units × separately supplied accounting COGS per unit |
| Gross margin | gross profit / revenue; unknown if revenue is zero |
| Operating profit | revenue − variable expenses − fixed operating expenses |
| Continuous break-even units | fixed expenses / positive contribution per unit |
| Minimum whole break-even units | ceiling(continuous break-even units) |
| Whole-unit break-even revenue | minimum whole units × price |
| One-time expenses | equipment + initial software + launch marketing + other one-time costs |
| Contingency | directly entered AED, or chosen percentage of one-time expenses only |
| Required startup capital | one-time expenses + working-capital cash buffer + contingency |
| Funding gap | required capital − available funds; negative means surplus |
| Available operating cash | available funds − initial expenses − ring-fenced contingency |
| Monthly net cash flow | separately supplied cash collections − recurring cash payments |
| Runway | operating cash / positive monthly net cash burn |

Working capital is a required cash buffer, not a second spending item. It remains within available operating cash and is not deducted twice. A funding request is not treated as received money. COGS is an optional accounting classification; it is not assumed to equal all variable costs. Accounting profit and cash timing remain separate.

When contribution is zero or negative, break-even is `unreachable`, with no infinity or fabricated unit count. When cash flow is neutral or positive and operating cash is known, runway is `no_burn`. When initial spending is underfunded, runway is `underfunded`. Missing cash inputs produce `unknown`, even if accounting profit exists.

## Independently checked example

Equipment 1000 + software 200 + marketing 300 + other 500 = **2000** one-time expenses. A 10% contingency is **200**. With working capital 1000, required capital is **3200**. Available funds 3000 leave a **200** shortfall.

Price 50, units 100, variable cost 20 and fixed expenses 1200 produce revenue **5000**, variable expenses **2000**, contribution **30** per unit (**60%**) and operating profit **1800**. COGS 15 per unit gives gross profit **3500** and gross margin **70%**. Break-even is **40** whole units, generating **2000** revenue.

Cash collections 4000 and payments 4600 imply monthly burn **600**. Operating cash is 3000 − 2000 − 200 = **800**, giving **1.33 months** runway. Positive accounting profit therefore does not imply positive cash flow.

## Scenarios, sensitivity and stages

Three independently editable input dictionaries use the same engine. They initially match the base assumptions; no forecasts or fixed percentages are invented. Reset restores the first explicitly calculated inputs. Reducing scenario units to 10 in the example gives revenue 500 and operating loss 900, without changing the other scenarios.

Sensitivity changes units, price, variable cost or fixed cost separately by ±10%. Unit counts round to the nearest whole unit; other changed monetary inputs follow the fils policy. In the example, a 10% price decrease produces operating profit **1300**; a 10% unit increase produces **2100**.

Six stage allocations remain founder choices. A known allocation sum above available funds triggers a warning even if other stage budgets are blank. Full allocation totals and remaining capital remain unknown until every stage value is supplied. Stage completion and readiness checks are self-reported, never automatically inferred from AI prose.

## Boundaries

This is a single-period planning model, not a full ledger, tax model, debt amortization model or demand forecast. Founders must supply cash timing assumptions. Quotes, customer behavior, financing availability and regulatory approvals are not verified by the calculator. Sensitivity and scenarios are illustrations, not success probabilities.
