# Khotwa financial calculation contract (V2.1)

`finance.py` is the authoritative Decimal engine. It has no network or persistence. `/finance`, both PDF reports and Advisor context recalculate from user assumptions; clients cannot submit authoritative results.

Money inputs are AED decimal strings, rounded to fils with ROUND_HALF_UP. Intermediate precision is 50 digits. Output money and month estimates have two decimals; ratios and mathematical break-even units have four. Operational break-even units use ceiling. Blank/null means unknown, never zero. Negative zero normalizes to zero. Boolean, non-finite, negative nonzero, unknown fields, fractional units and values above the computational limit of 1 trillion are rejected.

## Inputs and outputs

| Output | Formula / assumption |
|---|---|
| Revenue | monthly whole units x price per matching unit |
| Variable expenses | units x variable cost per unit |
| Contribution | price minus all variable cost per unit |
| Contribution ratio | contribution / price; unknown at zero price |
| Operating profit | revenue minus variable expenses minus fixed expenses |
| Gross profit | revenue minus units x supplied accounting COGS |
| Gross margin | gross profit / revenue; unknown at zero revenue |
| Continuous break-even | fixed expenses / positive contribution |
| Whole break-even units | ceiling(continuous units); unreachable for contribution <= 0, except zero contribution AND zero fixed cost is at_break_even with 0 units |
| Break-even revenue | whole break-even units x price |
| One-time expenses | equipment + initial software + launch marketing + other setup + explicitly entered licensing |
| Contingency | entered AED or selected percent of one-time expenses only |
| Startup capital | one-time expenses + working-capital buffer + contingency |
| Funding gap | startup capital minus available funds; negative = surplus |
| Operating cash | available funds minus one-time expenses minus contingency |
| Monthly net cash flow | effective cash collections minus effective recurring payments |
| Cash runway | operating cash / positive monthly net cash burn |
| Simple payback months | one-time spending / positive monthly net cash benefit |

Working capital is held cash, not a second expense. Payback uses spent initial capital, excluding held working capital and contingency, and explicitly uses the selected cash basis. It ignores variable future cash flows and time value of money. No positive cash benefit means payback unavailable. Unknown cost/cash input means unknown payback. Zero initial spend with positive benefit yields 0.00 months. Underfunded initial spending has an underfunded runway status; zero or positive cash flow has a no-current-burn status, not infinity.

## Explicit accounting and cash modes

`cash_mode=entered` remains the raw API and legacy-record default. New browser businesses default to the disclosed `simplified` assumption; recovered saved modes remain unchanged. Separate cash receipts/payments remain authoritative even when profit is positive. `cash_mode=simplified` requires the user's selection: collections equal projected revenue, payments equal variable plus fixed operating expenses in the same month. It does not overwrite detailed cash fields or describe them as actuals. `cash_flow_basis` reports entered_cash_flow, simplified_user_assumption or missing_information.

`cogs_basis=separate` permits a different accounting category, including fixed production costs. No false restriction is imposed. With `subset_of_variable`, accounting COGS per unit cannot exceed variable cost per unit: the engine returns a warning and withholds contradictory gross profit/margin while retaining independent operating-profit calculations.

Licensing is optional and has no invented fee. Old saved records retain their known subtotal when it is absent; `licensing_not_provided` explicitly warns that capital excludes unprovided licensing. Missing licensing remains null. Entering 0 explicitly differs from leaving it blank. Users must move any licensing already inside Other costs to the new field to avoid duplicating their own input. An entered licensing amount is added exactly once, including the resulting change to percentage contingency.

## Scenarios and sensitivity

Default scenarios vary base sales volume by -20% and +20%, rounded to whole units with a minimum one-unit move when possible. Base retains original inputs; missing values remain missing. From zero, downside remains zero and upside is one; no negative sales are invented. These are labelled editable illustrations, not model forecasts or demand evidence. Independent dictionaries, individual reset, use-current/reset-original controls and same-tab recovery are preserved.

Sensitivity changes one assumption at a time toward +/-10%. Whole-unit changes that would round back to baseline move by at least one where possible. For three units, comparisons are two and four, labelled actual -33.33%/+33.33%, not literal +/-10%. The response includes baseline, actual rounded comparison, actual percentage, signed profit impact and complete result. Percentage from a zero baseline is undefined. Monetary comparisons reflect actual fil rounding. Results sort by descending absolute profit impact; tied leading fields are all named. The detailed table retains absolute-impact order. The chart groups the two directions per assumption, with groups ordered by maximum absolute impact and a zero-centered axis. Unequal moves differing by more than two percentage points receive an explanation. Identical scenario metrics move to one summary line rather than repeated columns.

Example: price 50, units 100, variable cost 20, fixed costs 1200 gives revenue 5000, contribution 30 (60%), profit 1800 and break-even 40 units. With initial costs 2000, working capital 1000, contingency 10%, and available funds 3000, startup capital is 3200 (licensing unprovided warning). Collections 4000 and payments 4600 give burn 600, operating cash 800 and runway 1.33 months. Simplified mode instead yields cash benefit 1800, no current burn and payback 1.11 months on known initial spending; it is not actual cash evidence.

## Presentation and boundaries

Both languages use Latin digits, thousands grouping, two decimal fils and the AED code: `3,200.00 AED`. RTL browser currency runs are directionally isolated to keep minus signs with their numbers. PDFs use the same numeric policy, percentage ratios such as 60%, whole operational units and localized footers. CSV contains raw and formatted values plus meaningful units; ratios are not labelled AED. Unknowns stay unknown. UI formatting does not change engine values.

This is a single-period educational model, not a ledger, tax calculation, financing offer, debt amortization schedule or forecast. User estimates do not earn customer-evidence points or alter the fixed five-by-five scoring methodology. Tests include retained V2 examples and 3,000 reproducible independent comparisons across different costs, prices, volumes, losses and cash benefits.

## V2.2 rounding and beginner-input contract

Percent contingency is rounded to fils **before** it is added to capital or subtracted from operating cash. All displayed components therefore reconcile exactly. Input values with more than two decimals return `rounded_fields` and `rounded_input:<field>` warnings so the interface explains rounding. Whole unit strings are plain decimal integers, never scientific notation.

Stage allocation `total` remains null until all six stages are supplied. `known_total` sums the provided stages, `remaining` is available funds minus that known subtotal, and `unallocated_stages` counts the missing entries. Remaining funds are useful without pretending all stages were costed.

The four-number browser starter defines price, units, variable cost and fixed cost, plus available funds prefilled from the budget. It supports revenue, contribution, operating profit and break-even. It cannot determine money already spent on setup or cash held in reserve. Numeric runway and payback remain unknown until their required startup assumptions exist; the UI explains the missing inputs and links Startup costs. This resolves the specification's conflicting request for four-input runway/payback without inventing zero costs. Explicit zero entries still work. A positive simplified monthly benefit has no current burn only when the operating-cash position is known.

The display uses positive Surplus/Shortfall funding labels, signed two-decimal percentage changes, grouped whole units and the shared AED formatter in Proof Mode, UI and reports. The raw engine funding gap remains signed for API compatibility. Automated coverage retains the 3,000 independent cases and adds 20,000 seeded reconciliation cases, zero/zero break-even and partial allocations.
