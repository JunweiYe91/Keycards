from pathlib import Path

import streamlit as st

from bucket_parser import parse_bucket_lower_bound, parse_bucket_midpoint
from data_loader import get_question, load_card_rates, load_questions
from scoring import recommend_cards

LOGO_PATH = Path(__file__).parent.parent / "assets" / "keycards_logo.png"

st.set_page_config(page_title="Credit Card Recommender", page_icon="💳", layout="centered")
st.logo(str(LOGO_PATH))

st.title("💳 Credit Card Recommender")
st.write(
    "Answer a few questions about your spending habits, and we'll estimate "
    "which cards would earn you the most rewards."
)


@st.cache_data
def get_data():
    return load_card_rates(), load_questions()


card_rates, questions = get_data()


def q(ques_no: int):
    return get_question(questions, ques_no)


with st.form("card_form"):
    st.subheader("About you")
    text, options = q(1)
    card_type_pref = st.selectbox(text, options)

    text, options = q(2)
    singaporean = st.selectbox(text, options)

    text, options = q(3)
    income_bracket = st.selectbox(text, options)

    st.subheader("Petrol")
    text, options = q(4)
    st.selectbox(text, options)  # informational only — no brand-specific rates yet

    text, options = q(5)
    petrol_bracket = st.selectbox(text, options)

    st.subheader("Public transport")
    text, options = q(6)
    transport_bracket = st.selectbox(text, options)

    st.subheader("Dining")
    text, options = q(7)
    dining_bracket = st.selectbox(text, options)

    st.subheader("Groceries")
    text, options = q(8)
    st.selectbox(text, options)  # informational — all 5 stores qualify for the bonus

    text, options = q(9)
    grocery_bracket = st.selectbox(text, options)

    st.subheader("Ride-hailing")
    text, options = q(10)
    ride_hailing_app = st.selectbox(text, options)

    text, options = q(11)
    ride_hailing_bracket = st.selectbox(text, options)

    st.subheader("Online shopping")
    text, options = q(12)
    online_platform = st.selectbox(text, options)

    text, options = q(13)
    online_bracket = st.selectbox(text, options)

    st.subheader("Travel & overseas spend (yearly estimate)")
    text, options = q(14)
    flights_local_bracket = st.selectbox(text, options)

    text, options = q(15)
    flights_foreign_bracket = st.selectbox(text, options)

    text, options = q(16)
    foreign_spend_bracket = st.selectbox(text, options)

    submitted = st.form_submit_button("Find my best cards")

if submitted:
    profile = {
        "card_type_pref": card_type_pref,
        "singaporean": singaporean,
        "income_lower_bound": parse_bucket_lower_bound(income_bracket),
        "petrol_spend": parse_bucket_midpoint(petrol_bracket),
        "transport_spend": parse_bucket_midpoint(transport_bracket),
        "dining_spend": parse_bucket_midpoint(dining_bracket),
        "grocery_spend": parse_bucket_midpoint(grocery_bracket),
        "ride_hailing_app": ride_hailing_app,
        "ride_hailing_spend": parse_bucket_midpoint(ride_hailing_bracket),
        "online_platform": online_platform,
        "online_spend": parse_bucket_midpoint(online_bracket),
        "flights_local_annual": parse_bucket_midpoint(flights_local_bracket),
        "flights_foreign_annual": parse_bucket_midpoint(flights_foreign_bracket),
        "foreign_spend_annual": parse_bucket_midpoint(foreign_spend_bracket),
    }

    top_cards = recommend_cards(card_rates, profile, top_n=3)

    st.subheader("🏆 Your top matches")

    if not top_cards:
        st.warning(
            "No cards matched your income eligibility and card-type preference. "
            "Try adjusting your answers."
        )
    else:
        is_cashback = profile["card_type_pref"].strip().lower() == "cashback"

        for i, result in enumerate(top_cards, 1):
            if is_cashback:
                value_label = f"${result['annual_total_reward']:,.0f} / year"
            else:
                value_label = f"{result['annual_total_reward']:,.0f} miles / year"

            st.metric(label=f"#{i}  {result['card_name']}", value=value_label)

            with st.expander("See breakdown"):
                st.write(f"Estimated total monthly spend: ${result['total_monthly_spend']:,.0f}")
                st.write(
                    "Qualifies for bonus rates: "
                    + ("✅ Yes" if result["qualifies_for_bonus"] else "❌ No — below minimum spend, base rate only")
                )
                if is_cashback:
                    st.write(f"Recurring reward (annualized): ${result['annual_recurring_reward']:,.2f}")
                    st.write(f"Travel & overseas reward (annual): ${result['travel_reward']:,.2f}")
                else:
                    st.write(f"Recurring reward (annualized): {result['annual_recurring_reward']:,.0f} miles")
                    st.write(f"Travel & overseas reward (annual): {result['travel_reward']:,.0f} miles")
                    if result["conversion_fee"] > 0:
                        st.write(f"Note: this card charges a ${result['conversion_fee']:,.0f} miles conversion fee.")

        st.caption(
            "Estimates use the midpoint of your selected spending brackets against each "
            "card's published rates, minimum spend requirements, and monthly caps. "
            "Actual rewards may vary — always check the issuer's terms."
        )
