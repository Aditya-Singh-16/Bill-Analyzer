import pandas as pd

def classify_bill(row):
    if row['Meter Reading'] == 0:
        return "NR"
    elif row['Meter Status'] == "Faulty":
        return "MR"
    else:
        return "OK"

def process_bill(df):
    df['Bill_Status'] = df.apply(classify_bill, axis=1)
    return df
