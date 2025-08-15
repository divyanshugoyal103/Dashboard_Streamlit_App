import streamlit as st
import pandas as pd
import json
import sqlite3
from datetime import datetime
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

# Set page config
st.set_page_config(
    page_title="Interactive Data Export Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class StreamlitDataExporter:
    def __init__(self, df, base_filename=None):
        self.df = df
        self.base_filename = base_filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    def to_excel_formatted(self):
        """Export to Excel with formatting and multiple sheets"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main data sheet
            self.df.to_excel(writer, sheet_name='Data', index=False)
            
            # Summary statistics sheet (for numeric data)
            numeric_cols = self.df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                summary = self.df[numeric_cols].describe()
                summary.to_excel(writer, sheet_name='Summary_Stats')
            
            # Data info sheet
            info_data = {
                'Metric': ['Total Rows', 'Total Columns', 'Missing Values', 'Numeric Columns', 'Text Columns'],
                'Value': [
                    len(self.df),
                    len(self.df.columns),
                    self.df.isnull().sum().sum(),
                    len(self.df.select_dtypes(include=['number']).columns),
                    len(self.df.select_dtypes(include=['object']).columns)
                ]
            }
            info_df = pd.DataFrame(info_data)
            info_df.to_excel(writer, sheet_name='Data_Info', index=False)
            
            # Format the main data sheet
            workbook = writer.book
            worksheet = writer.sheets['Data']
            
            # Header formatting
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    
    def to_json_structured(self):
        """Export to JSON with metadata"""
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_records': len(self.df),
                'columns': list(self.df.columns),
                'data_types': {col: str(dtype) for col, dtype in self.df.dtypes.items()}
            },
            'data': self.df.to_dict(orient='records')
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def to_sqlite(self):
        """Export to SQLite database"""
        output = io.BytesIO()
        
        # Create in-memory database first
        conn = sqlite3.connect(':memory:')
        
        # Export main data
        self.df.to_sql('data', conn, if_exists='replace', index=False)
        
        # Create metadata table
        metadata = pd.DataFrame({
            'key': ['export_date', 'total_records', 'total_columns'],
            'value': [
                datetime.now().isoformat(),
                str(len(self.df)),
                str(len(self.df.columns))
            ]
        })
        metadata.to_sql('metadata', conn, if_exists='replace', index=False)
        
        # Backup to bytes
        backup_conn = sqlite3.connect(':memory:')
        conn.backup(backup_conn)
        
        # Get the database as bytes
        temp_file = io.BytesIO()
        for line in backup_conn.iterdump():
            temp_file.write(f'{line}\n'.encode('utf-8'))
        
        temp_file.seek(0)
        conn.close()
        backup_conn.close()
        
        return temp_file
    
    def to_csv_clean(self):
        """Export to clean CSV with optimized settings"""
        # Clean data for CSV export
        df_clean = self.df.copy()
        
        # Handle potential CSV issues
        for col in df_clean.select_dtypes(include=['object']).columns:
            df_clean[col] = df_clean[col].astype(str).str.replace(',', ';').str.replace('\n', ' ')
        
        return df_clean.to_csv(index=False, encoding='utf-8')

def load_data(uploaded_file):
    """Load data from uploaded file"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
        elif file_extension == 'json':
            data = json.load(uploaded_file)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame([data])
        else:
            st.error(f"Unsupported file format: {file_extension}")
            return None
            
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def display_data_stats(df):
    """Display data statistics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rows", len(df))
    
    with col2:
        st.metric("Total Columns", len(df.columns))
    
    with col3:
        numeric_cols = len(df.select_dtypes(include=['number']).columns)
        st.metric("Numeric Columns", numeric_cols)
    
    with col4:
        missing_values = df.isnull().sum().sum()
        st.metric("Missing Values", missing_values)

def main():
    st.title("📊 Interactive Data Export Tool")
    st.markdown("Upload CSV, Excel, or JSON files and export them in multiple formats")
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("📁 File Upload")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'xlsx', 'xls', 'json'],
            help="Upload CSV, Excel, or JSON files"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.info(f"File size: {uploaded_file.size / 1024:.1f} KB")
    
    # Main content area
    if uploaded_file is not None:
        # Load data
        with st.spinner("Loading data..."):
            df = load_data(uploaded_file)
        
        if df is not None:
            # Display data statistics
            st.subheader("📈 Data Overview")
            display_data_stats(df)
            
            # Data preview
            st.subheader("👀 Data Preview")
            preview_rows = st.selectbox("Number of rows to preview", [5, 10, 20, 50], index=0)
            st.dataframe(df.head(preview_rows), use_container_width=True)
            
            # Column information
            with st.expander("📋 Column Information"):
                col_info = pd.DataFrame({
                    'Column': df.columns,
                    'Data Type': df.dtypes.astype(str),
                    'Non-Null Count': df.count(),
                    'Null Count': df.isnull().sum(),
                    'Unique Values': df.nunique()
                })
                st.dataframe(col_info, use_container_width=True)
            
            # Export section
            st.subheader("💾 Export Data")
            
            # Initialize exporter
            base_filename = st.text_input(
                "Base filename (optional)", 
                value=f"export_{datetime.now().strftime('%Y%m%d_%H%M')}"
            )
            exporter = StreamlitDataExporter(df, base_filename)
            
            # Export buttons in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📊 Export Excel", use_container_width=True):
                    with st.spinner("Generating Excel file..."):
                        excel_data = exporter.to_excel_formatted()
                        st.download_button(
                            label="Download Excel File",
                            data=excel_data,
                            file_name=f"{base_filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success("✅ Excel file ready for download!")
            
            with col2:
                if st.button("📄 Export CSV", use_container_width=True):
                    csv_data = exporter.to_csv_clean()
                    st.download_button(
                        label="Download CSV File",
                        data=csv_data,
                        file_name=f"{base_filename}.csv",
                        mime="text/csv"
                    )
                    st.success("✅ CSV file ready for download!")
            
            with col3:
                if st.button("🔧 Export JSON", use_container_width=True):
                    json_data = exporter.to_json_structured()
                    st.download_button(
                        label="Download JSON File",
                        data=json_data,
                        file_name=f"{base_filename}.json",
                        mime="application/json"
                    )
                    st.success("✅ JSON file ready for download!")
            
            with col4:
                if st.button("🗄️ Export SQLite", use_container_width=True):
                    with st.spinner("Generating SQLite database..."):
                        sqlite_data = exporter.to_sqlite()
                        st.download_button(
                            label="Download SQLite DB",
                            data=sqlite_data,
                            file_name=f"{base_filename}.db",
                            mime="application/x-sqlite3"
                        )
                        st.success("✅ SQLite database ready for download!")
            
            # Data analysis section
            if len(df.select_dtypes(include=['number']).columns) > 0:
                st.subheader("📊 Quick Analysis")
                
                with st.expander("Statistical Summary"):
                    st.dataframe(df.describe(), use_container_width=True)
                
                # Simple visualization
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if len(numeric_cols) > 0:
                    with st.expander("📈 Data Visualization"):
                        chart_type = st.selectbox("Chart Type", ["Line Chart", "Bar Chart", "Area Chart"])
                        selected_cols = st.multiselect(
                            "Select columns to visualize", 
                            numeric_cols, 
                            default=numeric_cols[:3]  # Default to first 3 numeric columns
                        )
                        
                        if selected_cols:
                            chart_data = df[selected_cols]
                            if chart_type == "Line Chart":
                                st.line_chart(chart_data)
                            elif chart_type == "Bar Chart":
                                st.bar_chart(chart_data)
                            elif chart_type == "Area Chart":
                                st.area_chart(chart_data)
    
    else:
        # Welcome message
        st.info("👆 Please upload a file using the sidebar to get started!")
        
        # Feature list
        st.markdown("""
        ### ✨ Features:
        - 📁 **File Upload**: Support for CSV, Excel (.xlsx, .xls), and JSON files
        - 📊 **Data Preview**: Interactive data exploration with customizable row count
        - 📈 **Statistics**: Automatic data profiling and summary statistics
        - 💾 **Multiple Export Formats**: Excel (with formatting), CSV, JSON (with metadata), SQLite
        - 🎨 **Data Visualization**: Quick charts for numeric data
        - 📋 **Column Analysis**: Detailed information about each column
        
        ### 🚀 How to use:
        1. Upload your data file using the file uploader in the sidebar
        2. Explore your data with the preview and statistics
        3. Choose your export format and download the processed file
        4. Optionally, explore quick visualizations for numeric data
        """)

if __name__ == "__main__":
    main()
