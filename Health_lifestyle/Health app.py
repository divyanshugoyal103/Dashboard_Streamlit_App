import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import gdown
import os

st.set_page_config(page_title="Health & Lifestyle Dashboard", layout="wide")

FILE_ID = "ydivyanshugoyal103@gmail.com"
FILE_NAME = "health_lifestyle_classification.csv"

@st.cache_data
def load_data():
    if not os.path.exists(FILE_NAME):
        url = f"https://drive.google.com/file/d/1IkBrsm7ekENjZWOTrODL8jdXJhRFcMJk/view?usp=drive_link"
        gdown.download(url, FILE_NAME, quiet=False)
    try:
        # Try reading normally first
        df = pd.read_csv(FILE_NAME)
    except pd.errors.ParserError:
        # If error, try skipping bad lines and explicitly set delimiter as comma
        df = pd.read_csv(FILE_NAME, sep=',', on_bad_lines='skip')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    with open(FILE_NAME, 'r', encoding='utf-8') as f:
        st.text("First 10 lines of your CSV file for inspection:")
        for _ in range(10):
            line = f.readline()
            st.text(line)
    st.stop()

with st.sidebar:
    selected = option_menu(
        "Dashboard Pages",
        ["Demographics & Target", "Health Metrics", "Lifestyle Factors", "Mental & Environmental"],
        icons=["person", "activity", "heart-pulse", "cloud"],
        menu_icon="bar-chart", default_index=0
    )

if selected == "Demographics & Target":
    st.title("Demographics & Target Distribution")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Age Distribution")
        fig = px.histogram(df, x='age', nbins=30, color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Gender Distribution")
        fig = px.pie(df, names='gender', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Target Class Distribution")
    fig = px.histogram(df, x='target', color='target', color_discrete_sequence=px.colors.qualitative.Vivid)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Health Classification by Gender")
    gender_target_ct = pd.crosstab(df['gender'], df['target'], normalize='index')
    st.dataframe(gender_target_ct.style.background_gradient(axis=1, cmap='viridis'), use_container_width=True)

elif selected == "Health Metrics":
    st.title("Health Metrics Overview")
    numeric_cols = ['bmi', 'waist_size', 'blood_pressure', 'heart_rate',
                    'cholesterol', 'glucose', 'insulin']

    selected_metric = st.selectbox("Select Health Metric", numeric_cols)
    fig = px.box(df, x='target', y=selected_metric, color='target')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Correlation Heatmap")
    corr = df[numeric_cols].corr()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', ax=ax)
    st.pyplot(fig)

elif selected == "Lifestyle Factors":
    st.title("Lifestyle Factors")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sleep Hours by Target")
        fig = px.box(df, x='target', y='sleep_hours', color='target')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Physical Activity vs Target")
        fig = px.box(df, x='target', y='physical_activity', color='target')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Daily Steps vs Target")
        fig = px.box(df, x='target', y='daily_steps', color='target')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Screen Time vs Target")
        fig = px.box(df, x='target', y='screen_time', color='target')
        st.plotly_chart(fig, use_container_width=True)

elif selected == "Mental & Environmental":
    st.title("Mental & Environmental Factors")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stress Level by Target")
        fig = px.box(df, x='target', y='stress_level', color='target')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Mental Health Score")
        fig = px.box(df, x='target', y='mental_health_score', color='target')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Environmental Risk Score")
        fig = px.box(df, x='target', y='environmental_risk_score', color='target')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Supplement Dosage")
        fig = px.box(df, x='target', y='daily_supplement_dosage', color='target')
        st.plotly_chart(fig, use_container_width=True)
