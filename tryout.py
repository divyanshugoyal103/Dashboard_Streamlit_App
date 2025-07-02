import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from io import BytesIO

# Create a streamlit app
st.title("Advanced Data Analytics Dashboard")

# Add a file uploader
uploaded_file = st.file_uploader("Choose a dataset file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file is not None:
    try:
        # Load dataset based on file extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == "csv":
            df = pd.read_csv(uploaded_file)
        elif file_extension in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file)
        elif file_extension == "json":
            df = pd.read_json(uploaded_file)
        else:
            st.error("Unsupported file format")
            st.stop()
            
        # Display dataset summary
        st.write("Dataset Preview:")
        st.write(df.head())
        
        with st.expander("Dataset Info"):
            buffer = BytesIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue().decode('utf-8'))
        
        st.write("Descriptive Statistics:")
        st.write(df.describe())

        # Correlation analysis
        st.write("## Correlation Analysis")
        numerical_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        
        if len(numerical_cols) < 2:
            st.warning("Not enough numerical columns for correlation analysis")
        else:
            corr_matrix = df[numerical_cols].corr()
            st.write(corr_matrix)
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", ax=ax)
            st.pyplot(fig)
            plt.close(fig)

        # Regression analysis
        st.write("## Regression Analysis")
        if len(numerical_cols) < 2:
            st.warning("Not enough numerical columns for regression analysis")
        else:
            selected_target_col = st.selectbox("Select target column", numerical_cols)
            available_features = [col for col in numerical_cols if col != selected_target_col]
            selected_feature_cols = st.multiselect("Select feature columns", available_features)

            if len(selected_feature_cols) > 0:
                X = df[selected_feature_cols]
                y = df[selected_target_col]

                # Split data into training and testing sets
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )

                # Linear regression
                st.write("### Linear Regression")
                lr_model = LinearRegression()
                lr_model.fit(X_train, y_train)
                y_pred = lr_model.predict(X_test)
                st.write(f"Mean Squared Error: {mean_squared_error(y_test, y_pred):.4f}")
                st.write(f"R2 Score: {r2_score(y_test, y_pred):.4f}")

                # Random forest regression
                st.write("### Random Forest Regression")
                rf_model = RandomForestRegressor(random_state=42)
                rf_model.fit(X_train, y_train)
                y_pred = rf_model.predict(X_test)
                st.write(f"Mean Squared Error: {mean_squared_error(y_test, y_pred):.4f}")
                st.write(f"R2 Score: {r2_score(y_test, y_pred):.4f}")

                # Feature importance
                st.write("### Feature Importance")
                feature_importances = rf_model.feature_importances_
                feature_importances_df = pd.DataFrame(
                    {"Feature": selected_feature_cols, "Importance": feature_importances}
                ).sort_values(by="Importance", ascending=False)
                st.write(feature_importances_df)

                # Plot feature importance
                fig, ax = plt.subplots(figsize=(8, 4))
                sns.barplot(data=feature_importances_df, x="Importance", y="Feature", ax=ax)
                st.pyplot(fig)
                plt.close(fig)

        # Data visualization
        st.write("## Data Visualization")
        selected_col = st.selectbox("Select a column", df.columns)
        fig, ax = plt.subplots(figsize=(8, 6))
        
        if df[selected_col].dtype in ["int64", "float64"]:
            sns.histplot(df[selected_col], kde=True, ax=ax)
        else:
            sns.countplot(y=selected_col, data=df, ax=ax)
            
        st.pyplot(fig)
        plt.close(fig)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Description of analysis
st.sidebar.write("## About This App")
st.sidebar.write("""
This app performs:
- Correlation analysis (identifies relationships between variables)
- Regression analysis (predicts target variables)
- Data visualization (shows variable distributions)
""")
