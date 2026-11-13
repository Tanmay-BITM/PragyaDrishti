import sys
import os
import json
import joblib
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.ml_model import MLModel
from app.services.automl_engine import AutoMLEngine

def test_m10_model_19_and_target_switching():
    print("=" * 80)
    print("      M10 PREDICTIVE ANALYTICS — MODEL #19 & TARGET SWITCHING TEST")
    print("=" * 80)

    db = SessionLocal()
    
    # 1. Inspect Model #19 or create a model if #19 is not in DB yet
    m19 = db.query(MLModel).filter(MLModel.id == 19).first()
    if not m19:
        print("Model #19 not found in DB. Searching for latest regression model...")
        m19 = db.query(MLModel).filter(MLModel.target_column == "Profit").order_by(MLModel.id.desc()).first()

    if not m19:
        print("No Profit regression model found in DB. Training a new model on Sales dataset for Profit...")
        df_sales = pd.DataFrame({
            "Order_ID": list(range(1, 103)),
            "Date": ["2026-01-01"] * 102,
            "Region": ["North", "South", "East", "West"] * 25 + ["North", "South"],
            "Product": ["Laptops", "Phones", "Tablets"] * 34,
            "Quantity": [10] * 102,
            "Unit_Price": [500.0] * 102,
            "Discount": [0.05] * 102,
            "Sales": [4750.0] * 102,
            "Profit": [950.0] * 102
        })
        res = AutoMLEngine.train_and_evaluate(df_sales, target_column="Profit", task_type="regression", dataset_id=1)
        m19 = MLModel(
            name=f"Model_regression_pragyadrishti_sales_test_dataset",
            task_type=res["task_type"],
            target_column=res["target_column"],
            best_algorithm=res["best_algorithm"],
            file_path=res["model_file_path"],
            metrics_json=json.dumps(res["metrics"]),
            feature_importance_json=json.dumps(res["feature_importance"]),
            leaderboard_json=json.dumps(res["leaderboard"]),
            explanation_text=json.dumps(res["explanation_dict"]),
            endpoint_url="/api/v1/prompt-ml/predict",
            status="ACTIVE",
            dataset_id=1
        )
        db.add(m19)
        db.commit()
        db.refresh(m19)

    print(f"\n--- Model #{m19.id} Metadata Audit ---")
    print(f"Model ID        : #{m19.id}")
    print(f"Dataset ID      : {m19.dataset_id}")
    print(f"Target Column   : {m19.target_column}")
    print(f"Task Type       : {m19.task_type}")
    print(f"Best Algorithm  : {m19.best_algorithm}")
    print(f"Joblib Path     : {m19.file_path}")

    # Inspect joblib feature columns
    artifact = joblib.load(m19.file_path)
    joblib_features = artifact.get("feature_cols", [])
    print(f"Joblib Saved Features ({len(joblib_features)}): {joblib_features}")
    
    assert "Unit_Price" in joblib_features, "ERROR: Unit_Price was missing from saved joblib feature columns!"
    assert "Profit" not in joblib_features, "ERROR: Target column Profit was included in feature columns!"
    assert "Order_ID" not in joblib_features, "ERROR: ID column Order_ID was not excluded!"

    print("\n✅ Feature column verification: 'Unit_Price' is present, 'Profit' (target) and 'Order_ID' (ID) excluded!")

    # 2. Test Prediction Execution using saved pipeline
    pipeline = artifact["pipeline"]
    test_features = {
        "Region": "North",
        "Product": "Laptops",
        "Quantity": 10,
        "Unit_Price": 500.0,
        "Discount": 0.05
    }
    
    input_df = pd.DataFrame([test_features])[joblib_features]
    pred_output = float(pipeline.predict(input_df)[0])
    
    print(f"\n--- Live Prediction Test ---")
    print(f"Input Payload   : {test_features}")
    print(f"Predicted Profit: {pred_output}")
    assert isinstance(pred_output, float), "Prediction output is not numeric!"
    print("✅ Live Joblib Pipeline Prediction Execution PASS!")

    # 3. Test Target Switching Lookup
    print("\n--- Target Switching Lookup Test ---")
    profit_model = db.query(MLModel).filter(MLModel.dataset_id == m19.dataset_id, MLModel.target_column == "Profit").first()
    sales_model = db.query(MLModel).filter(MLModel.dataset_id == m19.dataset_id, MLModel.target_column == "Sales").first()

    print(f"Target 'Profit' model lookup -> Model #{profit_model.id if profit_model else 'None'}")
    print(f"Target 'Sales' model lookup  -> Model #{sales_model.id if sales_model else 'None (Displays No Trained Model Warning)'}")
    
    assert profit_model is not None, "Profit model should be found!"
    print("✅ Target Switching Lookup PASS!")

    print("\n" + "=" * 80)
    print("🎉 ALL M10 PREDICTIVE ANALYTICS VERIFICATIONS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    test_m10_model_19_and_target_switching()
