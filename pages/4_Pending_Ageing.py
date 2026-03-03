import streamlit as st
import pandas as pd
from utils.ageing_calculator import calculate_ageing

st.header("⏳ Pending Bill Ageing")

uploaded = st.file_uploader("Upload Bills", type=["xlsx"])

if uploaded:
    df = pd.read_excel(uploaded)
    df = calculate_ageing(df)

    pending = df[df['Payment Status'] == "Pending"]

    st.metric("Total Pending Bills", len(pending))

    st.dataframe(pending.sort_values(by="Ageing_Days", ascending=False))
