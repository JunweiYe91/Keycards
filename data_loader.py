"""
Loads card_rates.xlsx and questions.xlsx from the data/ folder and exposes
small helpers for the app to pull question text/options by question number.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

NUMERIC_RATE_COLUMNS = [
    "Singaporean/PR Minimum Income",
    "Non-Singaporean Minimum Income",
    "Petrol",
    "Transport",
    "Dining",
    "Groceries",
    "Groceries (Additional)",
    "Flights and Hotel (Local)",
    "Flights and Hotel (Foreign)",
    "Foreign Spend",
    "Online Spending",
    "Grab",
    "Grab (Additional)",
    "Shopee",
    "Shopee (Additional)",
    "Others",
    "Minimum Spending",
    "Total Cap",
    "Additional Cap",
    "Conversion Fees",
]

# Not a rate — passed through as-is (text), used to display card art.
IMAGE_COLUMN = "Image URL"


def load_card_rates(path: Optional[Path] = None) -> pd.DataFrame:
    path = path or DATA_DIR / "card_rates.xlsx"
    df = pd.read_excel(path)
    for col in NUMERIC_RATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def load_questions(path: Optional[Path] = None) -> pd.DataFrame:
    path = path or DATA_DIR / "questions.xlsx"
    df = pd.read_excel(path)
    df = df.dropna(subset=["Ques No"]).reset_index(drop=True)
    df["Ques No"] = df["Ques No"].astype(int)
    return df


def get_question(questions_df: pd.DataFrame, ques_no: int):
    """Return (question_text, [options...]) for a given question number."""
    row = questions_df.loc[questions_df["Ques No"] == ques_no].iloc[0]
    text = row["Questions"]
    option_cols = [f"Response {i}" for i in range(1, 8)]
    options = [row[c] for c in option_cols if c in row and pd.notna(row[c])]
    return text, options
