"""
Board-Ready MRR Waterfall Dataset — synthetic data generator
Seed: 42 (fixed for reproducibility)

Generates 5 CSVs: customers, subscriptions_plan_history, invoices,
support_tickets, marketing_spend.

NOTE ON A DELIBERATE DEVIATION FROM THE SPEC (documented, not hidden):
The brief's churn hazard (8%/month for months 1-3, tapering to a steady
1.5%/month) is mathematically incompatible with landing 150k-180k invoice
rows inside a 48-month window. Even in the most extreme case (every one of
the 5,000 customers signs up in month 0, and churn hazard drops to 0% after
month 12), the ceiling is ~142k invoices — still short of the low end of
the target range. Chasing the row-count target by flattening the hazard
curve toward zero would gut the churn signal that's the entire point of a
"bathtub curve" dataset (cohort curves would look almost flat).
Resolution used here: keep the bathtub *shape* (a ~5x multiple between
early-tenure and steady-state monthly hazard) but scale the magnitude down,
and front-load new-customer signups somewhat more toward the earlier years
(a realistic "strong early growth, slower afterward" pattern for a
maturing SaaS company). This lands at ~125k-135k invoice rows with ~30-33%
cumulative 4-year logo churn — short of the 150k-180k target, but a dataset
where retention curves and churn-ticket correlation actually show signal.
"""

import numpy as np
import pandas as pd
from datetime import timedelta

SEED = 42
rng = np.random.default_rng(SEED)

N_CUSTOMERS = 5000
CUSTOMER_ID_START = 100000

MONTHS = pd.date_range('2021-01-01', '2024-12-01', freq='MS')
N_MONTHS = len(MONTHS)  # 48
DATASET_END = pd.Timestamp('2025-01-01')  # exclusive upper bound

CHANNELS = ['Paid Search', 'Organic Search', 'Referral', 'Outbound Sales', 'Partner', 'Content/Social']
CHANNEL_WEIGHTS = [0.22, 0.20, 0.18, 0.14, 0.12, 0.14]

INDUSTRIES = ['SaaS', 'Retail', 'Healthcare', 'Financial Services', 'Education',
              'Manufacturing', 'Media', 'Logistics']

COUNTRIES = ['United States', 'United Kingdom', 'India', 'Canada', 'Australia', 'Germany']
COUNTRY_WEIGHTS = [0.55, 0.12, 0.10, 0.08, 0.05, 0.05]
OTHER_COUNTRIES = ['France', 'Brazil', 'Singapore', 'Japan', 'South Africa', 'Netherlands']

PLAN_TIERS = ['Starter', 'Growth', 'Pro', 'Enterprise']
PLAN_WEIGHTS = [0.45, 0.35, 0.15, 0.05]
PLAN_SEAT_RANGE = {'Starter': (1, 5), 'Growth': (5, 20), 'Pro': (20, 100), 'Enterprise': (50, 1000)}
PLAN_PRICE_PER_SEAT = {'Starter': 15.0, 'Growth': 29.0, 'Pro': 49.0}  # Enterprise handled separately

# ---- signup timing: mildly front-loaded across years + Jan/Sept seasonal bump ----
YEAR_WEIGHT = {0: 2.0, 1: 1.1, 2: 0.6, 3: 0.3}
MOY_BOOST = {0: 1.25, 8: 1.15}  # Jan, Sept

# ---- churn hazard: bathtub shape, magnitude scaled down from spec (see note above) ----
HAZARD_EARLY = 0.03      # months 1-3
HAZARD_STEADY = 0.006    # month 13+
HAZARD_TAPER_END = 12    # linear taper from month 3 to month 12


def monthly_hazard(tenure_month: int) -> float:
    """tenure_month is 1-indexed months since signup."""
    if tenure_month <= 3:
        return HAZARD_EARLY
    elif tenure_month <= HAZARD_TAPER_END:
        frac = (tenure_month - 3) / (HAZARD_TAPER_END - 3)
        return HAZARD_EARLY + (HAZARD_STEADY - HAZARD_EARLY) * frac
    else:
        return HAZARD_STEADY


print("Config loaded. Generating customers...")

# ---------------------------------------------------------------------------
# Company name generation
# ---------------------------------------------------------------------------
NAME_PREFIX = [
    "Nimbus", "Vertex", "Northwind", "Cobalt", "Solstice", "Ironclad", "Bluepeak",
    "Meridian", "Lumen", "Anchor", "Crestline", "Redwood", "Silverline", "Catalyst",
    "Beacon", "Harborview", "Summit", "Cascade", "Pinecrest", "Steadfast", "Clearwater",
    "Vantage", "Fieldstone", "Amberlight", "Granite", "Wildflower", "Orbital", "Keystone",
    "Brightline", "Fernway", "Hollowbrook", "Ridgeline", "Sable", "Cinder", "Marrow",
    "Palisade", "Driftwood", "Lattice", "Thornbury", "Windward", "Copperfield", "Quarrystone",
    "Halcyon", "Tidewater", "Overlook", "Basalt", "Wrenfield", "Aldergate", "Brackenridge",
    "Fallowmere",
]
NAME_MID = [
    "Data", "Cloud", "Logic", "Works", "Digital", "Analytics", "Health", "Retail",
    "Finance", "Learning", "Robotics", "Media", "Freight", "Supply", "Systems", "", "", "",
]
NAME_SUFFIX = [
    "Inc.", "LLC", "Group", "Solutions", "Technologies", "Partners", "Co.", "Systems",
    "Labs", "Holdings", "Industries", "Corp.", "Ventures", "Collective", "Networks",
]


def make_company_name(rnd):
    prefix = rnd.choice(NAME_PREFIX)
    mid = rnd.choice(NAME_MID)
    suffix = rnd.choice(NAME_SUFFIX)
    if mid:
        return f"{prefix} {mid} {suffix}"
    return f"{prefix} {suffix}"


company_names = [make_company_name(rng) for _ in range(N_CUSTOMERS)]
# de-dup exact collisions by appending a differentiator, keep it rare
seen = {}
for i, nm in enumerate(company_names):
    if nm in seen:
        seen[nm] += 1
        company_names[i] = f"{nm} ({seen[nm]})"
    else:
        seen[nm] = 0

# Inject ~25 intentional near-duplicate-looking names (real datasets have these:
# "Acme Solutions" vs "Acme Solutions Inc" vs "Acme Solutions LLC")
near_dupe_idx = rng.choice(N_CUSTOMERS, size=25, replace=False)
for idx in near_dupe_idx:
    base = company_names[idx].split(" (")[0]
    # strip a trailing known suffix if present, then re-suffix
    variant_suffix = rng.choice(["Inc", "LLC", "Group", "Co"])
    parts = base.rsplit(" ", 1)
    company_names[idx] = f"{parts[0]} {variant_suffix}" if len(parts) == 2 else f"{base} {variant_suffix}"

# ---------------------------------------------------------------------------
# Signup timing
# ---------------------------------------------------------------------------
signup_weights = np.zeros(N_MONTHS)
for i in range(N_MONTHS):
    yr, moy = i // 12, i % 12
    signup_weights[i] = YEAR_WEIGHT[yr] * MOY_BOOST.get(moy, 1.0)
signup_weights /= signup_weights.sum()

signup_month_idx = rng.choice(N_MONTHS, size=N_CUSTOMERS, p=signup_weights)
signup_day = rng.integers(1, 29, size=N_CUSTOMERS)  # avoid month-length edge cases
signup_dates = pd.to_datetime(
    [MONTHS[m] + timedelta(days=int(d) - 1) for m, d in zip(signup_month_idx, signup_day)]
)

# ---------------------------------------------------------------------------
# Acquisition channel, country, industry
# ---------------------------------------------------------------------------
acquisition_channel = rng.choice(CHANNELS, size=N_CUSTOMERS, p=CHANNEL_WEIGHTS)

country_choice = rng.choice(COUNTRIES + ['__other__'], size=N_CUSTOMERS, p=COUNTRY_WEIGHTS + [0.05])
country = np.array([
    c if c != '__other__' else rng.choice(OTHER_COUNTRIES) for c in country_choice
])

industry = rng.choice(INDUSTRIES, size=N_CUSTOMERS)

# ---------------------------------------------------------------------------
# Company size (right-skewed; NULL ~10%)
# ---------------------------------------------------------------------------
raw_size = rng.lognormal(mean=3.0, sigma=1.3, size=N_CUSTOMERS)
company_size = np.clip(raw_size, 1, 5000).round().astype(float)
size_null_mask = rng.random(N_CUSTOMERS) < 0.10
company_size[size_null_mask] = np.nan

# ---------------------------------------------------------------------------
# Churn simulation (bathtub hazard)
# ---------------------------------------------------------------------------
churn_month_idx = np.full(N_CUSTOMERS, -1)  # -1 = never churned within window
for i in range(N_CUSTOMERS):
    s = signup_month_idx[i]
    for m in range(s, N_MONTHS):
        tenure = m - s + 1  # this is the tenure-th month they'd be billed for
        if rng.random() < monthly_hazard(tenure):
            # they ARE billed for month m (their tenure-th month) and then
            # leave before the next one -- churn_month_idx is the first
            # month with no invoice, never the signup month itself
            candidate = m + 1
            if candidate < N_MONTHS:
                churn_month_idx[i] = candidate
            # else: hazard fired on the last month in the window -- that
            # "churn" would land after the observation period, so as of
            # Dec 2024 this customer is still on the books (leave at -1)
            break

is_churned = churn_month_idx >= 0
customer_status = np.where(is_churned, 'Churned', 'Active')
# a small slice of survivors get "Paused" instead of "Active"
active_mask = customer_status == 'Active'
active_idx = np.where(active_mask)[0]
paused_pick = rng.random(len(active_idx)) < 0.03
customer_status[active_idx[paused_pick]] = 'Paused'

# churn_date: first day of the churn month, used only internally to bound invoices/tickets
churn_date = np.where(
    is_churned,
    MONTHS[np.clip(churn_month_idx, 0, N_MONTHS - 1)],
    np.datetime64('NaT'),
)

print(f"Signups generated. Cumulative churn rate: {is_churned.mean():.1%}")

# ---------------------------------------------------------------------------
# Account owner (NULL for self-serve; rate depends on acquisition channel)
# ---------------------------------------------------------------------------
SALES_REPS = [
    "Priya Anand", "Marcus Webb", "Jordan Kim", "Elena Torres", "Sam O'Rourke",
    "Devon Wallace", "Grace Lin", "Tariq Rahman", "Hannah Ostrowski", "Leo Castillo",
    "Nadia Petrov", "Owen Fitzgerald", "Mei Chen", "Isaac Brennan", "Farah Sultan",
]
# self-serve-heavy channels have a much higher chance of no assigned rep
NULL_OWNER_RATE = {
    'Outbound Sales': 0.04,
    'Partner': 0.17,
    'Paid Search': 0.40,
    'Organic Search': 0.49,
    'Referral': 0.36,
    'Content/Social': 0.49,
}
account_owner = np.empty(N_CUSTOMERS, dtype=object)
for i in range(N_CUSTOMERS):
    ch = acquisition_channel[i]
    if rng.random() < NULL_OWNER_RATE[ch]:
        account_owner[i] = None
    else:
        account_owner[i] = rng.choice(SALES_REPS)

# ---------------------------------------------------------------------------
# Deliberate messiness: inconsistent casing in industry / country (~1.5% of rows)
# ---------------------------------------------------------------------------
industry_display = industry.astype(object).copy()
country_display = country.astype(object).copy()

messy_idx = rng.choice(N_CUSTOMERS, size=int(N_CUSTOMERS * 0.015), replace=False)
for idx in messy_idx:
    choice = rng.integers(0, 3)
    if choice == 0:
        industry_display[idx] = industry_display[idx].lower()
    elif choice == 1:
        industry_display[idx] = industry_display[idx].upper()
    else:
        industry_display[idx] = f" {industry_display[idx]} "  # stray whitespace

messy_country_idx = rng.choice(N_CUSTOMERS, size=int(N_CUSTOMERS * 0.015), replace=False)
COUNTRY_TYPO = {'United States': 'USA', 'United Kingdom': 'UK'}
for idx in messy_country_idx:
    c = country_display[idx]
    if c in COUNTRY_TYPO and rng.random() < 0.6:
        country_display[idx] = COUNTRY_TYPO[c]
    else:
        country_display[idx] = c.lower()

# ---------------------------------------------------------------------------
# Assemble customers DataFrame
# ---------------------------------------------------------------------------
customer_ids = np.arange(CUSTOMER_ID_START, CUSTOMER_ID_START + N_CUSTOMERS)

customers_df = pd.DataFrame({
    'customer_id': customer_ids,
    'company_name': company_names,
    'industry': industry_display,
    'country': country_display,
    'company_size_employees': company_size,
    'signup_date': signup_dates.date,
    'acquisition_channel': acquisition_channel,
    'account_owner': account_owner,
    'customer_status': customer_status,
})

print(customers_df.head())
print(customers_df.isna().mean().round(3))

# ---------------------------------------------------------------------------
# Each customer's "observed end" — last day they're considered on-book.
# Churned -> the day before their churn month starts. Still active/paused ->
# end of the dataset window (Dec 2024).
# ---------------------------------------------------------------------------
customer_end_date = np.where(
    is_churned,
    (pd.to_datetime(churn_date) - timedelta(days=1)).values,
    np.datetime64(DATASET_END - timedelta(days=1)),
)
customer_end_date = pd.to_datetime(customer_end_date)

# last billable month index (inclusive) per customer
last_billed_month_idx = np.where(is_churned, churn_month_idx - 1, N_MONTHS - 1)
last_billed_month_idx = np.clip(last_billed_month_idx, signup_month_idx, N_MONTHS - 1)

# ---------------------------------------------------------------------------
# Plan tier helpers
# ---------------------------------------------------------------------------
TIER_RANK = {t: i for i, t in enumerate(PLAN_TIERS)}


def sample_initial_tier(size_hint, rnd):
    """Bias toward higher tiers for larger companies; base distribution otherwise."""
    if size_hint is not None and not np.isnan(size_hint):
        if size_hint >= 500:
            weights = [0.05, 0.20, 0.40, 0.35]
        elif size_hint >= 100:
            weights = [0.15, 0.40, 0.35, 0.10]
        elif size_hint >= 20:
            weights = [0.35, 0.45, 0.18, 0.02]
        else:
            weights = [0.60, 0.32, 0.07, 0.01]
    else:
        weights = PLAN_WEIGHTS
    return rnd.choice(PLAN_TIERS, p=weights)


def price_for_tier(tier, rnd):
    if tier == 'Enterprise':
        return round(rnd.uniform(20, 45), 2)
    return PLAN_PRICE_PER_SEAT[tier]


def seats_for_tier(tier, rnd):
    lo, hi = PLAN_SEAT_RANGE[tier]
    # Pareto-ish skew within range: mostly toward the low end, a long tail up top
    span = hi - lo
    skewed = lo + span * (rnd.random() ** 2.2)
    return max(lo, int(round(skewed)))


CHANGE_REASONS_FOLLOWUP = ['Upgrade', 'Downgrade', 'Seat Change', 'Renewal']
CHANGE_REASON_WEIGHTS = [0.35, 0.15, 0.30, 0.20]

sub_rows = []
sub_id_counter = 1

for i in range(N_CUSTOMERS):
    cust_id = customer_ids[i]
    start = signup_dates[i]
    end = customer_end_date[i]  # inclusive last day on-book
    span_days = max((end - start).days, 1)

    # number of plan rows for this customer (mean ~1.8)
    n_rows = rng.choice([1, 2, 3, 4, 5], p=[0.50, 0.28, 0.13, 0.06, 0.03])
    n_rows = min(n_rows, max(1, span_days // 20))  # don't cram 5 changes into 10 days

    # breakpoints strictly inside (start, end) to split into n_rows segments
    if n_rows > 1:
        offsets = sorted(rng.choice(range(1, span_days), size=n_rows - 1, replace=False))
        boundaries = [start] + [start + timedelta(days=int(o)) for o in offsets] + [end + timedelta(days=1)]
    else:
        boundaries = [start, end + timedelta(days=1)]

    tier = sample_initial_tier(company_size[i], rng)
    seats = seats_for_tier(tier, rng)
    price = price_for_tier(tier, rng)

    for r in range(n_rows):
        valid_from = boundaries[r]
        valid_to = boundaries[r + 1] if r < n_rows - 1 else pd.NaT

        if r > 0:
            reason = rng.choice(CHANGE_REASONS_FOLLOWUP, p=CHANGE_REASON_WEIGHTS)
            rank = TIER_RANK[tier]
            prev_monthly = seats * price if not pd.isna(price) else seats * 30.0

            # Already at the top/bottom tier: an Upgrade/Downgrade can't apply
            # in the requested direction, so relabel it as what actually
            # happens (a seat increase/decrease) rather than mislabeling a
            # no-op change as "Upgrade"/"Downgrade".
            if reason == 'Upgrade' and rank == len(PLAN_TIERS) - 1:
                reason = 'Seat Change'
            elif reason == 'Downgrade' and rank == 0:
                reason = 'Seat Change'

            if reason == 'Upgrade':
                tier = PLAN_TIERS[rank + 1]
                price = price_for_tier(tier, rng)
                # pick seats so total revenue reliably rises, regardless of how
                # the new tier's per-seat rate compares to the old one
                target_monthly = prev_monthly * rng.uniform(1.15, 1.9)
                lo, hi = PLAN_SEAT_RANGE[tier]
                seats = int(np.clip(round(target_monthly / price), lo, hi))
            elif reason == 'Downgrade':
                tier = PLAN_TIERS[rank - 1]
                price = price_for_tier(tier, rng)
                target_monthly = prev_monthly * rng.uniform(0.45, 0.8)
                lo, hi = PLAN_SEAT_RANGE[tier]
                seats = int(np.clip(round(target_monthly / price), lo, hi))
            elif reason == 'Seat Change':
                lo, hi = PLAN_SEAT_RANGE[tier]
                # bias the delta toward growth when already at the tier ceiling,
                # toward shrinkage when at the floor, so it isn't a silent no-op
                if seats >= hi:
                    delta = rng.integers(-max(1, seats // 3), 0)
                elif seats <= lo:
                    delta = rng.integers(1, max(2, seats // 2 + 1))
                else:
                    delta = rng.integers(-max(1, seats // 4), max(2, seats // 3))
                    if delta == 0:
                        delta = 1
                seats = int(np.clip(seats + delta, lo, hi))
            # Renewal: no structural change
        else:
            reason = 'Initial Signup'

        # ~2% of rows lose their change_reason to a data-entry gap
        if rng.random() < 0.02:
            reason = None

        price_val = price
        if tier == 'Enterprise' and rng.random() < 0.03:
            price_val = np.nan  # custom pricing still being finalized

        if pd.isna(price_val):
            # monthly price negotiated directly, not seats * per-seat rate
            monthly_price = round(seats * rng.uniform(20, 45) * rng.uniform(0.9, 1.05), 2)
        else:
            monthly_price = round(seats * price_val, 2)
            if rng.random() < 0.10:  # negotiated discount baked into the contract
                monthly_price = round(monthly_price * rng.uniform(0.85, 0.97), 2)

        sub_rows.append({
            'subscription_id': sub_id_counter,
            'customer_id': cust_id,
            'plan_name': tier,
            'seats': seats,
            'price_per_seat': price_val,
            'monthly_price': monthly_price,
            'valid_from': valid_from.date(),
            'valid_to': valid_to.date() if not pd.isna(valid_to) else None,
            'change_reason': reason,
        })
        sub_id_counter += 1

subscriptions_df = pd.DataFrame(sub_rows)
print("\nsubscriptions_plan_history rows:", len(subscriptions_df))
print("avg rows/customer:", len(subscriptions_df) / N_CUSTOMERS)
print(subscriptions_df.isna().mean().round(3))
print(subscriptions_df['plan_name'].value_counts(normalize=True).round(3))

# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------
# Build a fast per-customer lookup of plan segments sorted by valid_from
subs_by_customer = {}
for row in sub_rows:
    subs_by_customer.setdefault(row['customer_id'], []).append(row)
for cid in subs_by_customer:
    subs_by_customer[cid].sort(key=lambda r: r['valid_from'])

invoice_rows = []
invoice_id_counter = 1000000

for i in range(N_CUSTOMERS):
    cust_id = customer_ids[i]
    segs = subs_by_customer[cust_id]
    seg_idx = 0
    n_segs = len(segs)

    for m in range(signup_month_idx[i], last_billed_month_idx[i] + 1):
        month_start = MONTHS[m].date()
        month_end = (MONTHS[m] + pd.offsets.MonthEnd(1)).date()

        # advance seg_idx until we find the segment active at month_start
        while (seg_idx < n_segs - 1) and (segs[seg_idx]['valid_to'] is not None) and (segs[seg_idx]['valid_to'] <= month_start):
            seg_idx += 1
        seg = segs[seg_idx]

        amount_due = seg['monthly_price']

        # partial first month: signup can land mid-month, so the first invoice
        # is prorated to the days actually held that month (not a full month)
        if m == signup_month_idx[i]:
            days_in_month = (month_end - month_start).days + 1
            days_held = days_in_month - signup_dates[i].day + 1
            amount_due = round(amount_due * (days_held / days_in_month), 2)
        # proration noise if a transition happens *within* this month
        next_seg = segs[seg_idx + 1] if seg_idx + 1 < n_segs else None
        if next_seg is not None and month_start <= next_seg['valid_from'] <= month_end:
            blend = rng.uniform(0.85, 1.10)
            amount_due = round(amount_due * blend, 2)

        discount_pct = np.nan
        if rng.random() < 0.15:  # ~85% NULL overall
            discount_pct = round(rng.uniform(5, 30), 1)
            amount_due = round(amount_due * (1 - discount_pct / 100), 2)

        status = rng.choice(
            ['Paid', 'Failed', 'Pending', 'Refunded'],
            p=[0.92, 0.04, 0.02, 0.02],
        )

        if status in ('Failed', 'Pending'):
            payment_date = None
            amount_paid = 0.0
        elif status == 'Refunded':
            payment_date = (pd.Timestamp(month_start) + timedelta(days=int(rng.integers(1, 12)))).date()
            amount_paid = 0.0
        else:  # Paid
            payment_date = (pd.Timestamp(month_start) + timedelta(days=int(rng.integers(0, 12)))).date()
            if rng.random() < 0.02:
                amount_paid = round(amount_due * rng.uniform(0.5, 0.95), 2)
            else:
                amount_paid = amount_due

        invoice_rows.append({
            'invoice_id': invoice_id_counter,
            'customer_id': cust_id,
            'subscription_id': seg['subscription_id'],
            'billing_month': month_start,
            'amount_due': amount_due,
            'amount_paid': amount_paid,
            'invoice_status': status,
            'payment_date': payment_date,
            'discount_pct': discount_pct,
        })
        invoice_id_counter += 1

invoices_df = pd.DataFrame(invoice_rows)
print("\ninvoices rows:", len(invoices_df))
print(invoices_df.isna().mean().round(3))
print(invoices_df['invoice_status'].value_counts(normalize=True).round(3))

# ---------------------------------------------------------------------------
# Support tickets — volume correlated with churn proximity
# ---------------------------------------------------------------------------
TICKET_CATEGORIES = ['Billing', 'Technical Issue', 'Feature Request', 'Onboarding', 'Cancellation Request']
BASE_CATEGORY_WEIGHTS = [0.25, 0.30, 0.20, 0.15, 0.10]
PRIORITIES = ['Low', 'Medium', 'High', 'Urgent']
BASE_PRIORITY_WEIGHTS = [0.40, 0.35, 0.18, 0.07]

MU_BASE = 0.34         # baseline expected tickets per active customer-month
MU_CHURN_BOOST = 3.0   # multiplier applied in the 2 months leading up to churn
ONBOARDING_TENURE_MONTHS = 2

ticket_rows = []
ticket_id_counter = 1

for i in range(N_CUSTOMERS):
    cust_id = customer_ids[i]
    s = signup_month_idx[i]
    churned = is_churned[i]
    window_end = churn_month_idx[i] if churned else N_MONTHS - 1

    for m in range(s, window_end + 1):
        tenure = m - s + 1
        months_to_churn = (churn_month_idx[i] - m) if churned else None

        mu = MU_BASE
        near_churn = churned and months_to_churn is not None and months_to_churn <= 1
        if near_churn:
            mu *= MU_CHURN_BOOST

        n_tickets = rng.poisson(mu)
        for _ in range(min(n_tickets, 3)):
            # category selection
            if tenure <= ONBOARDING_TENURE_MONTHS and rng.random() < 0.5:
                category = 'Onboarding'
            elif near_churn and rng.random() < 0.55:
                category = rng.choice(['Cancellation Request', 'Technical Issue'], p=[0.65, 0.35])
            else:
                category = rng.choice(TICKET_CATEGORIES, p=BASE_CATEGORY_WEIGHTS)

            # priority selection
            if category == 'Cancellation Request' or (near_churn and category == 'Technical Issue'):
                priority = rng.choice(PRIORITIES, p=[0.10, 0.20, 0.40, 0.30])
            else:
                priority = rng.choice(PRIORITIES, p=BASE_PRIORITY_WEIGHTS)

            created_day = int(rng.integers(0, 28))
            created_date = MONTHS[m].date() + timedelta(days=created_day)

            days_to_end = (DATASET_END.date() - created_date).days
            if days_to_end <= 20:
                unresolved = rng.random() < 0.75  # very recent tickets are usually still open
            else:
                unresolved = rng.random() < 0.08

            if unresolved:
                resolved_date = None
            else:
                resolve_lag = int(rng.integers(1, 31))
                resolved_date = min(created_date + timedelta(days=resolve_lag), DATASET_END.date() - timedelta(days=1))

            if rng.random() < 0.45:  # ~55% NULL overall
                if priority in ('High', 'Urgent') or category == 'Cancellation Request':
                    csat = rng.choice([1, 2, 3, 4, 5], p=[0.30, 0.25, 0.20, 0.15, 0.10])
                else:
                    csat = rng.choice([1, 2, 3, 4, 5], p=[0.08, 0.10, 0.17, 0.30, 0.35])
            else:
                csat = None

            ticket_rows.append({
                'ticket_id': ticket_id_counter,
                'customer_id': cust_id,
                'created_date': created_date,
                'category': category,
                'priority': priority,
                'resolved_date': resolved_date,
                'csat_score': csat,
            })
            ticket_id_counter += 1

tickets_df = pd.DataFrame(ticket_rows)
print("\nsupport_tickets rows:", len(tickets_df))
print(tickets_df.isna().mean().round(3))

# ---------------------------------------------------------------------------
# Marketing spend — 6 channels x 48 months
# ---------------------------------------------------------------------------
# actual new-customer counts per channel+month, straight from customers_df,
# so LTV:CAC ties out exactly with the acquisition data (integrity rule #3)
signup_month_col = MONTHS[signup_month_idx]
customer_channel_month = pd.DataFrame({
    'acquisition_channel': acquisition_channel,
    'signup_month': signup_month_col,
})
new_cust_lookup = (
    customer_channel_month
    .groupby(['acquisition_channel', 'signup_month'])
    .size()
)

CHANNEL_COST_TIER = {
    'Outbound Sales': (28000, 48000),
    'Paid Search': (22000, 40000),
    'Partner': (9000, 18000),
    'Content/Social': (6000, 14000),
    'Organic Search': (2000, 6000),
    'Referral': (800, 2500),
}
CHANNEL_COST_PER_LEAD = {
    'Paid Search': 45,
    'Organic Search': 12,
    'Outbound Sales': 90,
    'Content/Social': 20,
}

spend_rows = []
spend_id_counter = 1
for channel in CHANNELS:
    lo, hi = CHANNEL_COST_TIER[channel]
    # mild upward drift in spend over the 4 years
    for m in range(N_MONTHS):
        growth_factor = 1.0 + 0.35 * (m / (N_MONTHS - 1))
        base_spend = rng.uniform(lo, hi) * growth_factor
        spend_amount = round(base_spend, 2)

        month_date = MONTHS[m]
        new_customers = int(new_cust_lookup.get((channel, month_date), 0))

        if channel in ('Referral', 'Partner'):
            leads = None
        else:
            cpl = CHANNEL_COST_PER_LEAD[channel]
            leads = int(round(spend_amount / cpl * rng.uniform(0.85, 1.15)))
            leads = max(leads, new_customers)  # can't win more customers than leads generated

        spend_rows.append({
            'spend_id': spend_id_counter,
            'channel': channel,
            'month': month_date.date(),
            'spend_amount': spend_amount,
            'new_customers_acquired': new_customers,
            'leads_generated': leads,
        })
        spend_id_counter += 1

marketing_df = pd.DataFrame(spend_rows)
print("\nmarketing_spend rows:", len(marketing_df))
print(marketing_df.isna().mean().round(3))
print(marketing_df.groupby('channel')['spend_amount'].mean().round(0))

# ---------------------------------------------------------------------------
# Write CSVs + a plain-text row-count / null-count summary
# ---------------------------------------------------------------------------
import os

OUT_DIR = "/mnt/user-data/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

tables = {
    "customers": customers_df,
    "subscriptions_plan_history": subscriptions_df,
    "invoices": invoices_df,
    "support_tickets": tickets_df,
    "marketing_spend": marketing_df,
}

for name, df in tables.items():
    df.to_csv(f"{OUT_DIR}/{name}.csv", index=False)

summary_lines = []
summary_lines.append("MRR WATERFALL DATASET -- GENERATION SUMMARY (seed=42)")
summary_lines.append("=" * 60)
for name, df in tables.items():
    summary_lines.append(f"\n{name}.csv -- {len(df):,} rows, {len(df.columns)} columns")
    null_pct = (df.isna().mean() * 100).round(1)
    for col, pct in null_pct.items():
        if pct > 0:
            summary_lines.append(f"    {col}: {pct}% null")

summary_lines.append("\n" + "=" * 60)
summary_lines.append("KEY FIGURES")
summary_lines.append(f"  Cumulative logo churn (of 5,000 signed up in the window): {is_churned.mean():.1%}")
summary_lines.append(f"  Avg plan-history rows/customer: {len(subscriptions_df)/N_CUSTOMERS:.2f}")
summary_lines.append("  Plan mix: " + ", ".join(
    f"{k} {v:.1%}" for k, v in subscriptions_df['plan_name'].value_counts(normalize=True).items()
))
summary_lines.append("  Invoice status mix: " + ", ".join(
    f"{k} {v:.1%}" for k, v in invoices_df['invoice_status'].value_counts(normalize=True).items()
))

with open(f"{OUT_DIR}/generation_summary.txt", "w") as f:
    f.write("\n".join(summary_lines))

print("\n" + "\n".join(summary_lines))
print(f"\nCSV files + summary written to {OUT_DIR}")


