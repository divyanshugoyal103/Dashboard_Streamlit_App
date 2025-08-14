import streamlit as st
import pandas as pd
from io import StringIO, BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="Data Profiler App",
    page_icon="📈",
    layout="wide",
)

# --- Functions for Data Profiling ---

def profile_data(df):
    """Generates a comprehensive data profile for a given DataFrame."""
    profile = {}
    
    # Basic Info
    profile['basicInfo'] = {
        'rows': df.shape[0],
        'columns': df.shape[1],
        'memoryEstimate': f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB"
    }

    # Column Analysis
    column_analysis = {}
    numeric_cols = []
    categorical_cols = []
    date_cols = []

    for col in df.columns:
        series = df[col]
        non_null_count = series.count()
        missing_count = series.isnull().sum()
        missing_percent = (missing_count / len(series)) * 100
        unique_count = series.nunique()
        unique_ratio = unique_count / non_null_count if non_null_count > 0 else 0
        
        column_type = 'mixed'
        stats = {}
        
        # Type inference
        if pd.api.types.is_numeric_dtype(series):
            column_type = 'numeric'
            numeric_cols.append(col)
            stats = {
                'min': series.min(),
                'max': series.max(),
                'mean': series.mean(),
                'median': series.median(),
                'std': series.std()
            }
        elif pd.api.types.is_datetime64_any_dtype(series):
            column_type = 'date'
            date_cols.append(col)
        else:
            column_type = 'categorical'
            categorical_cols.append(col)
            top_values = series.value_counts().head(5).reset_index()
            top_values.columns = ['value', 'count']
            top_values['percent'] = (top_values['count'] / non_null_count) * 100
            stats['topValues'] = top_values.to_dict('records')
            
        column_analysis[col] = {
            'type': column_type,
            'uniqueCount': unique_count,
            'missingCount': missing_count,
            'missingPercent': missing_percent,
            'uniqueRatio': unique_ratio,
            'stats': stats,
        }

    # Data Quality Issues
    quality_issues = []
    if df.duplicated().sum() > 0:
        quality_issues.append(f"{df.duplicated().sum()} duplicate rows found.")
    
    for col, analysis in column_analysis.items():
        if analysis['missingPercent'] > 50:
            quality_issues.append(f"Column '{col}': High missing data ({analysis['missingPercent']:.1f}%)")
        if analysis['uniqueRatio'] > 0.95 and analysis['type'] == 'categorical':
            quality_issues.append(f"Column '{col}': Potential ID column ({analysis['uniqueRatio'] * 100:.1f}% unique)")
        # Note: Outlier detection is complex. Using a simple IQR method for numeric columns for this example.
        if analysis['type'] == 'numeric':
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col].count()
            if outliers > 0:
                quality_issues.append(f"Column '{col}': {outliers} potential outliers detected")

    # Optimization Suggestions
    optimization_suggestions = []
    for col, analysis in column_analysis.items():
        if analysis['type'] == 'categorical' and analysis['uniqueRatio'] < 0.5:
            optimization_suggestions.append(f"Convert '{col}' to a 'category' type for memory savings.")
    
    profile['columnAnalysis'] = column_analysis
    profile['numericColumns'] = numeric_cols
    profile['categoricalColumns'] = categorical_cols
    profile['dateColumns'] = date_cols
    profile['qualityIssues'] = quality_issues
    profile['optimizationSuggestions'] = optimization_suggestions

    return profile

# --- Main Streamlit App ---

st.title("Data Profiler App 📊")
st.markdown("Upload a CSV or Excel file to get an instant, detailed data profile.")
st.write("---")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx"],
    help="Supports CSV and Excel files (.csv, .xlsx).",
    accept_multiple_files=False
)

if uploaded_file is not None:
    try:
        # Determine file type and read data
        file_extension = uploaded_file.name.split('.')[-1]
        
        with st.spinner('Reading and processing your file...'):
            if file_extension == 'csv':
                df = pd.read_csv(uploaded_file, encoding='latin-1', on_bad_lines='skip')
            elif file_extension == 'xlsx':
                df = pd.read_excel(uploaded_file)
            else:
                st.error("Unsupported file type. Please upload a CSV or Excel file.")
                st.stop()
        
        if df.empty:
            st.warning("The uploaded file is empty or could not be parsed.")
        else:
            # Generate the data profile
            with st.spinner('Generating data profile...'):
                profile = profile_data(df)
            
            st.success("File processed and data profile generated successfully!")
            
            # --- Display Results ---
            
            st.header("1. Dataset Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", profile['basicInfo']['rows'])
            with col2:
                st.metric("Columns", profile['basicInfo']['columns'])
            with col3:
                st.metric("Est. Memory", profile['basicInfo']['memoryEstimate'])
            
            st.write("---")

            st.header("2. Data Preview")
            st.markdown(f"Displaying the first 5 rows of {profile['basicInfo']['rows']} total rows.")
            st.dataframe(df.head(), use_container_width=True)
            
            st.write("---")

            st.header("3. Column Types Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader(f"Numeric ({len(profile['numericColumns'])})")
                st.markdown(", ".join(profile['numericColumns']))
            with col2:
                st.subheader(f"Categorical ({len(profile['categoricalColumns'])})")
                st.markdown(", ".join(profile['categoricalColumns']))
            with col3:
                st.subheader(f"Date/Time ({len(profile['dateColumns'])})")
                st.markdown(", ".join(profile['dateColumns']))
            
            st.write("---")
            
            st.header("4. Detailed Column Analysis")
            profile_df = pd.DataFrame(profile['columnAnalysis']).T
            st.dataframe(profile_df, use_container_width=True)
            
            st.write("---")
            
            if profile['qualityIssues']:
                st.header("5. Data Quality Issues ⚠️")
                for issue in profile['qualityIssues']:
                    st.warning(issue)
                
                st.write("---")

            if profile['optimizationSuggestions']:
                st.header("6. Optimization Suggestions 🚀")
                for suggestion in profile['optimizationSuggestions']:
                    st.info(suggestion)
                
                st.write("---")
            
            # --- Download Button ---
            
            # Prepare a report for download
            report_content = {
                "filename": uploaded_file.name,
                "basic_info": profile['basicInfo'],
                "column_analysis": profile['columnAnalysis'],
                "quality_issues": profile['qualityIssues'],
                "optimization_suggestions": profile['optimizationSuggestions']
            }
            
            # Convert dictionary to JSON string
            import json
            report_json = json.dumps(report_content, indent=4)
            
            st.download_button(
                label="Download Report as JSON",
                data=report_json,
                file_name=f"data_profile_{uploaded_file.name}.json",
                mime="application/json"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please check if the file format is correct and the data is not corrupt.")
