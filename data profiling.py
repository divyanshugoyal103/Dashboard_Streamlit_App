# You must install these libraries to run the app:
# pip install streamlit pandas ydata-profiling openpyxl

import streamlit as st
import pandas as pd
from ydata_profiling import ProfileReport
import tempfile
import json
from datetime import datetime

def main():
    """
    Main function to create and run the Streamlit data profiler app.
    """
    st.set_page_config(
        page_title="Data Profiler App",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- Header and Introduction ---
    st.title("📊 Data Upload & Profiler")
    st.markdown("Upload your CSV or Excel file to get a detailed, interactive data quality report.")

    # --- File Upload Section ---
    uploaded_file = st.file_uploader(
        "**Step 1: Upload Your Data**",
        type=["csv", "xlsx", "xls"],
        help="Drag and drop your file here, or click to browse. Supports CSV and Excel files."
    )

    if uploaded_file:
        try:
            with st.spinner("⏳ Reading your file..."):
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                if file_extension == 'csv':
                    df = pd.read_csv(uploaded_file)
                elif file_extension in ['xlsx', 'xls']:
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
                else:
                    st.error("Unsupported file format. Please upload a CSV or Excel file.")
                    return

            st.success("🎉 File uploaded successfully!")

            if df.empty:
                st.warning("The uploaded file is empty or could not be parsed.")
                return

            # --- Data Preview ---
            st.markdown("---")
            st.header("🔍 Data Preview")
            st.write(f"The dataset contains **{df.shape[0]} rows** and **{df.shape[1]} columns**.")
            st.dataframe(df.head())

            # --- Data Profiling ---
            st.markdown("---")
            st.header("📊 Generating Profile Report...")
            
            with st.spinner("Analyzing your data, this may take a moment..."):
                profile = ProfileReport(
                    df, 
                    title=f"Profile Report for {uploaded_file.name}", 
                    explorative=True
                )
            
            st.success("✅ Profile report generated!")

            # --- View and Export Report ---
            st.markdown("---")
            st.header("📄 Interactive Profile Report")
            st.info("The report is an interactive HTML file. You can view it directly or download it.")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as fp:
                profile.to_file(fp.name)
                
                st.components.v1.html(profile.to_html(), height=800, scrolling=True)

                with open(fp.name, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Profile Report as HTML",
                        data=f,
                        file_name=f"profile_report_{uploaded_file.name.split('.')[0]}.html",
                        mime="text/html"
                    )

            st.markdown("---")
            st.header("JSON Report")
            json_report = profile.get_description().as_json()
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"profile_{uploaded_file.name.split('.')[0]}_{timestamp}.json"

            st.download_button(
                label="⬇️ Download Full Profile Report as JSON",
                data=json_report,
                file_name=filename,
                mime="application/json"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.info("Please check if your file format is correct and the data is not corrupt.")

if __name__ == "__main__":
    main()

