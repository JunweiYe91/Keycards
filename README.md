# Credit Card Recommender

A Streamlit app that recommends the top 3 credit cards (cashback or miles)
based on a user's spending habits, income eligibility, and card-specific
bonus rules (merchant partnerships, minimum spend, monthly caps).

## Project structure

```
credit_card_recommender/
├── Home.py                          # Entry point / homepage
├── pages/
│   └── 1_Credit_Card_Recommender.py # Recommender tool (shows in sidebar nav)
├── data_loader.py                   # Loads card_rates.xlsx / questions.xlsx
├── bucket_parser.py                 # Converts dropdown bucket labels -> $ values
├── scoring.py                       # Core reward calculation & ranking logic
├── requirements.txt
├── data/
│   ├── card_rates.xlsx   # One row per card (or per spend tier for tiered cards)
│   └── questions.xlsx    # Question text + dropdown response options
└── README.md
```

This uses Streamlit's built-in multipage app support: any file placed in
`pages/` automatically appears as a page in the sidebar, named after the
filename (numbers/underscores are formatted away — `1_Credit_Card_Recommender.py`
shows as "Credit Card Recommender"). To add a new tool later, just drop a
new `.py` file into `pages/` — no extra config needed. Number-prefix the
filename (e.g. `2_...py`) to control its order in the sidebar.

## How the recommendation logic works

1. **Card type preference (Q1)** — cards are ranked ONLY against others of
   the same type. Cashback cards are ranked in dollars; miles cards in
   miles. They are never compared against each other.
2. **Income eligibility (Q2/Q3)** — cards whose minimum income requirement
   exceeds the user's stated income bracket (using the bracket's lower
   bound, conservatively) are filtered out entirely.
3. **Merchant-specific bonuses** — some categories have a base rate column
   plus an "(Additional)" bonus column in `card_rates.xlsx`:
   - Groceries: all 5 partner stores trigger the additional bonus.
   - Ride-hailing: only "Grab" triggers `Grab` + `Grab (Additional)`;
     any other app (Gojek/Ryde/Tada/Others) uses the general `Transport` rate.
   - Online shopping: only "Shopee" triggers `Shopee` + `Shopee (Additional)`;
     any other platform (Lazada/Taobao/Others) uses `Online Spending`.
4. **Minimum spend / tiers** — a card only earns bonus rates if the user's
   total relevant monthly spend meets `Minimum Spending`; otherwise it
   falls back to the flat `Others` rate. Cards with multiple rows in
   `card_rates.xlsx` (e.g. UOB One Card) represent spend TIERS of the same
   card — the highest tier the user qualifies for is automatically selected.
5. **Caps** — `Total Cap` limits the combined base-rate reward per month;
   `Additional Cap` limits the combined bonus-rate reward per month.
6. **Travel & foreign spend** — collected as ANNUAL estimates (since travel
   is lumpy, not monthly) and scored directly against the annual rate,
   with the monthly cap approximated as an annual cap (`Total Cap x 12`).

## Updating the data

Both Excel files can be edited directly — no code changes needed as long as
column/question numbering stays consistent:
- Add/update cards by editing rows in `data/card_rates.xlsx`.
- Add tiers for a card by adding another row with the same
  `Credit Card Name` and a different `Minimum Spending` / rate combination.
- Question wording and dropdown option labels in `data/questions.xlsx` can
  be freely edited — the app renders whatever text/options are there.
  **Do not change the question numbering (`Ques No`)** — the app maps
  specific question numbers (1–16) to specific scoring logic.
- **Card images**: fill in the `Image URL` column in `card_rates.xlsx` with
  a direct link to each card's image (must end in `.png`/`.jpg`/etc. and be
  publicly accessible — hotlinking directly from bank websites often
  doesn't work due to hotlink protection, and reproducing bank card art
  may raise copyright/trademark concerns, so it's best to source images
  you have the rights to use, e.g. your own screenshots, or an official
  press kit). Leave a row blank and the app shows a placeholder image
  instead. For tiered cards (e.g. UOB One Card's 3 rows), only the row
  actually selected for the user's spend tier is shown, so it's simplest
  to put the same image URL on every tier row of that card.

## Running locally

```bash
pip install -r requirements.txt
streamlit run Home.py
```

The app defaults to light mode (set in `.streamlit/config.toml`). Users can
still switch to dark mode or "Use system setting" via the "⋮" menu in the
top-right corner → Settings.

## Deploying to Streamlit Community Cloud

1. Push this whole folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, and click "New app".
3. Select your repo, branch, and set the main file path to `Home.py`.
4. Click "Deploy" — Streamlit Cloud will install `requirements.txt`
   automatically and host the app at a public URL.

## Adding more pages later

Drop a new `.py` file into `pages/`, e.g. `pages/2_Credit_Card_Sentiments.py`.
It will automatically appear in the sidebar. It can import `data_loader`,
`bucket_parser`, and `scoring` the same way the recommender page does,
since they live at the project root.

## Known simplifications (documented, not bugs)

- Bucket ranges are converted to their midpoint (e.g. "100 to 199" -> 149.5)
  for reward calculations, and to their lower bound for income eligibility.
- "Others" spend (uncategorized) is not asked about and assumed to be $0.
- Miles are never converted to a dollar value — cashback and miles cards
  are ranked as two separate, non-comparable lists.
- Annual fees are not in the current `card_rates.xlsx`, so they're not
  netted out of the reward. Miles conversion fees ARE shown per card (as
  a flat $ note) but not subtracted from the miles total since they're a
  different unit.
