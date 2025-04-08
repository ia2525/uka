# indicators/production_index.py

import os
import pandas as pd

def load_company_and_industry_allocations():
    base_dir = os.path.dirname(__file__)
    excel_path = os.path.join(base_dir, "..", "data", "raw", "Timeseries_for_uk_ets_allocations_non-aviation.xlsx")

    company_allocations = pd.read_excel(excel_path, sheet_name="Timeseries - Company Allocation")
    industry_allocations = pd.read_excel(excel_path, sheet_name="Timeseries-Industry Allocations")

    return company_allocations, industry_allocations

def reshape_allocation_timeseries():
    company_df, industry_df = load_company_and_industry_allocations()

    top_companies_df = company_df.dropna(subset=["Company"]).iloc[:10]
    top_industries_df = industry_df.dropna(subset=["Industries"]).iloc[1:11]

    year_columns = [col for col in top_companies_df.columns if str(col).isdigit()]

    companies_long = top_companies_df.melt(
        id_vars="Company", value_vars=year_columns,
        var_name="Year", value_name="Allocation"
    )
    industries_long = top_industries_df.melt(
        id_vars="Industries", value_vars=year_columns,
        var_name="Year", value_name="Allocation"
    )

    companies_long["Year"] = companies_long["Year"].astype(str)
    industries_long["Year"] = industries_long["Year"].astype(str)

    return companies_long, industries_long