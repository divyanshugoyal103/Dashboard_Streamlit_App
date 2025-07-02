import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Create a streamlit app
st.title("Advanced Data Analytics Dashboard")

# Add a file uploader
uploaded_file = st.file_uploader("Choose a dataset file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file is not None:
    # Load dataset based on file type
    if uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" or uploaded_file.type == "application/vnd.ms-excel":
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.type == "application/json":
        df = pd.read_json(uploaded_file)

    # Display dataset summary
    st.write("Dataset Summary:")
    st.write(df.head())
    st.write(df.info())
    st.write(df.describe())

    # Correlation analysis
    st.write("Correlation Analysis:")
    corr_matrix = df.corr()
    st.write(corr_matrix)
    fig = plt.figure(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm")
    st.pyplot(fig)

    # Regression analysis
    st.write("Regression Analysis:")
    numerical_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    selected_target_col = st.selectbox("Select target column", numerical_cols)
    selected_feature_cols = st.multiselect("Select feature columns", [col for col in numerical_cols if col != selected_target_col])

    if len(selected_feature_cols) > 0:
        X = df[selected_feature_cols]
        y = df[selected_target_col]

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Linear regression
        st.write("Linear Regression:")
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        y_pred = lr_model.predict(X_test)
        st.write("Mean Squared Error:", mean_squared_error(y_test, y_pred))
        st.write("R2 Score:", r2_score(y_test, y_pred))

        # Random forest regression
        st.write("Random Forest Regression:")
        rf_model = RandomForestRegressor()
        rf_model.fit(X_train, y_train)
        y_pred = rf_model.predict(X_test)
        st.write("Mean Squared Error:", mean_squared_error(y_test, y_pred))
        st.write("R2 Score:", r2_score(y_test, y_pred))

        # Feature importance
        st.write("Feature Importance:")
        feature_importances = rf_model.feature_importances_
        feature_importances_df = pd.DataFrame({"Feature": selected_feature_cols, "Importance": feature_importances})
        feature_importances_df = feature_importances_df.sort_values(by="Importance", ascending=False)
        st.write(feature_importances_df)

    # Data visualization
    st.write("Data Visualization:")
    selected_col = st.selectbox("Select a column", df.columns)
    fig = plt.figure(figsize=(8, 6))
    sns.histplot(df[selected_col], kde=True)
    st.pyplot(fig)

    # Description of analysis
    st.write("Description of Analysis:")
    st.write("This analysis performs correlation analysis, regression analysis, and data visualization on the uploaded dataset.")
    st.write("Correlation analysis helps identify relationships between variables.")
    st.write("Regression analysis predicts the target variable based on feature variables.")
    st.write("Data visualization helps understand the distribution of variables.")