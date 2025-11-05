import pandas as pd

file_path = r"d:\Gawean Rebinmas\Monitoring Database\Plantware_Auto_Report\Daftar_Upah_Reporting\Create_Template_Using_Excel\Template\Template_Daftar_Upah.xlsx"

try:
    df = pd.read_excel(file_path, header=None)

    # Focus on rows 4-7 which seem to contain headers
    print("Header rows analysis:")
    for i in range(4, 8):
        print(f"\nRow {i}:")
        for j in range(len(df.columns)):
            val = df.iloc[i, j]
            if not pd.isna(val) and str(val).strip():
                print(f"  Column {j:2d}: {val}")

    # Look for sample data rows
    print("\n\nSample data rows (starting from row 15):")
    for i in range(15, min(20, len(df))):
        print(f"\nRow {i}:")
        has_data = False
        for j in range(min(20, len(df.columns))):
            val = df.iloc[i, j]
            if not pd.isna(val) and str(val).strip():
                print(f"  Column {j:2d}: {val}")
                has_data = True
        if not has_data:
            print("  (No data in this row)")

except Exception as e:
    print(f"Error: {e}")