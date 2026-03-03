from datetime import datetime
import pandas as pd

def calculate_ageing(df):
    today = datetime.today()
    df['Due Date'] = pd.to_datetime(df['Due Date'])
    df['Ageing_Days'] = (today - df['Due Date']).dt.days
    return df
