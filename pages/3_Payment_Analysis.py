import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SEB EB Bill KPI Dashboard", layout="wide")

# ---------------- Sidebar ---------------- #
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go To", ["Upload & Clean Data", "Pending KPI Dashboard"])

# ---------------- Session ---------------- #
if "clean_df" not in st.session_state:
    st.session_state.clean_df = None

# ---------------- Helper Functions ---------------- #
def fix_duplicate_columns(cols):
    seen = {}
    new_cols = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    return new_cols


def auto_detect_header(raw_df):
    for i in range(10):
        row = raw_df.iloc[i].astype(str).str.lower().tolist()
        if any("sap id" in x for x in row):
            return i
    return None


# ====================================================== #
#                      PAGE 1                            #
# ====================================================== #
if page == "Upload & Clean Data":

    st.title("📤 Upload & Clean SEB Excel")

    uploaded_file = st.file_uploader("Upload SEB Excel", type=["xlsx", "xls"])

    if uploaded_file:

        raw_df = pd.read_excel(uploaded_file, header=None)

        header_row = auto_detect_header(raw_df)

        if header_row is None:
            st.error("❌ Could not auto-detect header row.")
            st.dataframe(raw_df.head(15), width="stretch")
            st.stop()

        # Assign header
        raw_df.columns = raw_df.iloc[header_row]
        df = raw_df.iloc[header_row + 1:].reset_index(drop=True)

        # Clean column names
        df.columns = df.columns.astype(str).str.strip()

        # Fix duplicate columns
        df.columns = fix_duplicate_columns(df.columns.tolist())

        # Drop fully empty rows
        df = df.dropna(how="all")

        # Convert date columns
        date_cols = ["Created On", "Bill Date", "Due Date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Convert amount
        if "Current Amount" in df.columns:
            df["Current Amount"] = pd.to_numeric(df["Current Amount"], errors="coerce").fillna(0)

        st.success("✅ Excel Loaded, Header Fixed & Columns Cleaned")

        # Required columns check
        required_cols = ["SAP ID", "Bill No", "Created On", "Due Date", "Current Status", "Current Amount"]
        missing = [c for c in required_cols if c not in df.columns]

        if missing:
            st.error(f"❌ Missing Required Columns: {missing}")
            st.stop()

        # ---------------- KEY LOGIC ---------------- #
        # Sort newest → oldest
        df = df.sort_values("Created On", ascending=False)

        # Remove duplicates → keep newest bill only
        clean_df = df.drop_duplicates(subset=["SAP ID", "Bill No"], keep="first")

        # Now sort oldest → newest (final clean dataset)
        clean_df = clean_df.sort_values("Created On", ascending=True)

        st.session_state.clean_df = clean_df.copy()

        st.success("🔥 Duplicate Removal + Date Sorting Done")

        st.subheader("📄 Final Cleaned Dataset")
        st.dataframe(clean_df.head(50), width="stretch")

        # Download cleaned file
        clean_df.to_excel("cleaned_seb_output.xlsx", index=False)
        with open("cleaned_seb_output.xlsx", "rb") as f:
            st.download_button("⬇ Download Clean Excel", f, "cleaned_seb_output.xlsx")

# ====================================================== #
#                      PAGE 2                            #
# ====================================================== #
elif page == "Pending KPI Dashboard":

    st.title("📊 Pending Bill KPI & Ageing Dashboard")

    if st.session_state.clean_df is None:
        st.warning("⚠ Please upload & clean Excel first")
        st.stop()

    df = st.session_state.clean_df.copy()
    today = datetime.today()

    # Pending filter
    pending_df = df[df["Current Status"].astype(str).str.contains("PEND", case=False, na=False)]

    if pending_df.empty:
        st.warning("No Pending Bills Found")
        st.stop()

    # Ageing calculation
    pending_df["Ageing Days"] = (today - pending_df["Due Date"]).dt.days
    pending_df["Ageing Days"] = pending_df["Ageing Days"].fillna(0).astype(int)

    # KPIs
    total_pending = pending_df.shape[0]
    total_amount = pending_df["Current Amount"].sum()
    max_ageing = pending_df["Ageing Days"].max()
    avg_ageing = int(pending_df["Ageing Days"].mean())
    last_bill_date = pending_df["Bill Date"].max()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pending Bills", total_pending)
    c2.metric("Total Pending Amount (₹)", f"{total_amount:,.0f}")
    c3.metric("Max Ageing (Days)", max_ageing)
    c4.metric("Last Bill Date", last_bill_date.strftime("%d-%m-%Y") if pd.notna(last_bill_date) else "N/A")

    st.divider()

    # Ageing Buckets
    bins = [-999, 0, 15, 30, 60, 90, 99999]
    labels = ["Not Due", "1–15", "16–30", "31–60", "61–90", "90+"]
    pending_df["Ageing Bucket"] = pd.cut(pending_df["Ageing Days"], bins=bins, labels=labels)

    st.subheader("📊 Ageing Bucket Summary")
    bucket_summary = pending_df.groupby("Ageing Bucket")["Current Amount"].sum().reset_index()
    st.dataframe(bucket_summary, width="stretch")

    st.divider()

    # Site-wise summary
    st.subheader("🏭 Site-wise Pending Summary")
    site_summary = pending_df.groupby("SAP ID").agg(
        Total_Pending_Amount=("Current Amount", "sum"),
        Total_Bills=("Bill No", "count"),
        Max_Ageing=("Ageing Days", "max"),
        Last_Bill_Date=("Bill Date", "max")
    ).reset_index()

    st.dataframe(site_summary, width="stretch")

    st.divider()

    # Last 10 Pending Bills (Newest First)
    st.subheader("🕒 Last 10 Pending Bills (Newest First)")

    last_10_pending = pending_df.sort_values("Created On", ascending=False).head(10)

    show_cols = ["SAP ID", "Bill No", "Bill Date", "Due Date", 
                 "Current Amount", "Ageing Days", "Current Status"]

    show_cols = [c for c in show_cols if c in last_10_pending.columns]

    st.dataframe(last_10_pending[show_cols], width="stretch")

