import pandas as pd
import json

# Read the Excel file
file_path = r"d:\Gawean Rebinmas\Monitoring Database\Plantware_Auto_Report\Daftar_Upah_Reporting\Create_Template_Using_Excel\Template\Template_Daftar_Upah.xlsx"

try:
    # Read all sheets
    excel_file = pd.ExcelFile(file_path)
    print(f"Sheet names: {excel_file.sheet_names}")

    # Read each sheet and display structure
    for sheet_name in excel_file.sheet_names:
        print(f"\n=== Sheet: {sheet_name} ===")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nData types:")
        print(df.dtypes)

except Exception as e:
    print(f"Error reading Excel file: {e}")