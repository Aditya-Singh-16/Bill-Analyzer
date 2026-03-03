import streamlit as st
import pandas as pd

st.set_page_config(page_title="Excel Auto Merge Tool", layout="wide")

st.title("📊 SEB Excel Auto Merge & Balance Summary Tool")

st.markdown("### Upload 3 Excel Files")

file1 = st.file_uploader("Upload Excel 1 (Source Data)", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload Excel 2 (Source Data)", type=["xlsx", "xls"])
file3 = st.file_uploader("Upload Excel 3 (Master Sheet)", type=["xlsx", "xls"])

if file1 and file2 and file3:

    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)
    df3 = pd.read_excel(file3)

    # Clean column names
    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()
    df3.columns = df3.columns.str.strip()

    key_col = "Rjio Site Id"

    required_cols = [
        "Created On",
        "Period To",
        "ClosingReading",
        "SAP Posting Date",
        "Current Status",
        "remarks2"
    ]

    # Check column availability
    missing1 = [c for c in [key_col] + required_cols if c not in df1.columns]
    missing2 = [c for c in [key_col] + required_cols if c not in df2.columns]
    missing3 = [key_col] if key_col not in df3.columns else []

    if missing1:
        st.error(f"Excel 1 Missing Columns: {missing1}")
    if missing2:
        st.error(f"Excel 2 Missing Columns: {missing2}")
    if missing3:
        st.error(f"Excel 3 Missing Columns: {missing3}")

    if not missing1 and not missing2 and not missing3:

        # Convert Created On to datetime
        df1["Created On"] = pd.to_datetime(df1["Created On"], errors="coerce")
        df2["Created On"] = pd.to_datetime(df2["Created On"], errors="coerce")

        # Pick latest record per site
        df1_latest = df1.sort_values("Created On").groupby(key_col).last().reset_index()
        df2_latest = df2.sort_values("Created On").groupby(key_col).last().reset_index()

        # Combine both sheets
        combined = pd.concat([df1_latest, df2_latest], ignore_index=True)

        final_latest = combined.sort_values("Created On").groupby(key_col).last().reset_index()

        # Merge into master sheet
        final_df = df3.merge(
            final_latest[[key_col] + required_cols],
            on=key_col,
            how="left"
        )

        st.success("✅ Merge Completed Successfully")

        st.subheader("📄 Final Output Preview")
        st.dataframe(final_df, width="stretch")

        # Download button
        output_file = "Final_SEB_Merged_Output.xlsx"
        final_df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                "⬇ Download Final Excel File",
                f,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
