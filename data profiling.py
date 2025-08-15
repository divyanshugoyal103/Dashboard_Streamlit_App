# You must install these libraries to run the app:
# pip install streamlit pandas openpyxl numpy

import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- Custom CSS for a professional look ---
st.markdown("""
<style>
    /* Main Content */
    .reportview-container {
        background: #f0f2f6;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Header and Title */
    h1 {
        color: #1a237e;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 700;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #4a4a4a;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #1a237e;
        font-size: 2rem;
        font-weight: 700;
    }

    /* Section Headers */
    h2 {
        color: #37474f;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }

    /* Table Styling */
    .stTable {
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Warning and Info Boxes */
    div.stAlert.stAlert--info {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
        color: #2196f3;
        font-weight: 500;
    }
    div.stAlert.stAlert--warning {
        background-color: #fff3e0;
        border-left-color: #ff9800;
        color: #ff9800;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Profiling Function to Generate Structured Report Data ---
def create_profile_report_data(df, filename):
    """
    Analyzes a DataFrame and generates a dictionary with the specified profiling structure,
    including detailed column statistics and specific duplicate information.
    """
    rows, cols = df.shape

    # Calculate basic info and memory usage
    memory_estimate = f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f}"

    basic_info = {
        "rows": rows,
        "columns": cols,
        "memoryEstimate": memory_estimate
    }

    column_summary = []
    quality_issues = []
    optimization_suggestions = []

    # Check for duplicate columns
    duplicate_cols = df.columns[df.columns.duplicated()].unique().tolist()
    if duplicate_cols:
        quality_issues.append({
            "type": "Duplicate Columns",
            "count": len(duplicate_cols),
            "details": f"The following columns are duplicated: {', '.join(duplicate_cols)}"
        })
    
    # Check for duplicate rows and get a preview of them
    duplicated_rows_df = df[df.duplicated(keep='first')]
    if not duplicated_rows_df.empty:
        quality_issues.append({
            "type": "Duplicate Rows",
            "count": len(duplicated_rows_df),
            "details": duplicated_rows_df.to_dict('records')
        })

    # Analyze each column
    for col in df.columns:
        series = df[col]
        
        # Determine column type
        if pd.api.types.is_numeric_dtype(series):
            report_type = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            report_type = "date/time"
        else:
            report_type = "categorical"
            
        # Missing values
        missing_count = series.isnull().sum()
        missing_percent = f"{(missing_count / rows) * 100:.0f}%"
        
        # Unique values
        unique_count = series.nunique()
        
        details = ""
        
        if report_type == "numeric":
            # Column statistics for numeric data
            stats = {
                "min": series.min(),
                "max": series.max(),
                "mean": series.mean(),
                "median": series.median()
            }
            details += f"Range: {stats['min']:.2f} - {stats['max']:.2f}"
            
            # Outlier detection using IQR
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = series[(series < lower_bound) | (series > upper_bound)].count()
            if outliers > 0:
                quality_issues.append({
                    "type": "Outliers",
                    "column": col,
                    "count": int(outliers),
                    "details": f"{col}: {int(outliers)} potential outliers detected"
                })
                details += f"\n{int(outliers)} outliers"
            
        if report_type == "categorical":
            # Get top values for categorical data
            if not series.empty:
                value_counts = series.value_counts(normalize=True).head(1)
                for val, percent in value_counts.items():
                    details += f"Top: {val} ({percent * 100:.1f}%)"
        
        # Check for potential high cardinality
        if report_type == "categorical" and unique_count / rows > 0.95:
            quality_issues.append({
                "type": "High Cardinality",
                "column": col,
                "details": f"{col}: Potential ID column ({unique_count / rows * 100:.0f}% unique)"
            })
        
        if report_type == "categorical" and unique_count < 0.5 * rows:
            optimization_suggestions.append(f"Convert '{col}' to categorical type for memory savings")
        
        column_summary.append({
            "column": col,
            "type": report_type,
            "missing_percent": missing_percent,
            "unique": unique_count,
            "details": details
        })

    # Get column type counts for the summary
    column_types = {
        "numeric": 0,
        "categorical": 0,
        "date/time": 0
    }
    for col_info in column_summary:
        if col_info["type"] in column_types:
            column_types[col_info["type"]] += 1

    report_data = {
        "filename": filename,
        "timestamp": datetime.now().isoformat(),
        "basicInfo": basic_info,
        "columnTypes": column_types,
        "columnSummary": column_summary,
        "qualityIssues": quality_issues,
        "optimizationSuggestions": optimization_suggestions
    }
    
    return report_data

# --- Streamlit UI and App Logic ---
def main():
    st.set_page_config(
        page_title="JSON Data Profiler",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- Sidebar for File Upload and Controls ---
    with st.sidebar:
        st.title("📂 Controls")
        st.markdown("Upload your file and view the report on the right.")
        
        uploaded_file = st.file_uploader(
            "**Upload Your Data**",
            type=["csv", "xlsx", "xls"]
        )

        if uploaded_file:
            # Add the download button for the JSON report
            report_data = create_profile_report_data(pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, engine='openpyxl'), uploaded_file.name)
            json_report = json.dumps(report_data, indent=2)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            download_filename = f"profile_{uploaded_file.name.split('.')[0]}_{timestamp}.json"
            
            st.markdown("---")
            st.download_button(
                label="⬇️ Download Full JSON Report",
                data=json_report,
                file_name=download_filename,
                mime="application/json",
                use_container_width=True
            )

    # --- Main Content Area ---
    st.title("📊 Data Profiler")
    st.markdown("## Instant Insights & Quality Analysis")

    if uploaded_file:
        try:
            with st.spinner("⏳ Reading your file..."):
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                if file_extension == 'csv':
                    df = pd.read_csv(uploaded_file)
                elif file_extension in ['xlsx', 'xls']:
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            st.success(f"🎉 **Uploaded:** {uploaded_file.name}")
            
            # Generate the report data
            report = create_profile_report_data(df, uploaded_file.name)

            # --- Dataset Overview ---
            st.header("Dataset Overview")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", f"{report['basicInfo']['rows']:,}")
            with col2:
                st.metric("Columns", f"{report['basicInfo']['columns']}")
            with col3:
                st.metric("Est. Memory", f"{report['basicInfo']['memoryEstimate']} MB")

            # --- Data Preview ---
            st.header("Data Preview")
            st.write(f"({df.shape[0]} rows total)")
            st.dataframe(df.head())

            # --- Column Analysis ---
            st.header("Column Analysis")
            
            # Create a dataframe for the column summary table with details
            summary_df = pd.DataFrame(report["columnSummary"])
            st.table(summary_df[['column', 'type', 'missing_percent', 'unique', 'details']])

            # --- Quality Issues & Optimization Suggestions ---
            st.header("Data Quality Report")
            
            # --- Data Quality Issues Section ---
            st.subheader("Data Quality Issues")
            if report["qualityIssues"]:
                for issue in report["qualityIssues"]:
                    if issue["type"] == "Duplicate Rows":
                        st.warning(f"⚠️ **{issue['count']}** duplicate rows found. See preview below:")
                        st.dataframe(pd.DataFrame(issue["details"]))
                    elif issue["type"] == "Duplicate Columns":
                        st.warning(f"⚠️ **{issue['count']}** duplicate columns found. {issue['details']}")
                    else:
                        st.warning(f"⚠️ {issue['details']}")
            else:
                st.success("✅ No major data quality issues found.")
                
            # --- Optimization Suggestions Section ---
            st.subheader("Optimization Suggestions")
            if report["optimizationSuggestions"]:
                for suggestion in report["optimizationSuggestions"]:
                    st.info(f"💡 {suggestion}")
            else:
                st.success("✅ No major optimization suggestions.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.info("Please check if your file format is correct and the data is not corrupt.")

    else:
        st.info("⬅️ Please upload a file to get started.")

if __name__ == "__main__":
    main()
