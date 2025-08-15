# You must install these libraries to run the app:
# pip install streamlit pandas openpyxl numpy

import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
from io import BytesIO

# --- Data Profiling Function to Generate JSON ---
def create_profile_report(df, filename):
    """
    Analyzes a DataFrame and generates a dictionary with the specified profiling structure.
    """
    rows, cols = df.shape
    
    # Calculate basic info
    memory_estimate = f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f}"
    
    basic_info = {
        "rows": rows,
        "columns": cols,
        "memoryEstimate": memory_estimate
    }
    
    column_summary = []
    quality_issues = []
    optimization_suggestions = []
    
    # Check for duplicate rows
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        quality_issues.append(f"{duplicates} duplicate rows found")

    # Analyze each column
    for col in df.columns:
        series = df[col]
        col_type = str(series.dtype)
        
        # Determine column type for the report
        if pd.api.types.is_numeric_dtype(series):
            report_type = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            report_type = "date"
        else:
            report_type = "categorical"
        
        # Missing values
        missing_count = series.isnull().sum()
        missing_percent = f"{(missing_count / rows) * 100:.0f}%"
        
        # Unique values
        unique_count = series.nunique()

        # Check for potential issues and optimizations
        if pd.api.types.is_numeric_dtype(series):
            # Outlier detection using IQR
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = series[(series < lower_bound) | (series > upper_bound)].count()
            if outliers > 0:
                quality_issues.append(f"{col}: {outliers} potential outliers detected")
        
        if report_type == "categorical" and unique_count / rows > 0.95:
            quality_issues.append(f"{col}: Potential ID column ({unique_count / rows * 100:.0f}% unique)")
        
        if report_type == "categorical" and unique_count < 0.5 * rows:
            optimization_suggestions.append(f"Convert '{col}' to categorical type for memory savings")
        
        column_summary.append({
            "column": col,
            "type": report_type,
            "missing": missing_percent,
            "unique": unique_count
        })

    # Build the final JSON structure
    report = {
        "filename": filename,
        "timestamp": datetime.now().isoformat(),
        "basicInfo": basic_info,
        "columnSummary": column_summary,
        "qualityIssues": quality_issues,
        "optimizationSuggestions": optimizationSuggestions
    }
    
    return report

# --- Streamlit UI and App Logic ---
def main():
    st.set_page_config(
        page_title="JSON Data Profiler",
        layout="wide"
    )

    st.title("📊 Data Profiler for JSON Reports")
    st.markdown("Upload your CSV or Excel file to generate a structured JSON profile report.")

    uploaded_file = st.file_uploader(
        "**Step 1: Upload Your Data**",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        try:
            with st.spinner("⏳ Reading your file..."):
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                if file_extension == 'csv':
                    df = pd.read_csv(uploaded_file)
                elif file_extension in ['xlsx', 'xls']:
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            st.success("🎉 File uploaded and read successfully!")

            st.markdown("---")
            st.header("🔍 Data Preview")
            st.write(f"The dataset contains **{df.shape[0]} rows** and **{df.shape[1]} columns**.")
            st.dataframe(df.head())

            st.markdown("---")
            st.header("⬇️ Download Your Report")
            
            with st.spinner("Generating JSON report..."):
                report_data = create_profile_report(df, uploaded_file.name)
            
            json_report = json.dumps(report_data, indent=2)
            
            # Use BytesIO to create an in-memory file for download
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            download_filename = f"profile_{uploaded_file.name.split('.')[0]}_{timestamp}.json"
            
            st.download_button(
                label="⬇️ Download JSON Report",
                data=json_report,
                file_name=download_filename,
                mime="application/json"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.info("Please check if your file format is correct and the data is not corrupt.")

if __name__ == "__main__":
    main()
