import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="EB Bill Average Analyzer", layout="wide")

st.title("⚡ EB Bill Average Analyzer")
st.caption("Fast | Smart | Editable | Save Enabled")

# -------------------- Optimized Excel Loader --------------------
@st.cache_data(show_spinner="Loading Excel...")
def load_excel(file):
    df_raw = pd.read_excel(file, header=None)

    header_row = df_raw[df_raw.iloc[:,0].astype(str)
                        .str.contains("Bill Nature", na=False)].index

    if len(header_row) == 0:
        return None

    df = pd.read_excel(file, header=header_row[0])
    df.columns = df.columns.str.strip()

    df["Bill Date"] = pd.to_datetime(df["Bill Date"], errors="coerce")
    df["Bill Amount"] = pd.to_numeric(df["Bill Amount"], errors="coerce").fillna(0)
    df["SAP ID"] = df["SAP ID"].astype(str)

    df = df.dropna(subset=["Bill Date"])

    return df


# -------------------- Upload --------------------
uploaded = st.file_uploader("Upload SEB Bill Excel", type=["xlsx", "xls"])

if uploaded is None:
    st.info("📂 Upload Excel File")
    st.stop()

df = load_excel(uploaded)

if df is None:
    st.error("Header row not found in Excel")
    st.stop()

st.success(f"File Loaded Successfully | Rows: {len(df)}")

# -------------------- Site Selection --------------------
st.subheader("🏗 Select Site")

site = st.selectbox("Select SAP ID", sorted(df["SAP ID"].unique()))

site_df = df[df["SAP ID"] == site].copy()

# -------------------- Last 6M & 1Y Average --------------------
today = pd.Timestamp.today()

six_months = today - timedelta(days=180)
one_year = today - timedelta(days=365)

avg_6m = site_df[site_df["Bill Date"] >= six_months]["Bill Amount"].mean()
avg_1y = site_df[site_df["Bill Date"] >= one_year]["Bill Amount"].mean()

c1, c2 = st.columns(2)
c1.metric("📊 Average - Last 6 Months", f"₹ {avg_6m:,.0f}")
c2.metric("📊 Average - Last 1 Year", f"₹ {avg_1y:,.0f}")

# -------------------- Custom Date Selection --------------------
st.subheader("📅 Custom Date Range")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Start Date", today - timedelta(days=180))

with col2:
    end_date = st.date_input("End Date", today)

custom_df = site_df[
    (site_df["Bill Date"] >= pd.to_datetime(start_date)) &
    (site_df["Bill Date"] <= pd.to_datetime(end_date))
]

custom_avg = custom_df["Bill Amount"].mean()

st.metric("📌 Custom Period Average", f"₹ {custom_avg:,.0f}")

# -------------------- Editable Notes Section --------------------
st.subheader("📝 Notes Section (Excel Like Editable Table)")

if "notes_df" not in st.session_state:
    st.session_state.notes_df = pd.DataFrame({
        "SAP ID": [site],
        "Remark": [""],
        "Action Required": [""],
        "Priority": ["Medium"],
        "Follow-up Date": [pd.Timestamp.today().date()]
    })

notes_df = st.session_state.notes_df

edited_notes = st.data_editor(
    notes_df,
    num_rows="dynamic",
    use_container_width=True
)

# -------------------- Save Button --------------------
if st.button("💾 Save Notes"):
    st.session_state.notes_df = edited_notes
    st.success("Notes Saved Successfully")

# -------------------- Download Notes --------------------
st.subheader("⬇ Download Notes Report")

output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    edited_notes.to_excel(writer, index=False, sheet_name="Notes")

st.download_button(
    label="Download Notes Excel",
    data=output.getvalue(),
    file_name="EB_Bill_Notes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# -------------------- Display Filtered Data --------------------
st.subheader("📋 Selected Period Bills")

st.dataframe(custom_df[["Bill Date", "Bill Amount"]], width="stretch")