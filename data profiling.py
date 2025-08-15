# To run this app, you'll need to install these libraries:
# pip install streamlit pandas openpyxl

import streamlit as st
import pandas as pd
import json
from datetime import datetime

def analyze_dataframe(df):
    """
    Performs data profiling on a pandas DataFrame to generate a report.
    This function manually calculates all the metrics found in your example JSON.
    """
    report = {}

    # Basic Info
    report['basicInfo'] = {
        'rows': df.shape[0],
        'columns': df.shape[1],
        'memoryEstimate': f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f}"
    }

    # Column Summary & Analysis
    column_summary = []
    quality_issues = []
    optimization_suggestions = []

    for col in df.columns:
        col_type = df[col].dtype
        
        # Check for object types that might be numeric or datetime
        if pd.api.types.is_object_dtype(col_type):
            try:
                # Attempt to convert to numeric
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                if numeric_col.notna().sum() / df.shape[0] > 0.8: # > 80% are numeric
                    col_type = 'numeric'
                else:
                    try:
                        # Attempt to convert to datetime
                        pd.to_datetime(df[col], errors='raise')
                        col_type = 'datetime'
                    except:
                        col_type = 'categorical'
            except:
                col_type = 'categorical'

        # Get unique and missing values
        unique_count = df[col].nunique()
        missing_count = df[col].isnull().sum()
        missing_percent = (missing_count / df.shape[0]) * 100

        col_info = {
            'column': col,
            'type': str(col_type),
            'missing': f"{missing_percent:.1f}%",
            'unique': unique_count
        }
        column_summary.append(col_info)

        # Quality Issues
        if missing_percent > 50:
            quality_issues.append(f"{col}: High missing data ({missing_percent:.1f}%)")
        
        # Check for potential ID columns (high unique ratio for non-numeric)
        if unique_count / df.shape[0] > 0.9 and col_type in ['categorical', 'object']:
             quality_issues.append(f"{col}: Potential ID column ({unique_count/df.shape[0]*100:.0f}% unique)")
        
        # Outlier detection for numeric columns (simple IQR method)
        if col_type in ['numeric', 'int64', 'float64']:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[col][(df[col] < lower_bound) | (df[col] > upper_bound)].count()
            if outliers > 0:
                quality_issues.append(f"{col}: {outliers} potential outliers detected")

        # Optimization Suggestions
        if col_type in ['categorical', 'object'] and unique_count / df.shape[0] < 0.5:
            optimization_suggestions.append(f"Convert '{col}' to categorical type for memory savings")
    
    # Check for duplicate rows
    duplicate_rows_count = df.duplicated().sum()
    if duplicate_rows_count > 0:
        quality_issues.append(f"{duplicate_rows_count} duplicate rows found")

    report['columnSummary'] = column_summary
    report['qualityIssues'] = quality_issues
    report['optimizationSuggestions'] = optimization_suggestions
    report['timestamp'] = datetime.now().isoformat()
    report['filename'] = "Uploaded_File.csv"

    return report

# --- Streamlit UI ---

st.set_page_config(
    page_title="Data Profiler App",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Data Profiler")
st.markdown("Upload a CSV or Excel file to see its profile details in a structured format.")

uploaded_file = st.file_uploader(
    "**Upload your data file**",
    type=["csv", "xlsx", "xls"],
)

if uploaded_file:
    try:
        with st.spinner("⏳ Reading and profiling your file..."):
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                df = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            if df.empty:
                st.warning("The uploaded file is empty or could not be parsed.")
            else:
                profile_report = analyze_dataframe(df)

        st.success("🎉 File profiled successfully!")
        
        st.markdown("---")
        st.header("🔍 Dataset Overview")
        st.json(profile_report['basicInfo'])

        st.markdown("---")
        st.header("📋 Column Summary")
        st.json(profile_report['columnSummary'])
        
        if profile_report['qualityIssues']:
            st.markdown("---")
            st.header("⚠️ Quality Issues")
            st.json(profile_report['qualityIssues'])

        if profile_report['optimizationSuggestions']:
            st.markdown("---")
            st.header("⚡ Optimization Suggestions")
            st.json(profile_report['optimizationSuggestions'])

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please check if your file format is correct and the data is not corrupt.")
