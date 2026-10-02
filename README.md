# Revenue Leakage & Recovery Analysis

> **Billed vs Banked: where does our money really go?**
> A SQL + Power BI analysis of a subscription business that finds where billed revenue never turns into collected revenue, and what can be recovered.

## Overview

Revenue that is billed is not always revenue that is collected. This project quantifies **revenue leakage** (money billed but not banked), identifies its main causes, and estimates how much can be **recovered**. KPIs and analytical views were built in SQL, then imported into Power BI for a 2-page interactive dashboard.

## Business Questions

- How much of the billed revenue is actually collected?
- Where does the leakage occur: failed payments, discounts, plan changes, churn, support-related credits?
- Which customer segments, plans, or channels contribute most to leakage?
- How much revenue is realistically recoverable, and what should be prioritised?
- How does marketing spend relate to the revenue actually retained?

## Key Findings

> Replace with your real numbers.

- Total billed: **[ ]** | Total collected: **[ ]** | Leakage: **[ ] ([ ]%)**
- Largest leakage driver: **[ ]**
- Highest-risk segment/plan: **[ ]**
- Estimated recoverable revenue: **[ ]**
- Top recommendation: **[ ]**

## Dataset

| File | Description |
|------|-------------|
| `customers.csv` | Customer master data |
| `invoices.csv` | Billed invoices and payment status |
| `subscriptions_plan_history.csv` | Plan changes (upgrades, downgrades, cancellations) over time |
| `support_tickets.csv` | Customer support tickets |
| `marketing_spend.csv` | Marketing spend by period/channel |

`generate_dataset.py` and `generation_summary.txt` document how the dataset was produced. 

> Add row counts and date range here.

## Approach

1. **Data loading:** loaded the five tables into a SQL database.
2. **KPI & view creation (SQL):** wrote queries and views for billed vs collected revenue, leakage by cause, segment-level analysis, and recovery potential.
3. **Data import:** imported the SQL views into Power BI.
4. **Dashboard (Power BI):** built a 2-page interactive dashboard on top of the views.
5. **Reporting:** summarised insights and recommendations in a written report and a presentation deck.

## Tools & Technologies

- **SQL** (**[MySQL / PostgreSQL / SQL Server]**): KPIs, joins, aggregations, views
- **Power BI:** data modelling, DAX measures, visualisation

## Dashboard

<!-- ![Page 1](images/page1.png)  ![Page 2](images/page2.png) -->

- **Page 1: [name]:** [what it shows, e.g. revenue overview and leakage KPIs]
- **Page 2: [name]:** [what it shows, e.g. leakage drivers and recovery opportunities]

## Project Structure
├── customers.csv
├── invoices.csv
├── subscriptions_plan_history.csv
├── support_tickets.csv
├── marketing_spend.csv
├── generate_dataset.py
├── generation_summary.txt
├── RevenueLoss_and_RecoveryAnalysis.pbix # Power BI dashboard
├── Revenue Leakage & Recovery Analysis.pdf # Written report
└── Billed-vs-Banked-Where-Does-Our-Money-Really-Go.pptx.pdf # Presentation deck


## How to Use

1. Clone the repo:
```bash
   git clone https://github.com/SonaliShakhawar/Revenue_Leakage_and_Recovery_Analysis.git
```
2. Load the CSVs into your SQL database and run the SQL scripts to create the views.
3. Open `RevenueLoss_and_RecoveryAnalysis.pbix` in Power BI Desktop and update the data source if prompted.

## Recommendations

> Fill in from your report.

## Author

**Sonali Shakhawar**
[GitHub](https://github.com/SonaliShakhawar)
