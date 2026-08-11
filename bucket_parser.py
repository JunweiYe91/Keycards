"""
Converts the dropdown bucket labels used in questions.xlsx (e.g. "100 to 199",
"Less than 100", "More than 600", "80,000 or more") into representative
numeric values for use in the scoring calculations.
"""

import re


def parse_bucket_midpoint(label: str) -> float:
    """Return a representative dollar (or income) value for a bucket label.

    - "Less than X"   -> X * 0.5
    - "X to Y" / "X - Y" -> midpoint of X and Y
    - "More than X" / "X or more" -> X * 1.15 (rough padding above the floor)
    """
    s = str(label).strip().replace(",", "")

    m = re.match(r"(?i)less than\s*([\d.]+)", s)
    if m:
        return float(m.group(1)) * 0.5

    m = re.match(r"(?i)more than\s*([\d.]+)", s)
    if m:
        return float(m.group(1)) * 1.15

    m = re.match(r"(?i)([\d.]+)\s*or more", s)
    if m:
        return float(m.group(1)) * 1.15

    m = re.match(r"(?i)([\d.]+)\s*(?:to|-)\s*([\d.]+)", s)
    if m:
        x, y = float(m.group(1)), float(m.group(2))
        return (x + y) / 2.0

    raise ValueError(f"Could not parse bucket label: {label!r}")


def parse_bucket_lower_bound(label: str) -> float:
    """Return the conservative lower bound of a bucket label.

    Used for income-eligibility checks, where we assume the user's income
    could be as low as the bottom of their selected bracket.
    """
    s = str(label).strip().replace(",", "")

    if re.match(r"(?i)less than\s*([\d.]+)", s):
        return 0.0

    m = re.match(r"(?i)more than\s*([\d.]+)", s)
    if m:
        return float(m.group(1))

    m = re.match(r"(?i)([\d.]+)\s*or more", s)
    if m:
        return float(m.group(1))

    m = re.match(r"(?i)([\d.]+)\s*(?:to|-)\s*([\d.]+)", s)
    if m:
        return float(m.group(1))

    raise ValueError(f"Could not parse bucket label: {label!r}")
