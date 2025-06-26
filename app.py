import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_csv, get_column_types

st.set_page_config(page_title="Descriptive Data Dashboard", layout="wide")
st.title("📊 Descriptive Data Dashboard")

uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

if uploaded_file:
    df, error = load_csv(uploaded_file)

    if error:
        st.error(f"❌ Failed to load file: {error}")
    elif df.empty:
        st.warning("⚠️ Uploaded file is empty.")
    else:
        st.success("✅ File uploaded successfully.")
        st.dataframe(df.head())

        num_cols, cat_cols = get_column_types(df)
        date_cols = df.select_dtypes(include='datetime').columns.tolist()

        with st.sidebar:
            st.header("🛠️ Controls")

            if num_cols:
                num_col = st.selectbox("Select a Numeric Column", num_cols)
            else:
                num_col = None

            if cat_cols:
                cat_col = st.selectbox("Select a Categorical Column", cat_cols)
            else:
                cat_col = None

            if date_cols:
                date_col = st.selectbox("Select Date Column for Time Series", date_cols)
            else:
                date_col = None

        tab1, tab2, tab3 = st.tabs(["📦 Box & Histogram", "📈 Time Series", "📋 Summary"])

        with tab1:
            col1, col2 = st.columns(2)
            if cat_col and num_col:
                with col1:
                    try:
                        st.subheader(f"Box Plot: {num_col} by {cat_col}")
                        fig1 = px.box(df, x=cat_col, y=num_col, points="all")
                        st.plotly_chart(fig1, use_container_width=True)
                    except Exception as e:
                        st.error(f"Box plot failed: {e}")
                with col2:
                    try:
                        st.subheader(f"Histogram: {num_col}")
                        fig2 = px.histogram(df, x=num_col)
                        st.plotly_chart(fig2, use_container_width=True)
                    except Exception as e:
                        st.error(f"Histogram failed: {e}")
            else:
                st.warning("Please select valid numeric and categorical columns.")

        with tab2:
            if date_col and num_col:
                try:
                    df_sorted = df.sort_values(by=date_col)
                    fig3 = px.line(df_sorted, x=date_col, y=num_col, title=f"Time Series of {num_col}")
                    st.plotly_chart(fig3, use_container_width=True)
                except Exception as e:
                    st.error(f"Time series failed: {e}")
            else:
                st.info("To view a time series, select a datetime column and a numeric column.")

        with tab3:
            st.subheader("Descriptive Statistics")
            st.write(df.describe())
