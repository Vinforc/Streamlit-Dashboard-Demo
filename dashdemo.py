# analytics_demos.py

import pandas as pd
import streamlit as st
import altair as alt
import numpy as np
from datetime import datetime, timedelta
import uuid
import os

# Generate all datasets
restaurant_df = pd.read_csv("Restaurant_Sales_Data.csv")
construction_df = pd.read_csv("Construction_Jobs_Data.csv")
real_estate_df = pd.read_csv("Real_Estate_Listings_Data.csv")


# Streamlit layout
st.set_page_config(page_title="SMB Analytics Demo", layout="wide")
st.title("📊 Analytics Demos")

# Tabs for each business type
tabs = st.tabs(["Restaurant Chain", "Construction Services", "Real Estate Team"])

# --- Restaurant Dashboard ---
with tabs[0]:
    st.header("🍔 Restaurant Chain Dashboard")
    location_filter = st.selectbox("Select Location", ["All"] + restaurant_df["location"].unique().tolist())
    filtered = restaurant_df if location_filter == "All" else restaurant_df[restaurant_df["location"] == location_filter]

    st.subheader("🍽️ Key Performance Indicators")

    total_orders = len(filtered)
    total_sales = filtered["total_sales"].sum()
    avg_order_value = filtered["total_sales"].mean()
    avg_labor_pct = (filtered["labor_cost"] / filtered["total_sales"]).clip(upper=1).mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🧾 Total Orders", total_orders)
    col2.metric("💵 Total Sales", f"${total_sales:,.0f}")
    col3.metric("📊 Avg Order Value", f"${avg_order_value:,.2f}")
    col4.metric("👷 Avg Labor %", f"{avg_labor_pct:.1f}%")

    st.subheader("Sales Overview")
    daily_sales = filtered.groupby("date")["total_sales"].sum().reset_index()
    st.altair_chart(alt.Chart(daily_sales).mark_line().encode(x="date:T", y="total_sales:Q"), use_container_width=True)

    st.subheader("Top-Selling Items")
    # Summarize data
    top_items = (
        filtered.groupby("item")
        .agg(quantity=("quantity", "sum"), revenue=("total_sales", "sum"))
        .reset_index()
        .sort_values("quantity", ascending=False)
    )
    # Altair bar chart with tooltip
    chart = alt.Chart(top_items).mark_bar().encode(
        x=alt.X("item:N", sort="-y"),
        y="quantity:Q",
        tooltip=["item:N", "quantity:Q", alt.Tooltip("revenue:Q", format="$,.2f")],
        color = alt.Color("category:N", scale=alt.Scale(scheme="tableau10"))
    ).properties(width=600)
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Labor Cost Ratio")
    ratio_df = filtered.copy()
    ratio_df["labor_pct"] = (ratio_df["labor_cost"] / ratio_df["total_sales"]).clip(upper=1.0)
    st.line_chart(ratio_df.groupby("date")["labor_pct"].mean())

# --- Construction Dashboard ---
with tabs[1]:
    st.header("🏗️ Construction Services Dashboard")
    # Filter
    stage_filter = st.multiselect(
        "Filter by Stage",
        construction_df["stage"].unique(),
        default=construction_df["stage"].unique()
    )
    filtered = construction_df[construction_df["stage"].isin(stage_filter)].copy()
    filtered["profit"] = filtered["revenue"] - filtered["labor_cost"] - filtered["material_cost"]

    st.subheader("📐 Key Performance Indicators")

    total_jobs = len(filtered)
    completed_jobs = len(filtered[filtered["stage"] == "Completed"])
    total_revenue = filtered["revenue"].sum()
    avg_profit = (filtered["revenue"] - filtered["labor_cost"] - filtered["material_cost"]).mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🧾 Total Jobs", total_jobs)
    col2.metric("✅ Completed Jobs", completed_jobs)
    col3.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
    col4.metric("📈 Avg Job Profit", f"${avg_profit:,.0f}")


    # Revenue Chart
    st.subheader("Revenue by Job Type")
    revenue_summary = filtered.groupby("job_type")["revenue"].sum().reset_index()
    # Altair bar chart with distinct colors
    chart = alt.Chart(revenue_summary).mark_bar().encode(
        x=alt.X("job_type:N", sort="-y"),
        y=alt.Y("revenue:Q"),
        color="job_type:N",
        tooltip=["job_type:N", alt.Tooltip("revenue:Q", format="$,.2f")]
    )
    st.altair_chart(chart, use_container_width=True)

    # Split Tables
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Job Profitability")
        st.dataframe(
            filtered[["job_id", "job_type", "stage", "profit"]]
            .sort_values("profit", ascending=False)
        )
    with col2:
        st.subheader("Active Job Aging")
        active_jobs = filtered[filtered["stage"] != "Completed"].copy()
        active_jobs["age_days"] = (
            pd.to_datetime("today") - pd.to_datetime(active_jobs["start_date"])
        ).dt.days
        st.dataframe(
            active_jobs[["job_id", "stage", "start_date", "age_days"]]
            .sort_values("age_days", ascending=False)
        )

# --- Real Estate Dashboard ---
with tabs[2]:
    st.header("🏘️ Real Estate Team Dashboard")
    stage_filter = st.radio("Filter by Stage", ["All"] + real_estate_df["stage"].unique().tolist(), horizontal=True)
    filtered = real_estate_df if stage_filter == "All" else real_estate_df[real_estate_df["stage"] == stage_filter]

    st.subheader("🏡 Key Performance Indicators")
    # Filtered data assumed to be: filtered = real_estate_df[...]
    total_listings = len(filtered)
    total_commission = filtered["commission"].sum()
    avg_price = filtered["listing_price"].mean()
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Total Listings", total_listings)
    col2.metric("🏷️ Avg Listing Price", f"${avg_price:,.0f}")
    col3.metric("💰 Total Commission", f"${total_commission:,.2f}")

    st.subheader("Pipeline Stage Breakdown")
    # Prepare data
    stage_counts = real_estate_df["stage"].value_counts().reset_index()
    stage_counts.columns = ["stage", "count"]
    # Altair bar chart with distinct colors
    chart = alt.Chart(stage_counts).mark_bar().encode(
        x=alt.X("stage:N", sort="-y"),
        y=alt.Y("count:Q"),
        color="stage:N",
        tooltip=["stage:N", "count:Q"]
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Commissions by Agent")
    # Prepare data
    commission_data = real_estate_df.groupby("agent")["commission"].sum().reset_index()
    # Altair bar chart with distinct colors
    chart = alt.Chart(commission_data).mark_bar().encode(
        x=alt.X("agent:N", sort="-y"),
        y=alt.Y("commission:Q"),
        color="agent:N",
        tooltip=["agent:N", alt.Tooltip("commission:Q", format="$,.2f")]
    )
    st.altair_chart(chart, use_container_width=True)
    
    st.subheader("Lead Source Distribution")
    # Fix column names
    source_dist = real_estate_df["lead_source"].value_counts().reset_index()
    source_dist.columns = ["source", "count"]
    # Altair pie chart
    chart = alt.Chart(source_dist).mark_arc().encode(
        theta="count:Q",
        color="source:N",
        tooltip=["source:N", "count:Q"]
    )
    st.altair_chart(chart, use_container_width=True)
