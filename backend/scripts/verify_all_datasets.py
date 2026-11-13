import sys
import os
import pandas as pd
import numpy as np

# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.automl_engine import AutoMLEngine
from app.services.data_cleaner import DataCleaner

def run_verification():
    print("=" * 80)
    print("   PRAGYADRISHTI AUTOML END-TO-END DATASET VERIFICATION RUNNER")
    print("=" * 80)

    test_datasets = [
        {
            "name": "1. Student Dataset (CGPA - Regression)",
            "df": pd.DataFrame({
                "student_id": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112],
                "attendance": [90, 85, 92, 70, 60, 95, 88, 75, 82, 91, 65, 84],
                "study_hours": [5.5, 4.0, 6.0, 2.5, 1.5, 7.0, 5.0, 3.0, 4.5, 6.5, 2.0, 4.2],
                "CGPA": [8.8, 7.9, 9.2, 6.5, 5.8, 9.6, 8.4, 6.9, 8.0, 9.1, 6.0, 8.1]
            }),
            "target": "CGPA",
            "task": "regression"
        },
        {
            "name": "2. Student Dataset (Placement - Classification)",
            "df": pd.DataFrame({
                "student_code": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12"],
                "cgpa": [9.0, 6.0, 8.5, 5.5, 9.2, 7.0, 8.8, 6.2, 7.5, 9.5, 5.8, 8.2],
                "internships": [2, 0, 1, 0, 3, 1, 2, 0, 1, 2, 0, 1],
                "Placement": ["Placed", "Not Placed", "Placed", "Not Placed", "Placed", "Not Placed", "Placed", "Not Placed", "Placed", "Placed", "Not Placed", "Placed"]
            }),
            "target": "Placement",
            "task": "classification"
        },
        {
            "name": "3. Sales Dataset (Sales - Regression)",
            "df": pd.DataFrame({
                "Store_ID": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "Advertising_Spend": [1000, 2500, 1500, 3000, 4500, 2000, 3500, 5000, 1200, 2800, 4000, 1800],
                "Region": ["North", "South", "North", "East", "West", "East", "West", "North", "South", "East", "West", "South"],
                "Sales": [15000, 28000, 21000, 35000, 48000, 24000, 39000, 52000, 18000, 31000, 44000, 22000]
            }),
            "target": "Sales",
            "task": "regression"
        },
        {
            "name": "4. Customer Churn Dataset (Churn - Classification)",
            "df": pd.DataFrame({
                "Customer_UUID": ["u1", "u2", "u3", "u4", "u5", "u6", "u7", "u8", "u9", "u10", "u11", "u12"],
                "Monthly_Charges": [29.8, 56.9, 105.5, 42.3, 89.1, 75.0, 99.4, 35.6, 68.2, 110.0, 48.0, 95.0],
                "Contract": ["Month-to-month", "One year", "Month-to-month", "Two year", "Month-to-month", "One year", "Month-to-month", "Two year", "Month-to-month", "Month-to-month", "One year", "Month-to-month"],
                "Churn": ["No", "No", "Yes", "No", "Yes", "No", "Yes", "No", "No", "Yes", "No", "Yes"]
            }),
            "target": "Churn",
            "task": "classification"
        },
        {
            "name": "5. Dataset with Missing Values",
            "df": pd.DataFrame({
                "age": [25, np.nan, 35, 45, 50, 28, 32, np.nan, 40, 55, 60, 22],
                "salary": [50000, 60000, np.nan, 80000, 100000, 55000, 68000, 72000, np.nan, 110000, 125000, 45000],
                "purchased": ["No", "Yes", "No", "Yes", "Yes", "No", "No", "Yes", "Yes", "Yes", "Yes", "No"]
            }),
            "target": "purchased",
            "task": "classification"
        },
        {
            "name": "6. Dataset with Categorical Features",
            "df": pd.DataFrame({
                "education": ["Bachelors", "Masters", "PhD", "Bachelors", "HighSchool", "Bachelors", "Masters", "PhD", "Bachelors", "Masters", "HighSchool", "PhD"],
                "city": ["NY", "SF", "NY", "Austin", "SF", "Austin", "NY", "SF", "Austin", "NY", "Austin", "SF"],
                "income": [65000, 95000, 120000, 58000, 42000, 62000, 90000, 130000, 60000, 98000, 45000, 135000]
            }),
            "target": "income",
            "task": "regression"
        },
        {
            "name": "7. Dataset with Duplicate Rows",
            "df": pd.DataFrame({
                "feature1": [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3],
                "feature2": [10, 20, 30, 10, 20, 30, 10, 20, 30, 10, 20, 30],
                "target": [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0]
            }),
            "target": "target",
            "task": "classification"
        },
        {
            "name": "8. Dataset with ID Column",
            "df": pd.DataFrame({
                "User_ID_Code": [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012],
                "X1": [1.2, 2.3, 3.4, 4.5, 5.6, 6.7, 7.8, 8.9, 9.0, 10.1, 11.2, 12.3],
                "Target_Score": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
            }),
            "target": "Target_Score",
            "task": "regression"
        }
    ]

    all_passed = True
    for idx, t in enumerate(test_datasets, 1):
        print(f"\n--- Testing Dataset {idx}: {t['name']} ---")
        df = t["df"]
        
        # Pre-clean if dataset 7
        if "Duplicate" in t["name"]:
            df, report = DataCleaner.auto_clean(df, remove_duplicates=True)
            print(f"Auto-cleaned duplicate rows: {report['duplicates_removed']}")

        try:
            result = AutoMLEngine.train_and_evaluate(
                df=df,
                target_column=t["target"],
                task_type=t["task"],
                dataset_id=idx
            )
            
            successful_models = [m["algorithm"] for m in result["leaderboard"] if m.get("status") == "SUCCESS"]
            best_model = result["best_algorithm"]
            metrics = result["metrics"]

            print(f"  Dataset Shape : {df.shape}")
            print(f"  Target Column : {result['target_column']}")
            print(f"  Detected Task : {result['task_type']}")
            print(f"  Used Features : {result['used_features']}")
            print(f"  Models Trained: {len(successful_models)} / {len(result['leaderboard'])} models succeeded")
            print(f"  Best Model    : {best_model}")
            print(f"  Best Metrics  : {metrics}")
            print(f"  STATUS        : ✅ PASSED")
            
        except Exception as e:
            print(f"  STATUS        : ❌ FAILED - Error: {e}")
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL 8 DATASET SCENARIOS VERIFIED SUCCESSFULLY WITH 100% SUCCESS!")
    else:
        print("❌ SOME DATASET SCENARIOS FAILED VERIFICATION.")
    print("=" * 80)

if __name__ == "__main__":
    run_verification()
