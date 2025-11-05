import pandas as pd
import json

# Read the Excel file
file_path = r"d:\Gawean Rebinmas\Monitoring Database\Plantware_Auto_Report\Daftar_Upah_Reporting\Create_Template_Using_Excel\Template\Template_Daftar_Upah.xlsx"

try:
    # Read with header=None to see all data
    df = pd.read_excel(file_path, header=None)

    print("Full Excel structure analysis:")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    # Display first 15 rows to understand the structure
    print("\nFirst 15 rows:")
    for i in range(min(15, len(df))):
        row_data = []
        for j in range(min(10, len(df.columns))):  # Show first 10 columns
            val = df.iloc[i, j]
            if pd.isna(val):
                row_data.append("NULL")
            else:
                row_data.append(str(val)[:20])  # Truncate long values
        print(f"Row {i}: {row_data}")

    # Try to identify header rows
    print("\nLooking for potential headers:")
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        non_null_count = row.notna().sum()
        if non_null_count > 5:  # If row has more than 5 non-null values, it might be important
            print(f"Row {i} has {non_null_count} non-null values")
            for j in range(min(15, len(df.columns))):
                if not pd.isna(df.iloc[i, j]):
                    print(f"  Col {j}: {df.iloc[i, j]}")

except Exception as e:
    print(f"Error reading Excel file: {e}")