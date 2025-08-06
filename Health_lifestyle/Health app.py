import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import gzip
import io

# Set Streamlit page settings
st.set_page_config(page_title="Health & Lifestyle Dashboard", layout="wide")

@st.cache_data
def load_data_from_github_raw(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise error if download failed
    compressed_file = io.BytesIO(response.content)
    with gzip.open(compressed_file, 'rt') as f:
        df = pd.read_csv(f)
    return df

# Replace this with your actual GitHub raw URL of the .csv.gz file
GITHUB_RAW_URL = "https://raw.githubusercontent.com/divyanshugoyal103/Dashboard_Streamlit_App/f1da5750a69df6c4b8b691987d60b621fc9a411c/Health_lifestyle/health_lifestyle_classification.csv.gz
"

# Load data
df = load_data_from_github_raw(GITHUB_RAW_URL)

# Sidebar navigation
with st.sidebar:
    selected = option_menu(
        "Dashboard Pages",
        ["Demographics & Target", "Health Metrics", "Lifestyle Factors", "Mental & Environmental"],
        icons=["person", "activity", "heart-pulse", "cloud"],
        menu_icon="bar-chart", default_index=0
    )

# -------- PAGE 1: Demographics -------- #
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

# -------- PAGE 2: Health Metrics -------- #
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

# -------- PAGE 3: Lifestyle Factors -------- #
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

# -------- PAGE 4: Mental & Environmental -------- #
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
