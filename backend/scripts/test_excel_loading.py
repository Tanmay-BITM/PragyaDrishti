import sys
import os
import pandas as pd

# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.dataset_loader import DatasetLoader

def main():
    print("=" * 70)
    print("  EXCEL & CSV DATASET LOADING VERIFICATION SCRIPT")
    print("=" * 70)

    # Test 1: Generate synthetic XLSX file
    test_xlsx_path = os.path.join(os.path.dirname(__file__), "temp_sales_test.xlsx")
    df_sales = pd.DataFrame({
        "Order_ID": [101, 102, 103, 104, 105],
        "Date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
        "Region": ["North", "South", "East", "West", "North"],
        "Product": ["Laptops", "Phones", "Tablets", "Monitors", "Accessories"],
        "Quantity": [10, 20, 15, 8, 25],
        "Unit_Price": [1200, 800, 500, 300, 50],
        "Discount": [0.05, 0.1, 0.0, 0.15, 0.05],
        "Sales": [11400, 14400, 7500, 2040, 1187.5],
        "Profit": [2280, 2880, 1500, 306, 237.5]
    })

    df_sales.to_excel(test_xlsx_path, engine="openpyxl", index=False)
    print(f"\nCreated synthetic test XLSX at: {test_xlsx_path}")

    # Test loading synthetic XLSX
    print("\n--- Testing DatasetLoader.read_dataset_file on XLSX ---")
    loaded_xlsx_df = DatasetLoader.read_dataset_file(test_xlsx_path)
    assert not loaded_xlsx_df.empty
    assert loaded_xlsx_df.shape == (5, 9)
    assert "Sales" in loaded_xlsx_df.columns
    print("✅ XLSX Loading Successful!")

    # Test 2: Generate synthetic CSV file
    test_csv_path = os.path.join(os.path.dirname(__file__), "temp_sales_test.csv")
    df_sales.to_csv(test_csv_path, index=False)
    print(f"\nCreated synthetic test CSV at: {test_csv_path}")

    print("\n--- Testing DatasetLoader.read_dataset_file on CSV ---")
    loaded_csv_df = DatasetLoader.read_dataset_file(test_csv_path)
    assert not loaded_csv_df.empty
    assert loaded_csv_df.shape == (5, 9)
    assert "Sales" in loaded_csv_df.columns
    print("✅ CSV Loading Successful!")

    # Test 3: Check uploaded files in storage/uploads if any
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "uploads"))
    if os.path.exists(uploads_dir):
        files = os.listdir(uploads_dir)
        print(f"\n--- Checking {len(files)} files in storage/uploads ---")
        for f in files:
            if f.endswith(('.csv', '.xlsx', '.xls')):
                full_p = os.path.join(uploads_dir, f)
                try:
                    df = DatasetLoader.read_dataset_file(full_p)
                    print(f"  File '{f}': {df.shape[0]} rows × {df.shape[1]} cols -> ✅ READ OK")
                except Exception as e:
                    print(f"  File '{f}': ❌ FAILED - {e}")

    # Clean up temp files
    if os.path.exists(test_xlsx_path):
        os.remove(test_xlsx_path)
    if os.path.exists(test_csv_path):
        os.remove(test_csv_path)

    print("\n" + "=" * 70)
    print("🎉 ALL DATASET LOADING TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
