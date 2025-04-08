import os
import pandas as pd
import streamlit as st
import plotly.express as px

base_dir = os.path.dirname(__file__)
excel_path = os.path.join(base_dir, "..", "data", "raw", "Timeseries_for_uk_ets_allocations_non-aviation.xlsx")

company_allocations = pd.read_excel(excel_path, sheet_name="Timeseries - Company Allocation")
industry_allocations = pd.read_excel(excel_path, sheet_name="Timeseries-Industry Allocations")

print(company_allocations.head())
print(industry_allocations.head())

# Clean and select top 10 companies
top_companies_df = company_allocations.dropna(subset=["Company"]).iloc[:10]

# Clean and select top 10 industries (skip total row at top)
top_industries_df = industry_allocations.dropna(subset=["Industries"]).iloc[1:11]

# Identify year columns (you can also manually list them if needed)
year_columns = [col for col in top_companies_df.columns if str(col).isdigit()]

# Reshape companies
companies_long = top_companies_df.melt(
    id_vars="Company", 
    value_vars=year_columns, 
    var_name="Year", 
    value_name="Allocation"
)

# Reshape industries
industries_long = top_industries_df.melt(
    id_vars="Industries", 
    value_vars=year_columns, 
    var_name="Year", 
    value_name="Allocation"
)

#Plotting the charts
st.header("UKA Allocation Time Series")

st.subheader("Top 10 Companies")
fig1 = px.line(
    companies_long, 
    x="Year", y="Allocation", color="Company",
    title="Top 10 UKA Allocation Recipients – Companies"
)
st.plotly_chart(fig1)

st.subheader("Top 10 Industries")
fig2 = px.line(
    industries_long, 
    x="Year", y="Allocation", color="Industries",
    title="Top 10 UKA Allocation Recipients – Industries"
)
st.plotly_chart(fig2)