import pandas as pd
import sys

file_path = "4.INVENTORY 30 APRIL-2026 updated.xlsm"

try:
    xl = pd.ExcelFile(file_path, engine='openpyxl')
    print("Sheet names:", xl.sheet_names)
    
    for sheet in xl.sheet_names:
        print(f"\n--- Sheet: {sheet} ---")
        df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl', nrows=5)
        print("Columns:", list(df.columns))
        print("Sample Data:")
        print(df.head(2))
        
except Exception as e:
    print(f"Error reading file: {e}")
