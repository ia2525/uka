import pandas as pd
import streamlit as st

def fetch_industrial_production_index_from_csv():
    file_path = "data/raw/diop.csv"
    
    # Read the raw CSV, skipping metadata
    df_raw = pd.read_csv(file_path, skiprows=163)

    # Dynamically detect first column (assumed to be industry name)
    first_col = df_raw.columns[0]
    
    # Identify quarterly date columns (e.g., "2023 Q1")
    date_cols = [col for col in df_raw.columns if pd.Series(col).str.match(r"^\d{4} Q[1-4]$").any()]
    
    # Trim and rename
    df_trimmed = df_raw[[first_col] + date_cols].copy()
    df_trimmed = df_trimmed.rename(columns={first_col: "industry"})
    df_trimmed["industry"] = df_trimmed["industry"].astype(str).apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Transpose the DataFrame to have dates as rows
    df_transposed = df_trimmed.set_index("industry").T.reset_index()
    df_transposed = df_transposed.rename(columns={"index": "date"})

    # Convert "date" column to datetime using quarter format
    df_transposed["year"] = df_transposed["date"].str.extract(r"(\d{4})").astype(int)
    df_transposed["quarter"] = df_transposed["date"].str.extract(r"(Q[1-4])")
    quarter_to_month = {"Q1": 1, "Q2": 4, "Q3": 7, "Q4": 10}
    df_transposed["month"] = df_transposed["quarter"].map(quarter_to_month)
    df_transposed["date"] = pd.to_datetime(
        df_transposed[["year", "month"]].assign(day=1)
    )
    df_transposed = df_transposed.drop(columns=["year", "quarter", "month"])

    # Show what columns were found (debug)
    st.write("📋 Available industry columns:", df_transposed.columns.tolist())

    # Select only high-emission industries
    high_emission_industries = [
        "Manufacturing",
        "Electricity, gas, steam and air conditioning supply",
        "Coke and refined petroleum products",
        "Chemical and chemical products",
        "Basic metals"
    ]

    # Filter to valid columns
    valid_cols = ["date"] + [col for col in df_transposed.columns if col in high_emission_industries]
    df_filtered = df_transposed[valid_cols]

    if len(valid_cols) <= 1:
        st.error("⚠️ No matching high-emission industries found in CSV. Check column headers.")
        return pd.DataFrame()

    # Limit to last 12 months
    df_filtered = df_filtered[df_filtered["date"] >= pd.Timestamp.now() - pd.DateOffset(months=12)]

    return df_filtered