from pathlib import Path

import streamlit as st

LOGO_PATH = Path(__file__).parent / "assets" / "keycards_logo.png"

st.set_page_config(page_title="Credit Card Tools", page_icon="💳", layout="centered")
st.logo(str(LOGO_PATH))

st.image(str(LOGO_PATH), width=260)
st.title("Welcome to KEYCARDS!")

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

st.markdown("---")
st.markdown(
    "**Questions or feedback?** Reach out at [junwei.ye.sg@gmail.com](mailto:junwei.ye.sg@gmail.com)"
)
