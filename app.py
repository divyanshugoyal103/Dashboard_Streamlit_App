import streamlit as st
import plotly.express as px
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

        if not num_cols or not cat_cols:
            st.warning("⚠️ Not enough numeric or categorical data to plot.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader(f"Box Plot: {num_cols[0]} by {cat_cols[0]}")
                try:
                    fig1 = px.box(df, x=cat_cols[0], y=num_cols[0], points="all")
                    st.plotly_chart(fig1, use_container_width=True)
                except Exception as e:
                    st.error(f"Box Plot failed: {e}")

            with col2:
                st.subheader(f"Histogram: {num_cols[0]}")
                try:
                    fig2 = px.histogram(df, x=num_cols[0])
                    st.plotly_chart(fig2, use_container_width=True)
                except Exception as e:
                    st.error(f"Histogram failed: {e}")

            st.markdown("---")
            st.subheader("📈 Additional Insights")
            st.write(df.describe())
else:
    st.info("Please upload a CSV file to begin.")
