# Revenue Leakage & Recovery Analysis

> **Billed vs Banked: where does our money really go?**
> A SQL + Power BI analysis of a subscription business that finds where contracted revenue never turns into collected cash, which leaks are recoverable, and which warning signs appear before revenue is lost.

## Overview

Revenue that is contracted is not always revenue that is collected. This project quantifies **revenue leakage**, breaks it down by cause, identifies which leaks are recoverable, and links customer behaviour and acquisition channels to the money lost. KPIs and analytical views were built in SQL, then imported into Power BI for a 2-page interactive dashboard.

## Business Questions

- Where is the money going, and what should we fix first?
- How much of the contracted revenue is actually collected (capture rate)?
- Which leaks are recoverable, partially recoverable, or only preventable in future?
- Which acquisition channels return the most cash, and which leave spend unrecovered?
- What warning signs show up before a customer exits?

## Key Findings

**Overall performance**
- **Capture rate: 87.41%.** Of **$98.83M contracted**, only **$86.39M was collected**, a gap of about **$12.44M**.
- Including pricing leakage, total leakage comes to **$12.91M**.

**Leakage by category**

| Category | Amount | Share |
|----------|--------|-------|
| Collection leakage | $8.03M | 62.17% |
| Billing leakage | $4.42M | 34.19% |
| Pricing leakage | $0.47M | 3.64% |

**Recovery opportunity by leak**
- **Collection efficiency is the biggest and a recoverable leak (about $8.0M).**
- Other leaks sized: billing gap (contracted vs billed) **$4.42M**, discount leakage **$2.60M**, ownership NRR gap **$1.75M**, acquisition waste in Outbound Sales **$0.78M**, pricing gap (rate card realization) **$0.47M**.

**Acquisition channels**
- **Referral and Organic Search deliver the best 12-month cash multiple** and have the lowest CAC.
- **Outbound Sales is the worst performer:** highest CAC (about $2.8K), lowest cash multiple, and the largest unrecovered acquisition spend (about $0.78M), followed by **Paid Search** (about $0.6M).

**Warning signs and payment-led loss**
- **Seat cuts in the 90 days before exit are the strongest warning signal**, ahead of support tickets, having no assigned owner, and plan downgrades.
- Payment-led ("silent") churn costs about **$51.85K in monthly revenue**, and **$48.69K of unpaid invoices were never recovered**.
- Most revenue loss comes from **decided exits**, not silent payment-led ones.

## Dataset

| File | Description |
|------|-------------|
| `customers.csv` | Customer master data |
| `invoices.csv` | Billed invoices and payment status |
| `subscriptions_plan_history.csv` | Plan changes (upgrades, downgrades, cancellations) over time |
| `support_tickets.csv` | Customer support tickets |
| `marketing_spend.csv` | Marketing spend by channel |

`generate_dataset.py` and `generation_summary.txt` document how the dataset was produced.

## Approach

1. **Data loading:** loaded the five tables into a SQL database.
2. **KPI & view creation (SQL):** built views for capture rate, leakage by category, channel CAC and cash multiple, unrecovered acquisition spend, and pre-exit warning signals.
3. **Data import:** imported the SQL views into Power BI.
4. **Dashboard (Power BI):** built a 2-page interactive dashboard on top of the views.
5. **Reporting:** summarised insights and recommendations in a written report and a presentation deck.

## Tools & Technologies

- **SQL:** KPIs, joins, aggregations, views
- **Power BI:** data modelling, DAX measures, visualisation

## Project Structure

```
├── customers.csv
├── invoices.csv
├── subscriptions_plan_history.csv
├── support_tickets.csv
├── marketing_spend.csv
├── generate_dataset.py
├── generation_summary.txt
├── images/
│   ├── page1.png
│   └── page2.png
├── RevenueLoss_and_RecoveryAnalysis.pbix     # Power BI dashboard
├── Revenue Leakage & Recovery Analysis.pdf   # Written report
└── Billed-vs-Banked-Where-Does-Our-Money-Really-Go.pptx.pdf   # Presentation deck
```

## How to Use

1. Clone the repo:
```bash
   git clone https://github.com/SonaliShakhawar/Revenue_Leakage_and_Recovery_Analysis.git
```
2. Load the CSVs into your SQL database and run the SQL scripts to create the views.
3. Open `RevenueLoss_and_RecoveryAnalysis.pbix` in Power BI Desktop and update the data source if prompted.

## Recommendations

1. **Fix collections first.** It is the largest leak (about $8.0M) and is recoverable.
2. **Close the billing gap** between contracted and billed revenue ($4.42M).
3. **Reallocate acquisition spend** away from Outbound Sales and Paid Search toward Referral and Organic Search.
4. **Act on early warning signals.** Trigger outreach when seat cuts or support tickets spike, and make sure every account has an assigned owner.
5. **Review discount policy,** since discount leakage alone is about $2.6M.

## Author

**Sonali Shakhawar**
[GitHub](https://github.com/SonaliShakhawar)
