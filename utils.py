import pandas as pd

def load_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, parse_dates=True, infer_datetime_format=True)
        return df, None
    except Exception as e:
        return None, str(e)

def get_column_types(df):
    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(include='object').columns.tolist()
    return num_cols, cat_cols
