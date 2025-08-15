import streamlit as st
import pandas as pd
import json
import io

def generate_report(df: pd.DataFrame) -> dict:
    """
    Generates a comprehensive data quality report from a pandas DataFrame.
    """
    if df.empty:
        return {'error': 'No data to analyze'}

    total_rows = len(df)
    total_columns = len(df.columns)
    total_cells = total_rows * total_columns

    # Missing values analysis
    missing_counts = df.isnull().sum()
    missing_analysis = {
        col: {'count': int(count), 'percentage': (count / total_rows) * 100}
        for col, count in missing_counts.items() if count > 0
    }
    total_missing = sum(d['count'] for d in missing_analysis.values())

    # Duplicate analysis
    duplicate_rows = df.duplicated().sum()
    
    # Check for duplicate column names
    duplicate_columns = set()
    seen_columns = set()
    for col in df.columns:
        if col in seen_columns:
            duplicate_columns.add(col)
        else:
            seen_columns.add(col)

    # Column type analysis and recommendations
    column_info = {}
    recommendations = []
    
    for col in df.columns:
        # Get a series for the column, dropping nulls for unique value count
        series = df[col].dropna()
        if series.empty:
            column_info[col] = {'type': 'empty', 'unique_values': 0, 'unique_ratio': 0.0}
            recommendations.append(f"Consider removing empty column '{col}'")
            continue

        unique_values = series.nunique()
        total_non_null = len(series)
        unique_ratio = unique_values / total_non_null if total_non_null > 0 else 0
        
        # Heuristic type detection (similar to the React code)
        dtype = 'text'
        try:
            # Check if numeric
            if pd.to_numeric(series, errors='coerce').notna().all():
                dtype = 'numeric'
            # Check if datetime
            elif pd.to_datetime(series, errors='coerce').notna().mean() > 0.8:
                dtype = 'datetime'
            # Check if categorical
            elif unique_ratio < 0.1:
                dtype = 'categorical'
        except:
            pass # Fall back to 'text'

        column_info[col] = {
            'type': dtype,
            'unique_values': unique_values,
            'unique_ratio': unique_ratio,
        }

        # Additional recommendations based on column properties
        if unique_values == 1:
            recommendations.append(f"Consider removing constant column '{col}'")
        elif unique_ratio == 1.0 and total_rows > 1:
            recommendations.append(f"Column '{col}' appears to be a unique identifier")

    # Calculate quality score
    quality_score = 100
    penalties = []
    
    # Missing data penalty
    missing_ratio = total_missing / total_cells if total_cells > 0 else 0
    if missing_ratio > 0:
        penalty = min(missing_ratio * 40, 20)
        quality_score -= penalty
        penalties.append(f"Missing data: -{penalty:.1f}")

    # Duplicate penalty
    if duplicate_rows > 0:
        duplicate_ratio = duplicate_rows / total_rows
        penalty = min(duplicate_ratio * 20, 10)
        quality_score -= penalty
        penalties.append(f"Duplicates: -{penalty:.1f}")

    if not recommendations:
        recommendations.append('✓ Data appears to be in good quality!')

    return {
        'summary': {
            'total_rows': total_rows,
            'total_columns': total_columns,
            'total_cells': total_cells
        },
        'missing_analysis': missing_analysis,
        'total_missing': total_missing,
        'duplicate_rows': duplicate_rows,
        'duplicate_columns': list(duplicate_columns),
        'column_info': column_info,
        'quality_score': max(quality_score, 0),
        'penalties': penalties,
        'recommendations': recommendations
    }

def main():
    """The main Streamlit application function."""
    st.set_page_config(layout="wide", page_title="Data Quality Checker")
    st.title("📊 Data Quality Checker")
    st.markdown("---")
    
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="font-size: 1.2rem; color: #555;">
                Upload your data file (CSV or JSON) to get a comprehensive quality report.
            </p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a file", type=["csv", "json"], key="file_uploader")
    
    if uploaded_file is not None:
        try:
            # Read data based on file type
            file_name = uploaded_file.name
            if file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith('.json'):
                data = json.load(uploaded_file)
                if not isinstance(data, list):
                    data = [data]
                df = pd.DataFrame(data)
            else:
                st.error("Unsupported file format. Please upload a CSV or JSON file.")
                st.stop()

            st.success(f"File uploaded successfully: {file_name}")

            with st.spinner('Analyzing data...'):
                report = generate_report(df)

            if 'error' in report:
                st.error(f"Error analyzing data: {report['error']}")
            else:
                st.markdown("---")
                st.header("Quality Report")

                # Summary cards
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Rows", f"{report['summary']['total_rows']:,}")
                with col2:
                    st.metric("Total Columns", report['summary']['total_columns'])
                with col3:
                    st.metric("Missing Values", report['total_missing'])
                with col4:
                    score_color = 'green' if report['quality_score'] >= 80 else 'yellow' if report['quality_score'] >= 60 else 'red'
                    st.markdown(f"<p style='color: {score_color}; font-size: 1.5rem; font-weight: bold;'>Quality Score</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: {score_color}; font-size: 2rem; font-weight: bold;'>{report['quality_score']:.1f}/100</p>", unsafe_allow_html=True)

                # Missing values and duplicates
                st.markdown("---")
                if report['total_missing'] > 0:
                    st.warning("⚠️ Missing Values Found")
                    missing_df = pd.DataFrame(report['missing_analysis']).T.rename(columns={'count': 'Missing Count', 'percentage': 'Missing Percentage (%)'})
                    st.dataframe(missing_df.style.format({'Missing Percentage (%)': '{:.1f}'}), use_container_width=True)
                else:
                    st.success("✅ No missing values found.")

                if report['duplicate_rows'] > 0:
                    st.warning(f"⚠️ Found {report['duplicate_rows']} duplicate rows.")
                if report['duplicate_columns']:
                    st.warning(f"⚠️ Found duplicate column names: {', '.join(report['duplicate_columns'])}.")
                
                # Column analysis table
                st.markdown("---")
                st.subheader("Column Analysis")
                column_df = pd.DataFrame(report['column_info']).T.rename(columns={
                    'type': 'Type',
                    'unique_values': 'Unique Values',
                    'unique_ratio': 'Uniqueness (%)'
                })
                column_df['Uniqueness (%)'] = (column_df['Uniqueness (%)'] * 100).round(1)
                st.dataframe(column_df, use_container_width=True)

                # Recommendations
                st.markdown("---")
                st.subheader("Recommendations")
                for rec in report['recommendations']:
                    st.info(rec)
                
                # Download button
                # Build the multi-line parts of the report string separately
                missing_values_text = "• No missing values found" if report['total_missing'] == 0 else "\n".join(
                    f"• {col}: {info['count']} ({info['percentage']:.1f}%)" for col, info in report['missing_analysis'].items()
                )
                
                penalties_text = "• No penalties" if not report['penalties'] else "\n".join(
                    f"• {p}" for p in report['penalties']
                )

                column_types_text = "\n".join(
                    f"• {col}: {info['type']} ({info['unique_values']} unique, {info['unique_ratio'] * 100:.1f}% unique)"
                    for col, info in report['column_info'].items()
                )

                recommendations_text = "\n".join(
                    f"{i+1}. {rec}" for i, rec in enumerate(report['recommendations'])
                )

                report_text = f"""
DATA QUALITY REPORT
==================================================
File: {file_name}
Generated: {pd.Timestamp.now()}

SUMMARY:
• Rows: {report['summary']['total_rows']:,}
• Columns: {report['summary']['total_columns']}
• File Size: {uploaded_file.size / 1024:.1f} KB

MISSING VALUES:
{missing_values_text}

DUPLICATE ROWS: {report['duplicate_rows']}
DUPLICATE COLUMNS: {", ".join(report['duplicate_columns']) if report['duplicate_columns'] else "None"}

COLUMN TYPES:
{column_types_text}

QUALITY SCORE: {report['quality_score']:.1f}/100
Penalties:
{penalties_text}

RECOMMENDATIONS:
{recommendations_text}
"""
                st.download_button(
                    label="Download Full Report",
                    data=report_text,
                    file_name=f"quality_report_{file_name.split('.')[0]}.txt",
                    mime="text/plain",
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()

