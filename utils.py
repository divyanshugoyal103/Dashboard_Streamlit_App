import pandas as pd

def load_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        return df, None
    except Exception as e:
        return None, str(e)

def get_column_types(df):
    return df.select_dtypes(include='number').columns.tolist(), df.select_dtypes(include='object').columns.tolist()
