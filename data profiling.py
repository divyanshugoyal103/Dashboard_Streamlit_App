# You must install these libraries to run the app:
# pip install streamlit pandas openpyxl numpy

import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
from io import BytesIO

# --- Data Profiling Function to Generate Structured Report Data ---
def create_profile_report_data(df, filename):
    """
    Analyzes a DataFrame and generates a dictionary with the specified profiling structure,
    including detailed column statistics.
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
    
    # Check for duplicate rows
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        quality_issues.append(f"{duplicates} duplicate rows found")

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
        
        # Initialize statistics dictionary
        stats = {}
        
        if report_type == "numeric":
            # Column statistics for numeric data
            stats["min"] = series.min()
            stats["max"] = series.max()
            stats["mean"] = series.mean()
            stats["median"] = series.median()
            
            # Outlier detection using IQR
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = series[(series < lower_bound) | (series > upper_bound)].count()
            if outliers > 0:
                quality_issues.append(f"{col}: {outliers} potential outliers detected")
            
        top_values = []
        if report_type == "categorical":
            # Get top values for categorical data
            if not series.empty:
                value_counts = series.value_counts(normalize=True).head(5)
                for val, percent in value_counts.items():
                    top_values.append({
                        "value": str(val),
                        "count": int(series.value_counts()[val]),
                        "percent": f"{percent * 100:.1f}%"
                    })
        
        # Check for potential issues and optimizations
        if report_type == "categorical" and unique_count / rows > 0.95:
            quality_issues.append(f"{col}: Potential ID column ({unique_count / rows * 100:.0f}% unique)")
        
        if report_type == "categorical" and unique_count < 0.5 * rows:
            optimization_suggestions.append(f"Convert '{col}' to categorical type for memory savings")
        
        column_summary.append({
            "column": col,
            "type": report_type,
            "missing_percent": missing_percent,
            "unique": unique_count,
            "stats": stats,
            "top_values": top_values,
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

    st.title("📊 Data Upload & Profiler")
    st.markdown("Upload your CSV or Excel file to get instant data insights and quality analysis.")

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
            
            st.success(f"🎉 Uploaded: {uploaded_file.name}")
            
            st.markdown("---")
            st.header("🔍 Data Preview")
            st.write(f"({df.shape[0]} rows total)")
            st.dataframe(df.head())
            
            # Generate the report data
            report = create_profile_report_data(df, uploaded_file.name)

            # --- Render the Report Sections ---
            st.markdown("---")
            st.header("Dataset Overview")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", f"{report['basicInfo']['rows']:,}")
            with col2:
                st.metric("Columns", f"{report['basicInfo']['columns']}")
            with col3:
                st.metric("Est. Memory", f"{report['basicInfo']['memoryEstimate']} MB")

            st.markdown("---")
            st.header("Column Analysis")
            
            # Display detailed analysis for each column using an expander
            for col_info in report["columnSummary"]:
                with st.expander(f"**{col_info['column']}** ({col_info['type']})"):
                    st.write(f"**Unique Values:** {col_info['unique']}")
                    st.write(f"**Missing Values:** {col_info['missing_percent']}")
                    
                    if col_info["type"] == "numeric":
                        st.subheader("Statistics")
                        stats_df = pd.DataFrame([col_info["stats"]]).T.rename(columns={0: "Value"})
                        st.table(stats_df.style.format(precision=2))
                    
                    if col_info["type"] == "categorical" and col_info["top_values"]:
                        st.subheader("Top Values")
                        top_values_df = pd.DataFrame(col_info["top_values"])
                        st.dataframe(top_values_df)

            st.markdown("---")
            st.header("Data Quality Issues")
            if report["qualityIssues"]:
                for issue in report["qualityIssues"]:
                    st.warning(f"⚠️ {issue}")
            else:
                st.success("✅ No major data quality issues found.")

            st.markdown("---")
            st.header("Optimization Suggestions")
            if report["optimizationSuggestions"]:
                for suggestion in report["optimizationSuggestions"]:
                    st.info(f"💡 {suggestion}")
            else:
                st.success("✅ No major optimization suggestions.")

            # Add the download button for the JSON report
            st.markdown("---")
            st.header("Download Report")
            json_report = json.dumps(report, indent=2)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            download_filename = f"profile_{uploaded_file.name.split('.')[0]}_{timestamp}.json"
            
            st.download_button(
                label="⬇️ Download Full JSON Report",
                data=json_report,
                file_name=download_filename,
                mime="application/json"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.info("Please check if your file format is correct and the data is not corrupt.")

if __name__ == "__main__":
    main()
