import sys
import os
import json
import joblib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.ml_model import MLModel

def main():
    db = SessionLocal()
    models = db.query(MLModel).all()
    print(f"Total ML Models in DB: {len(models)}")
    for m in models:
        print(f"\nModel ID #{m.id}: {m.name}")
        print(f"  Dataset ID: {m.dataset_id}")
        print(f"  Target Column: {m.target_column}")
        print(f"  Task Type: {m.task_type}")
        print(f"  Best Algorithm: {m.best_algorithm}")
        print(f"  File Path: {m.file_path} (Exists: {os.path.exists(m.file_path)})")
        
        if m.explanation_text:
            try:
                exp = json.loads(m.explanation_text)
                print(f"  Explanation used_features: {exp.get('used_features')}")
            except Exception as e:
                print(f"  Explanation JSON parse error: {e}")
                
        if m.feature_importance_json:
            try:
                fi = json.loads(m.feature_importance_json)
                print(f"  Feature Importance keys: {list(fi.keys())}")
            except Exception as e:
                print(f"  Feature Importance JSON parse error: {e}")

        if os.path.exists(m.file_path):
            try:
                artifact = joblib.load(m.file_path)
                print(f"  Joblib artifact feature_cols: {artifact.get('feature_cols')}")
                print(f"  Joblib artifact numeric_features: {artifact.get('numeric_features')}")
                print(f"  Joblib artifact categorical_features: {artifact.get('categorical_features')}")
            except Exception as e:
                print(f"  Joblib load error: {e}")

if __name__ == "__main__":
    main()
