import streamlit as st

st.set_page_config(page_title="Credit Card Tools", page_icon="💳", layout="centered")

st.title("💳 Welcome!")

st.write(
    "This is your one-stop shop for credit card tools. Use the sidebar on the "
    "left to navigate between pages."
)

st.markdown(
    """
### What's available

- **Credit Card Recommender** — answer a few questions about your spending
  habits and get your top 3 best-fit cards (cashback or miles).

More tools will be added here over time.
"""
)

st.info("👈 Select a page from the sidebar to get started.")
