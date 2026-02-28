import pandas as pd
import os

file_path = "d:/ARFA PROJECTS/Decodex Dalmia/DecodeX_VoltRide_Dataset.xlsx"

try:
    xls = pd.ExcelFile(file_path)
    with open("data_schema.txt", "w") as f:
        f.write(f"Sheet names: {xls.sheet_names}\n")
        
        for sheet_name in xls.sheet_names:
            f.write(f"\n--- Sheet: {sheet_name} ---\n")
            df = pd.read_excel(xls, sheet_name=sheet_name, nrows=3)
            f.write(f"Columns: {list(df.columns)}\n")
            f.write(f"First row: {df.iloc[0].to_dict()}\n")
except Exception as e:
    with open("data_schema.txt", "w") as f:
        f.write(f"Error reading Excel file: {e}\n")
