"""
Core reward-calculation and ranking logic.

Key rules encoded here (agreed with the user):
- Cashback cards are ranked in dollars; Miles cards are ranked in miles.
  They are NEVER mixed/compared against each other — the user picks a
  preference up front (Q1) and we only rank cards of that type.
- Merchant-specific bonus = base rate column + "(Additional)" rate column,
  e.g. Shopee spend uses "Shopee" + "Shopee (Additional)".
  - Groceries: ALL 5 partner stores trigger the additional bonus.
  - Grab: only the "Grab" ride-hailing option triggers Grab + Grab (Additional).
    Any other ride-hailing app falls back to the general "Transport" rate.
  - Shopee: only the "Shopee" platform triggers Shopee + Shopee (Additional).
    Any other platform falls back to the general "Online Spending" rate.
- "Minimum Spending" must be met (based on total monthly relevant spend)
  for a card to earn ANY bonus rate; otherwise it falls back to the
  "Others" rate on total spend.
- "Total Cap" caps the combined BASE-rate reward per month.
  "Additional Cap" caps the combined ADDITIONAL-rate reward per month.
- Some cards (e.g. UOB One Card) have multiple rows representing spend
  TIERS of the same card. We pick the highest tier the user's total
  monthly spend qualifies for.
- Flights/Hotels and Foreign Spend are lumpy, so they're collected as
  ANNUAL estimates and scored directly against the annual figure. The
  monthly Total Cap is approximated as an annual cap (Total Cap x 12)
  applied to this travel portion independently of the monthly categories.
- Income eligibility: cards whose minimum income requirement exceeds the
  user's income are filtered out entirely.
"""

import pandas as pd

ADDITIONAL_RATE_COLUMNS = {
    "Groceries": "Groceries (Additional)",
    "Grab": "Grab (Additional)",
    "Shopee": "Shopee (Additional)",
}

TRAVEL_RATE_COLUMNS = [
    "Flights and Hotel (Local)",
    "Flights and Hotel (Foreign)",
    "Foreign Spend",
]


def select_card_tier(card_group: pd.DataFrame, total_monthly_spend: float) -> pd.Series:
    """For cards with multiple tiered rows, pick the highest tier the user's
    spend qualifies for. Falls back to the lowest tier if none qualify
    (compute_annual_reward will then correctly apply the "Others" fallback
    since the minimum spend for even that tier won't be met)."""
    eligible = card_group[card_group["Minimum Spending"] <= total_monthly_spend]
    if not eligible.empty:
        return eligible.sort_values("Minimum Spending", ascending=False).iloc[0]
    return card_group.sort_values("Minimum Spending").iloc[0]


def build_category_spend(profile: dict) -> dict:
    """Translate the raw questionnaire answers into the exact spend amount
    that should be multiplied against each Card_Rates rate column."""
    is_grab = profile["ride_hailing_app"] == "Grab"
    is_shopee = profile["online_platform"] == "Shopee"

    grab_spend = profile["ride_hailing_spend"] if is_grab else 0.0
    transport_effective = profile["transport_spend"] + (
        0.0 if is_grab else profile["ride_hailing_spend"]
    )
    shopee_spend = profile["online_spend"] if is_shopee else 0.0
    online_other_spend = 0.0 if is_shopee else profile["online_spend"]

    return {
        "Petrol": profile["petrol_spend"],
        "Transport": transport_effective,
        "Dining": profile["dining_spend"],
        "Groceries": profile["grocery_spend"],
        "Grab": grab_spend,
        "Online Spending": online_other_spend,
        "Shopee": shopee_spend,
    }


def compute_annual_reward(card: pd.Series, profile: dict) -> dict:
    category_spend = build_category_spend(profile)
    total_monthly_spend = sum(category_spend.values())
    min_spend_required = float(card.get("Minimum Spending", 0) or 0)

    qualifies = total_monthly_spend >= min_spend_required

    if qualifies:
        base_reward = sum(spend * float(card[col]) for col, spend in category_spend.items())
        additional_reward = sum(
            category_spend[base_col] * float(card[add_col])
            for base_col, add_col in ADDITIONAL_RATE_COLUMNS.items()
        )

        total_cap = float(card.get("Total Cap", 0) or 0)
        additional_cap = float(card.get("Additional Cap", 0) or 0)

        if total_cap > 0:
            base_reward = min(base_reward, total_cap)
        if additional_cap > 0:
            additional_reward = min(additional_reward, additional_cap)

        monthly_reward = base_reward + additional_reward
    else:
        monthly_reward = total_monthly_spend * float(card.get("Others", 0) or 0)

    annual_recurring_reward = monthly_reward * 12.0

    # Lumpy annual categories: travel + foreign spend
    travel_spend = {
        "Flights and Hotel (Local)": profile["flights_local_annual"],
        "Flights and Hotel (Foreign)": profile["flights_foreign_annual"],
        "Foreign Spend": profile["foreign_spend_annual"],
    }
    travel_reward_raw = sum(spend * float(card[col]) for col, spend in travel_spend.items())

    annual_total_cap = float(card.get("Total Cap", 0) or 0) * 12.0
    travel_reward = (
        min(travel_reward_raw, annual_total_cap) if annual_total_cap > 0 else travel_reward_raw
    )

    annual_total_reward = annual_recurring_reward + travel_reward

    image_url = card.get("Image URL", "")
    image_url = "" if pd.isna(image_url) else str(image_url).strip()

    return {
        "card_name": card["Credit Card Name"],
        "card_type": card["Card Type"],
        "image_url": image_url,
        "monthly_reward": monthly_reward,
        "annual_recurring_reward": annual_recurring_reward,
        "travel_reward": travel_reward,
        "annual_total_reward": annual_total_reward,
        "qualifies_for_bonus": qualifies,
        "total_monthly_spend": total_monthly_spend,
        "conversion_fee": float(card.get("Conversion Fees", 0) or 0),
    }


def is_income_eligible(card: pd.Series, singaporean: str, income_lower_bound: float) -> bool:
    col = (
        "Singaporean/PR Minimum Income"
        if singaporean == "Yes"
        else "Non-Singaporean Minimum Income"
    )
    min_income = float(card.get(col, 0) or 0)
    return income_lower_bound >= min_income


def recommend_cards(card_rates: pd.DataFrame, profile: dict, top_n: int = 3):
    category_spend = build_category_spend(profile)
    total_monthly_spend = sum(category_spend.values())

    results = []
    for _, group in card_rates.groupby("Credit Card Name", sort=False):
        card = select_card_tier(group, total_monthly_spend)

        if str(card["Card Type"]).strip().lower() != profile["card_type_pref"].strip().lower():
            continue
        if not is_income_eligible(card, profile["singaporean"], profile["income_lower_bound"]):
            continue

        results.append(compute_annual_reward(card, profile))

    results.sort(key=lambda r: r["annual_total_reward"], reverse=True)
    return results[:top_n]
