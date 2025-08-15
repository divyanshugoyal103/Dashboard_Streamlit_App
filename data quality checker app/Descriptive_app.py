import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import io

def detect_column_types(df):
    """Detect column types and analyze data characteristics"""
    column_info = {}
    
    for col in df.columns:
        # Get non-null values
        values = df[col].dropna()
        
        if len(values) == 0:
            column_info[col] = {
                'type': 'empty',
                'unique_values': 0,
                'unique_ratio': 0,
                'sample_values': []
            }
            continue
        
        unique_values = values.nunique()
        unique_ratio = unique_values / len(values) if len(values) > 0 else 0
        
        # Type detection
        col_type = 'text'
        
        # Check if numeric
        try:
            pd.to_numeric(values, errors='raise')
            col_type = 'numeric'
        except (ValueError, TypeError):
            # Check if categorical (low unique ratio)
            if unique_ratio < 0.1:
                col_type = 'categorical'
            else:
                # Check if datetime
                try:
                    pd.to_datetime(values, errors='raise', infer_datetime_format=True)
                    col_type = 'datetime'
                except (ValueError, TypeError):
                    col_type = 'text'
        
        column_info[col] = {
            'type': col_type,
            'unique_values': unique_values,
            'unique_ratio': unique_ratio,
            'sample_values': values.head(5).tolist()
        }
    
    return column_info

def generate_quality_report(df):
    """Generate comprehensive data quality report"""
    if df is None or df.empty:
        return {'error': 'No data to analyze'}
    
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    
    # Missing values analysis
    missing_analysis = {}
    total_missing = 0
    
    for col in df.columns:
        missing_count = df[col].isnull().sum() + (df[col] == '').sum()
        if missing_count > 0:
            missing_analysis[col] = {
                'count': int(missing_count),
                'percentage': float((missing_count / total_rows) * 100)
            }
            total_missing += missing_count
    
    # Duplicate analysis
    duplicate_rows = df.duplicated().sum()
    
    # Column type analysis
    column_info = detect_column_types(df)
    
    # Numeric analysis
    numeric_analysis = {}
    for col in df.columns:
        if column_info[col]['type'] == 'numeric':
            try:
                numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(numeric_values) > 0:
                    q1 = numeric_values.quantile(0.25)
                    q3 = numeric_values.quantile(0.75)
                    iqr = q3 - q1
                    outliers = numeric_values[(numeric_values < q1 - 1.5 * iqr) | 
                                            (numeric_values > q3 + 1.5 * iqr)]
                    
                    numeric_analysis[col] = {
                        'min': float(numeric_values.min()),
                        'max': float(numeric_values.max()),
                        'mean': float(numeric_values.mean()),
                        'outliers': len(outliers),
                        'zeros': int((numeric_values == 0).sum()),
                        'negatives': int((numeric_values < 0).sum())
                    }
            except Exception:
                pass
    
    # Text analysis
    text_analysis = {}
    for col in df.columns:
        if column_info[col]['type'] in ['text', 'categorical']:
            text_values = df[col].dropna().astype(str)
            text_values = text_values[text_values != '']
            
            if len(text_values) > 0:
                lengths = text_values.str.len()
                text_analysis[col] = {
                    'avg_length': float(lengths.mean()),
                    'min_length': int(lengths.min()),
                    'max_length': int(lengths.max()),
                    'leading_spaces': int((text_values != text_values.str.lstrip()).sum()),
                    'trailing_spaces': int((text_values != text_values.str.rstrip()).sum())
                }
    
    # Calculate quality score
    quality_score = 100
    penalties = []
    
    # Missing data penalty
    if total_missing > 0:
        missing_ratio = total_missing / total_cells
        penalty = min(missing_ratio * 40, 20)
        quality_score -= penalty
        penalties.append(f"Missing data: -{penalty:.1f}")
    
    # Duplicate penalty
    if duplicate_rows > 0:
        duplicate_ratio = duplicate_rows / total_rows
        penalty = min(duplicate_ratio * 20, 10)
        quality_score -= penalty
        penalties.append(f"Duplicates: -{penalty:.1f}")
    
    # Generate recommendations
    recommendations = []
    
    if total_missing > 0:
        high_missing_cols = [col for col, info in missing_analysis.items() 
                           if info['percentage'] > 50]
        
        if high_missing_cols:
            recommendations.append(f"Consider removing columns with >50% missing data: {', '.join(high_missing_cols)}")
        else:
            recommendations.append("Address missing values through imputation or removal")
    
    if duplicate_rows > 0:
        recommendations.append(f"Remove {duplicate_rows} duplicate rows")
    
    for col, info in column_info.items():
        if info['unique_values'] == 1:
            recommendations.append(f"Consider removing constant column '{col}'")
        elif info['unique_ratio'] == 1.0 and total_rows > 1:
            recommendations.append(f"Column '{col}' appears to be a unique identifier")
    
    if not recommendations:
        recommendations.append("✓ Data appears to be in good quality!")
    
    # Calculate file size estimate
    file_size_kb = len(df.to_csv()) / 1024
    
    return {
        'summary': {
            'total_rows': total_rows,
            'total_columns': total_cols,
            'total_cells': total_cells,
            'file_size': f"{file_size_kb:.1f} KB"
        },
        'missing_analysis': missing_analysis,
        'total_missing': int(total_missing),
        'duplicate_rows': int(duplicate_rows),
        'column_info': column_info,
        'numeric_analysis': numeric_analysis,
        'text_analysis': text_analysis,
        'quality_score': max(quality_score, 0),
        'penalties': penalties,
        'recommendations': recommendations
    }

def generate_text_report(report, filename):
    """Generate downloadable text report"""
    lines = []
    lines.append('DATA QUALITY REPORT')
    lines.append('=' * 60)
    lines.append(f'File: {filename}')
    lines.append(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append('')
    
    lines.append('SUMMARY:')
    lines.append(f'• Rows: {report["summary"]["total_rows"]:,}')
    lines.append(f'• Columns: {report["summary"]["total_columns"]}')
    lines.append(f'• File Size: {report["summary"]["file_size"]}')
    lines.append('')
    
    lines.append('MISSING VALUES:')
    if not report['missing_analysis']:
        lines.append('• No missing values found')
    else:
        for col, info in report['missing_analysis'].items():
            lines.append(f'• {col}: {info["count"]} ({info["percentage"]:.1f}%)')
    lines.append('')
    
    lines.append(f'DUPLICATE ROWS: {report["duplicate_rows"]}')
    lines.append('')
    
    lines.append('COLUMN TYPES:')
    for col, info in report['column_info'].items():
        lines.append(f'• {col}: {info["type"]} ({info["unique_values"]} unique, {info["unique_ratio"]*100:.1f}% unique)')
    lines.append('')
    
    lines.append(f'QUALITY SCORE: {report["quality_score"]:.1f}/100')
    if report['penalties']:
        lines.append('Penalties:')
        for penalty in report['penalties']:
            lines.append(f'• {penalty}')
    lines.append('')
    
    lines.append('RECOMMENDATIONS:')
    for i, rec in enumerate(report['recommendations'], 1):
        lines.append(f'{i}. {rec}')
    
    return '\n'.join(lines)

def main():
    st.set_page_config(
        page_title="Data Quality Checker",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1>📊 Data Quality Checker</h1>
        <p style='font-size: 1.2rem; color: #666;'>Upload your data files for comprehensive quality analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'txt', 'json', 'xlsx', 'xls'],
        help="Supports CSV, TXT, JSON, and Excel files"
    )
    
    if uploaded_file is not None:
        try:
            # Load data based on file type
            filename = uploaded_file.name.lower()
            
            with st.spinner('Analyzing your data...'):
                if filename.endswith(('.csv', '.txt')):
                    df = pd.read_csv(uploaded_file)
                elif filename.endswith('.json'):
                    data = json.load(uploaded_file)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame([data])
                elif filename.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file)
                else:
                    st.error(f"Unsupported file format: {filename}")
                    return
                
                # Generate quality report
                report = generate_quality_report(df)
            
            if 'error' in report:
                st.error(report['error'])
                return
            
            # File info
            st.success(f"✅ Successfully loaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Rows", f"{report['summary']['total_rows']:,}")
            
            with col2:
                st.metric("Columns", report['summary']['total_columns'])
            
            with col3:
                st.metric("Missing Values", report['total_missing'], 
                         delta=None if report['total_missing'] == 0 else "⚠️")
            
            with col4:
                score = report['quality_score']
                color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                st.metric("Quality Score", f"{score:.1f}/100", delta=color)
            
            # Tabs for detailed analysis
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "❌ Missing Data", "📊 Column Analysis", "💡 Recommendations"])
            
            with tab1:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Data Preview")
                    st.dataframe(df.head(10), use_container_width=True)
                
                with col2:
                    st.subheader("Quick Stats")
                    st.write(f"**Duplicate Rows:** {report['duplicate_rows']}")
                    st.write(f"**File Size:** {report['summary']['file_size']}")
                    
                    if report['penalties']:
                        st.subheader("Quality Penalties")
                        for penalty in report['penalties']:
                            st.write(f"• {penalty}")
            
            with tab2:
                if report['missing_analysis']:
                    st.subheader("Missing Values Analysis")
                    
                    missing_df = pd.DataFrame([
                        {
                            'Column': col,
                            'Missing Count': info['count'],
                            'Percentage': f"{info['percentage']:.1f}%"
                        }
                        for col, info in report['missing_analysis'].items()
                    ])
                    
                    st.dataframe(missing_df, use_container_width=True)
                    
                    # Visualize missing data
                    st.subheader("Missing Data Visualization")
                    missing_data = df.isnull().sum()
                    missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
                    
                    if len(missing_data) > 0:
                        st.bar_chart(missing_data)
                else:
                    st.success("🎉 No missing values found in your data!")
            
            with tab3:
                st.subheader("Column Type Analysis")
                
                # Create column analysis dataframe
                col_analysis = []
                for col, info in report['column_info'].items():
                    col_analysis.append({
                        'Column': col,
                        'Type': info['type'],
                        'Unique Values': info['unique_values'],
                        'Uniqueness %': f"{info['unique_ratio']*100:.1f}%",
                        'Sample Values': ', '.join(map(str, info['sample_values'][:3]))
                    })
                
                col_df = pd.DataFrame(col_analysis)
                st.dataframe(col_df, use_container_width=True)
                
                # Numeric analysis if available
                if report['numeric_analysis']:
                    st.subheader("Numeric Columns Analysis")
                    for col, stats in report['numeric_analysis'].items():
                        with st.expander(f"📈 {col}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Min", f"{stats['min']:.2f}")
                                st.metric("Max", f"{stats['max']:.2f}")
                            with col2:
                                st.metric("Mean", f"{stats['mean']:.2f}")
                                st.metric("Outliers", stats['outliers'])
                            with col3:
                                st.metric("Zeros", stats['zeros'])
                                st.metric("Negatives", stats['negatives'])
                
                # Text analysis if available
                if report['text_analysis']:
                    st.subheader("Text Columns Analysis")
                    for col, stats in report['text_analysis'].items():
                        with st.expander(f"📝 {col}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Avg Length", f"{stats['avg_length']:.1f}")
                                st.metric("Min Length", stats['min_length'])
                            with col2:
                                st.metric("Max Length", stats['max_length'])
                                st.metric("Leading Spaces", stats['leading_spaces'])
            
            with tab4:
                st.subheader("🎯 Data Quality Recommendations")
                
                for i, recommendation in enumerate(report['recommendations'], 1):
                    if recommendation.startswith('✓'):
                        st.success(f"{i}. {recommendation}")
                    else:
                        st.info(f"{i}. {recommendation}")
            
            # Download report
            st.markdown("---")
            report_text = generate_text_report(report, uploaded_file.name)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.download_button(
                    label="📥 Download Full Report",
                    data=report_text,
                    file_name=f"quality_report_{uploaded_file.name.split('.')[0]}.txt",
                    mime="text/plain"
                )
            
            with col2:
                with st.expander("📄 Preview Full Report"):
                    st.text(report_text)
                    
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please make sure your file is properly formatted and try again.")
    
    else:
        # Instructions when no file is uploaded
        st.markdown("""
        ### 📁 Getting Started
        
        1. **Upload your data file** using the file uploader above
        2. **Supported formats**: CSV, TXT, JSON, Excel (.xlsx, .xls)
        3. **Get instant analysis** including:
           - Missing values detection
           - Data type identification  
           - Quality scoring
           - Actionable recommendations
        
        ### 📊 What You'll Get
        
        - **Summary metrics** of your dataset
        - **Missing data analysis** with visualizations
        - **Column-by-column breakdown** with type detection
        - **Quality score** with detailed penalties
        - **Downloadable report** for your records
        """)

if __name__ == "__main__":
    main()
