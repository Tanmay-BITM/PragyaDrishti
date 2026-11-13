import os
import json
import joblib
import logging
import traceback
import time
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC, SVR
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, r2_score, mean_squared_error, mean_absolute_error
)

from app.core.config import settings

# Configure logger
logger = logging.getLogger("AutoMLEngine")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s'))
    logger.addHandler(ch)

class AutoMLEngine:
    @staticmethod
    def identify_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
        """Classifies columns into numeric, categorical, datetime, boolean, ID, and constant types."""
        numeric_cols = []
        categorical_cols = []
        datetime_cols = []
        boolean_cols = []
        id_cols = []
        constant_cols = []

        total_rows = len(df)

        for col in df.columns:
            series = df[col]
            nunique = series.nunique(dropna=True)
            col_lower = str(col).lower()

            # 1. Constant column (0 or 1 unique value)
            if nunique <= 1:
                constant_cols.append(col)
                continue

            # 2. Datetime column
            if pd.api.types.is_datetime64_any_dtype(series):
                datetime_cols.append(col)
                continue

            # Attempt datetime parsing if object/string and looks like date
            if pd.api.types.is_string_dtype(series) and any(kw in col_lower for kw in ['date', 'time', 'timestamp', 'created_at']):
                try:
                    pd.to_datetime(series, errors='raise')
                    datetime_cols.append(col)
                    continue
                except Exception:
                    pass

            # 3. Boolean column
            if pd.api.types.is_bool_dtype(series) or (nunique == 2 and set(series.dropna().unique()).issubset({0, 1, '0', '1', True, False, 'True', 'False', 'yes', 'no', 'Yes', 'No'})):
                boolean_cols.append(col)
                continue

            # 4. ID-like column (Strict identification based on name + cardinality)
            is_id_keyword = any(kw in col_lower for kw in ['id', 'uuid', 'guid', 'index', 'code', '#', 'student_id', 'user_id', 'customer_id', 'order_id'])
            if (is_id_keyword and nunique >= max(5, int(0.8 * total_rows))) or (nunique == total_rows and total_rows >= 10 and not pd.api.types.is_float_dtype(series)):
                id_cols.append(col)
                continue

            # 5. Numeric vs Categorical
            if pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)

        return {
            "numeric": numeric_cols,
            "categorical": categorical_cols,
            "datetime": datetime_cols,
            "boolean": boolean_cols,
            "id_cols": id_cols,
            "constant_cols": constant_cols
        }

    @staticmethod
    def extract_real_feature_importance(
        best_model_pipeline: Pipeline,
        X_train_raw: pd.DataFrame,
        X_test_raw: pd.DataFrame,
        y_test: np.ndarray,
        usable_features: List[str],
        num_features: List[str],
        cat_features: List[str],
        task_type: str
    ) -> Dict[str, float]:
        """Extracts real feature importances using native tree/linear importances or permutation importance,
        mapping one-hot encoded features back to their original source columns.
        """
        preprocessor = best_model_pipeline.named_steps['preprocessor']
        estimator = best_model_pipeline.named_steps['model']

        raw_column_importance = {col: 0.0 for col in usable_features}
        has_native_imp = hasattr(estimator, "feature_importances_") or hasattr(estimator, "coef_")

        if has_native_imp:
            try:
                if hasattr(estimator, "feature_importances_"):
                    importances = estimator.feature_importances_
                else:
                    coefs = estimator.coef_
                    importances = np.abs(coefs).mean(axis=0) if coefs.ndim > 1 else np.abs(coefs).flatten()

                try:
                    tf_names = preprocessor.get_feature_names_out()
                except Exception:
                    tf_names = None

                if tf_names is not None and len(tf_names) == len(importances):
                    for tf_name, imp_val in zip(tf_names, importances):
                        clean_tf = str(tf_name).split('__')[-1]
                        matched = False
                        for raw_col in usable_features:
                            if clean_tf == raw_col or clean_tf.startswith(f"{raw_col}_"):
                                raw_column_importance[raw_col] += float(imp_val)
                                matched = True
                                break
                        if not matched:
                            for raw_col in usable_features:
                                if raw_col in clean_tf:
                                    raw_column_importance[raw_col] += float(imp_val)
                                    break
                else:
                    all_feats = num_features + cat_features
                    for i, feat in enumerate(all_feats[:len(importances)]):
                        if feat in raw_column_importance:
                            raw_column_importance[feat] += float(importances[i])
            except Exception as err:
                logger.warning(f"Native feature importance extraction failed: {err}")
                has_native_imp = False

        # Permutation Importance for models without native importances (MLP, SVR, SVC, Naive Bayes)
        if not has_native_imp:
            try:
                from sklearn.inspection import permutation_importance
                scoring = 'r2' if task_type == 'regression' else 'f1_weighted'
                perm_res = permutation_importance(
                    best_model_pipeline, X_test_raw, y_test, n_repeats=5, random_state=42, scoring=scoring
                )
                for col, imp_val in zip(usable_features, perm_res.importances_mean):
                    raw_column_importance[col] = max(0.0, float(imp_val))
            except Exception as perm_err:
                logger.warning(f"Permutation importance calculation failed: {perm_err}")
                return {}

        # Normalize to 100%
        total_imp = sum(raw_column_importance.values())
        if total_imp > 0:
            return {col: round(val / total_imp, 4) for col, val in raw_column_importance.items()}
        return {}

    @staticmethod
    def train_and_evaluate(
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        feature_columns: Optional[List[str]] = None,
        task_type: Optional[str] = "auto",
        target_selection_source: Optional[str] = "Automatically inferred from dataset schema",
        dataset_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Dataset-agnostic AutoML training pipeline with structured logging, 9-point validation,
        real feature importance mapping, and explanation panel.
        """
        logger.info(f"=== STAGE 1: DATASET INGESTION ===")
        logger.info(f"Dataset ID: {dataset_id} | Shape: {df.shape} | Columns: {list(df.columns)}")

        if df.empty:
            raise ValueError("Dataset is empty (0 rows). Please upload a valid dataset.")

        if len(df.columns) < 2:
            raise ValueError("Insufficient Features for ML Training. Supervised machine learning requires at least one feature column and one target column. Please upload a dataset containing at least two usable columns.")

        df = df.replace([np.inf, -np.inf], np.nan)

        logger.info(f"=== STAGE 2: SCHEMA DETECTION & TYPE CLASSIFICATION ===")
        col_types = AutoMLEngine.identify_column_types(df)

        logger.info(f"=== STAGE 3: TARGET SELECTION & VALIDATION ===")
        if target_column:
            if target_column not in df.columns:
                raise ValueError(f"Target column '{target_column}' does not exist in the selected dataset. Available columns: {list(df.columns)}")
        else:
            candidates = [c for c in df.columns if c not in col_types["id_cols"] and c not in col_types["constant_cols"]]
            if not candidates:
                raise ValueError("Could not automatically infer target column. All columns are ID or constant columns.")
            target_column = candidates[-1]

        target_series = df[target_column].dropna()
        if target_series.empty:
            raise ValueError(f"Target column '{target_column}' is completely empty (all missing values).")

        target_unique_count = target_series.nunique()
        if target_unique_count <= 1:
            val_str = str(target_series.iloc[0])
            raise ValueError(f"Target column '{target_column}' has no variation (contains only 1 unique value: '{val_str}'). Supervised ML requires target variation with at least 2 distinct values.")

        if target_column in col_types["datetime"]:
            raise ValueError(f"Target column '{target_column}' is datetime type. Please select a numeric or categorical column.")

        logger.info(f"=== STAGE 4: TASK TYPE INFERENCE ===")
        if not task_type or task_type == "auto":
            is_numeric_target = pd.api.types.is_numeric_dtype(df[target_column])
            if is_numeric_target and target_unique_count > 10:
                task_type = "regression"
            else:
                task_type = "classification"

        if task_type == "classification" and target_unique_count < 2:
            raise ValueError(f"Classification requires at least 2 distinct target classes. Target column '{target_column}' contains only {target_unique_count} class.")

        logger.info(f"=== STAGE 5: FEATURE SELECTION & LEAKAGE AUDIT ===")
        excluded_features_info = []

        # Data Leakage & ID Column Checks
        if feature_columns:
            candidate_features = [c for c in feature_columns if c in df.columns and c != target_column]
        else:
            candidate_features = [c for c in df.columns if c != target_column]

        usable_features = []
        for col in candidate_features:
            col_lower = str(col).lower()
            tgt_lower = str(target_column).lower()

            # Target Leakage Check
            if col_lower == f"{tgt_lower}_target" or col_lower == f"target_{tgt_lower}":
                excluded_features_info.append({
                    "column": col,
                    "reason": f"Target leakage: column '{col}' is directly derived from target '{target_column}'."
                })
                continue

            # ID Column Check
            if col in col_types["id_cols"]:
                excluded_features_info.append({
                    "column": col,
                    "reason": f"Identifier column with near-unique cardinality ({df[col].nunique()} unique values)."
                })
                continue

            # Constant Column Check
            if col in col_types["constant_cols"]:
                excluded_features_info.append({
                    "column": col,
                    "reason": "Constant column with no variation (1 unique value)."
                })
                continue

            usable_features.append(col)

        if not usable_features:
            raise ValueError("No usable feature columns remaining after removing target, ID, and constant columns. Please upload a dataset with at least one informative feature column.")

        clean_df = df.dropna(subset=[target_column]).copy()
        if len(clean_df) < 5:
            raise ValueError(f"Dataset contains insufficient valid rows ({len(clean_df)}) for ML training after removing missing target rows. Minimum 5 valid rows required.")

        X = clean_df[usable_features].copy()
        y = clean_df[target_column].copy()

        # Date handling
        date_derived_features = []
        for dt_col in col_types["datetime"]:
            if dt_col in X.columns:
                try:
                    dt_series = pd.to_datetime(X[dt_col], errors='coerce')
                    X[f"{dt_col}_year"] = dt_series.dt.year.fillna(2026).astype(int)
                    X[f"{dt_col}_month"] = dt_series.dt.month.fillna(1).astype(int)
                    X[f"{dt_col}_day"] = dt_series.dt.day.fillna(1).astype(int)
                    X[f"{dt_col}_dayofweek"] = dt_series.dt.dayofweek.fillna(0).astype(int)
                    X = X.drop(columns=[dt_col])
                    usable_features = [c for c in X.columns]
                    date_derived_features.append(f"Decomposed date column '{dt_col}' into year, month, day, dayofweek components.")
                except Exception:
                    X = X.drop(columns=[dt_col])
                    usable_features = [c for c in X.columns]

        num_features = X.select_dtypes(include=[np.number]).columns.tolist()
        cat_features = X.select_dtypes(exclude=[np.number]).columns.tolist()

        logger.info(f"=== STAGE 6: PREPROCESSING & DATA SPLIT ===")
        test_size = 0.2 if len(clean_df) >= 20 else 0.1
        X_train_raw, X_test_raw, y_train_raw, y_test_raw = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        leaderboard = []
        best_model_name = ""
        best_model_pipeline = None
        best_score = -9999999.0
        label_encoder = None

        def make_preprocessor():
            transformers = []
            if num_features:
                transformers.append(('num', Pipeline([
                    ('imputer', SimpleImputer(strategy='median')),
                    ('scaler', StandardScaler())
                ]), num_features))
            if cat_features:
                transformers.append(('cat', Pipeline([
                    ('imputer', SimpleImputer(strategy='most_frequent')),
                    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
                ]), cat_features))
            return ColumnTransformer(transformers=transformers)

        logger.info(f"=== STAGE 7: MODEL TRAINING & CV LOOP ===")

        warnings_list = []
        if len(clean_df) < 30:
            warnings_list.append(f"Small dataset ({len(clean_df)} rows): model cross-validation metrics may be unstable.")

        primary_metric_label = "Cross-Validated R²" if task_type == "regression" else "Cross-Validated F1-Score"

        if task_type == "classification":
            label_encoder = LabelEncoder()
            y_train = label_encoder.fit_transform(y_train_raw.astype(str))
            y_test = label_encoder.transform(y_test_raw.astype(str))

            num_classes = len(np.unique(y_train))
            class_counts = np.bincount(y_train)
            min_class_count = int(np.min(class_counts)) if len(class_counts) > 0 else 0

            candidate_models = {
                "Random Forest Classifier": RandomForestClassifier(n_estimators=100, random_state=42),
                "Gradient Boosting Classifier": GradientBoostingClassifier(random_state=42),
                "Decision Tree Classifier": DecisionTreeClassifier(random_state=42),
                "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
                "Support Vector Classifier (SVM)": SVC(probability=True, random_state=42),
                "Gaussian Naive Bayes": GaussianNB(),
                "Neural Network (MLP)": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=400, random_state=42)
            }

            try:
                from xgboost import XGBClassifier
                candidate_models["XGBoost Classifier"] = XGBClassifier(eval_metric='logloss', random_state=42)
            except Exception:
                pass

            try:
                from lightgbm import LGBMClassifier
                candidate_models["LightGBM Classifier"] = LGBMClassifier(random_state=42, verbose=-1)
            except Exception:
                pass

            try:
                from catboost import CatBoostClassifier
                candidate_models["CatBoost Classifier"] = CatBoostClassifier(verbose=0, random_seed=42)
            except Exception:
                pass

            n_splits = min(5, len(X_train_raw), min_class_count)

            for name, model_instance in candidate_models.items():
                start_time = time.time()
                try:
                    full_pipeline = Pipeline([
                        ('preprocessor', make_preprocessor()),
                        ('model', model_instance)
                    ])

                    cv_score = None
                    if n_splits >= 2:
                        try:
                            scores = cross_val_score(full_pipeline, X_train_raw, y_train, cv=n_splits, scoring='f1_weighted')
                            cv_score = round(float(np.mean(scores)), 4)
                        except Exception as cv_err:
                            logger.warning(f"CV calculation failed for {name}: {cv_err}")

                    full_pipeline.fit(X_train_raw, y_train)
                    preds = full_pipeline.predict(X_test_raw)
                    train_dur = round(time.time() - start_time, 3)

                    acc = round(float(accuracy_score(y_test, preds)), 4)
                    f1 = round(float(f1_score(y_test, preds, average='weighted', zero_division=0)), 4)
                    prec = round(float(precision_score(y_test, preds, average='weighted', zero_division=0)), 4)
                    rec = round(float(recall_score(y_test, preds, average='weighted', zero_division=0)), 4)
                    cm = confusion_matrix(y_test, preds).tolist()

                    roc_auc = None
                    if hasattr(model_instance, "predict_proba") and num_classes == 2:
                        try:
                            proba = full_pipeline.predict_proba(X_test_raw)[:, 1]
                            roc_auc = round(float(roc_auc_score(y_test, proba)), 4)
                        except Exception:
                            pass

                    item = {
                        "algorithm": name,
                        "status": "SUCCESS",
                        "cv_score": cv_score,
                        "accuracy": acc,
                        "f1_score": f1,
                        "precision": prec,
                        "recall": rec,
                        "roc_auc": roc_auc,
                        "confusion_matrix": cm,
                        "training_time_sec": train_dur,
                        "primary_score": cv_score if cv_score is not None else f1
                    }
                    leaderboard.append(item)

                    if item["primary_score"] > best_score:
                        best_score = item["primary_score"]
                        best_model_name = name
                        best_model_pipeline = full_pipeline

                except Exception as err:
                    tb_str = traceback.format_exc()
                    leaderboard.append({
                        "algorithm": name,
                        "status": "FAILED",
                        "reason": str(err),
                        "traceback": tb_str,
                        "primary_score": -999.0
                    })

        else: # Regression
            y_train = y_train_raw.astype(float).values
            y_test = y_test_raw.astype(float).values

            candidate_models = {
                "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42),
                "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=42),
                "Decision Tree Regressor": DecisionTreeRegressor(random_state=42),
                "Linear Regression": LinearRegression(),
                "Ridge Regressor": Ridge(),
                "Support Vector Regressor (SVR)": SVR(),
                "Neural Network Regressor (MLP)": MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=400, random_state=42)
            }

            try:
                from xgboost import XGBRegressor
                candidate_models["XGBoost Regressor"] = XGBRegressor(random_state=42)
            except Exception:
                pass

            try:
                from lightgbm import LGBMRegressor
                candidate_models["LightGBM Regressor"] = LGBMRegressor(random_state=42, verbose=-1)
            except Exception:
                pass

            try:
                from catboost import CatBoostRegressor
                candidate_models["CatBoost Regressor"] = CatBoostRegressor(verbose=0, random_seed=42)
            except Exception:
                pass

            n_splits = min(5, len(X_train_raw))

            for name, model_instance in candidate_models.items():
                start_time = time.time()
                try:
                    full_pipeline = Pipeline([
                        ('preprocessor', make_preprocessor()),
                        ('model', model_instance)
                    ])

                    cv_score = None
                    if n_splits >= 2:
                        try:
                            scores = cross_val_score(full_pipeline, X_train_raw, y_train, cv=n_splits, scoring='r2')
                            cv_score = round(float(np.mean(scores)), 4)
                        except Exception as cv_err:
                            logger.warning(f"CV calculation failed for {name}: {cv_err}")

                    full_pipeline.fit(X_train_raw, y_train)
                    preds = full_pipeline.predict(X_test_raw)
                    train_dur = round(time.time() - start_time, 3)

                    r2 = round(float(r2_score(y_test, preds)), 4)
                    mse = round(float(mean_squared_error(y_test, preds)), 4)
                    rmse = round(float(np.sqrt(mse)), 4)
                    mae = round(float(mean_absolute_error(y_test, preds)), 4)

                    item = {
                        "algorithm": name,
                        "status": "SUCCESS",
                        "cv_score": cv_score,
                        "r2_score": r2,
                        "mse": mse,
                        "rmse": rmse,
                        "mae": mae,
                        "training_time_sec": train_dur,
                        "primary_score": cv_score if cv_score is not None else r2
                    }
                    leaderboard.append(item)

                    if item["primary_score"] > best_score:
                        best_score = item["primary_score"]
                        best_model_name = name
                        best_model_pipeline = full_pipeline

                except Exception as err:
                    tb_str = traceback.format_exc()
                    leaderboard.append({
                        "algorithm": name,
                        "status": "FAILED",
                        "reason": str(err),
                        "traceback": tb_str,
                        "primary_score": -999.0
                    })

        successful_models = [m for m in leaderboard if m.get("status") == "SUCCESS"]
        failed_models = [m for m in leaderboard if m.get("status") == "FAILED"]

        if not successful_models or not best_model_pipeline:
            failed_reasons = [{m["algorithm"]: m.get("reason")} for m in failed_models]
            err_msg = f"All candidate models failed during training. Failure reasons: {failed_reasons}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        leaderboard.sort(key=lambda x: x.get("primary_score", -999.0), reverse=True)
        for idx, item in enumerate(leaderboard):
            if item.get("status") == "SUCCESS":
                item["rank"] = idx + 1

        # Real feature importance calculation
        feature_importance_dict = AutoMLEngine.extract_real_feature_importance(
            best_model_pipeline=best_model_pipeline,
            X_train_raw=X_train_raw,
            X_test_raw=X_test_raw,
            y_test=y_test if task_type == 'regression' else label_encoder.transform(y_test_raw.astype(str)),
            usable_features=usable_features,
            num_features=num_features,
            cat_features=cat_features,
            task_type=task_type
        )

        timestamp = int(pd.Timestamp.now().timestamp())
        model_filename = f"model_ds{dataset_id or 0}_{task_type}_{timestamp}.joblib"
        model_filepath = os.path.join(settings.MODEL_DIR, model_filename)

        pipeline_artifact = {
            "pipeline": best_model_pipeline,
            "label_encoder": label_encoder,
            "feature_cols": usable_features,
            "numeric_features": num_features,
            "categorical_features": cat_features,
            "task_type": task_type,
            "target_column": target_column,
            "dataset_id": dataset_id,
            "metrics": leaderboard[0],
            "timestamp": timestamp
        }
        joblib.dump(pipeline_artifact, model_filepath)

        explanation_dict = {
            "dataset_shape": f"{len(df)} rows × {len(df.columns)} columns",
            "target_column": target_column,
            "task_type": task_type,
            "target_selection_source": target_selection_source,
            "used_features": usable_features,
            "excluded_features": excluded_features_info,
            "algorithms_evaluated": len(leaderboard),
            "successful_algorithms": len(successful_models),
            "failed_algorithms": len(failed_models),
            "cv_strategy": f"Dynamic K-Fold CV (n_splits={n_splits})",
            "primary_metric_label": primary_metric_label,
            "top_model": best_model_name,
            "top_score": best_score,
            "warnings": warnings_list,
            "date_derived_features": date_derived_features
        }

        return {
            "best_algorithm": best_model_name,
            "task_type": task_type,
            "target_column": target_column,
            "target_selection_source": target_selection_source,
            "used_features": usable_features,
            "leaderboard": leaderboard,
            "metrics": leaderboard[0],
            "feature_importance": feature_importance_dict,
            "model_file_path": model_filepath,
            "primary_metric_label": primary_metric_label,
            "explanation_dict": explanation_dict,
            "explanation": f"Evaluated {len(leaderboard)} candidate algorithms ({len(successful_models)} successful). '{best_model_name}' selected as Top Model by Cross-Validated Score with {primary_metric_label} of {best_score}."
        }
