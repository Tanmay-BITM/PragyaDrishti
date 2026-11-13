import os
import json
import pandas as pd
import numpy as np
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.dataset import Dataset
from app.models.ml_model import MLModel
from app.services.data_cleaner import DataCleaner, safe_float
from app.services.dataset_loader import DatasetLoader

class AIService:
    @staticmethod
    def get_dataset_context(dataset_id: int, db: Session) -> Dict[str, Any]:
        """Fetches and builds detailed factual dataset context from DB & DataFrame file."""
        try:
            ds, df, file_to_read = DatasetLoader.load_dataset(db, dataset_id, version="latest")
        except Exception:
            return {}

        inspection = DataCleaner.inspect_dataset(df)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

        column_stats = {}
        for col_info in inspection.get("columns", []):
            if col_info.get("stats"):
                column_stats[col_info["name"]] = col_info["stats"]

        # Compute correlations for numeric columns if available
        strongest_corr = {}
        if len(numeric_cols) >= 2:
            try:
                corr = df[numeric_cols].corr().abs()
                np.fill_diagonal(corr.values, 0)
                max_pair = corr.unstack().idxmax()
                max_val = corr.loc[max_pair[0], max_pair[1]]
                strongest_corr = {
                    "feature_1": str(max_pair[0]),
                    "feature_2": str(max_pair[1]),
                    "correlation": safe_float(max_val)
                }
            except Exception:
                pass

        # Check for trained models on this dataset
        models = db.query(MLModel).filter(MLModel.dataset_id == dataset_id).all()
        model_info = [
            {
                "id": m.id,
                "name": m.name,
                "algorithm": m.best_algorithm,
                "target": m.target_column,
                "task": m.task_type
            }
            for m in models
        ]

        return {
            "dataset_id": ds.id,
            "dataset_name": ds.name,
            "filename": ds.filename,
            "row_count": len(df),
            "col_count": len(df.columns),
            "quality_score": ds.quality_score,
            "is_cleaned": ds.cleaned_file_path is not None,
            "column_names": list(df.columns),
            "data_types": {str(col): str(df[col].dtype) for col in df.columns},
            "missing_summary": inspection.get("null_count", 0),
            "duplicate_count": inspection.get("duplicate_count", 0),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "column_stats": column_stats,
            "sample_rows": df.head(3).fillna("").to_dict(orient="records"),
            "strongest_correlation": strongest_corr,
            "trained_models": model_info
        }

    @staticmethod
    def get_executive_insights(dataset_id: int, db: Session) -> Dict[str, Any]:
        """Generates 100% dynamic, factual AI Executive Insights for active dataset."""
        context = AIService.get_dataset_context(dataset_id, db)
        if not context:
            return {
                "dataset_name": "None",
                "executive_summary": "Please upload or select a dataset to view AI Executive Insights.",
                "key_trends": ["No dataset selected."],
                "quality_score": 0
            }

        ds_name = context["dataset_name"]
        row_cnt = context["row_count"]
        col_cnt = context["col_count"]
        cols = context["column_names"]
        numeric_cols = context["numeric_columns"]
        corr = context.get("strongest_correlation", {})
        models = context.get("trained_models", [])

        # Build factual summary
        summary_parts = [f"Analysis of '{ds_name}' dataset ({row_cnt} rows × {col_cnt} columns) indicates a data quality score of {context['quality_score']}%."]
        if corr:
            summary_parts.append(f"Strongest numerical relationship observed between '{corr['feature_1']}' and '{corr['feature_2']}' (correlation: {corr['correlation']}).")
        if models:
            summary_parts.append(f"Active trained model available: {models[0]['algorithm']} predicting '{models[0]['target']}' ({models[0]['task']}).")

        executive_summary = " ".join(summary_parts)

        # Build dynamic key trends
        key_trends = []
        if context["missing_summary"] > 0:
            key_trends.append(f"Found {context['missing_summary']} missing values across columns ({round((context['missing_summary']/(row_cnt*col_cnt))*100, 1)}% null rate).")
        else:
            key_trends.append("Zero missing values detected across dataset features.")

        if context["duplicate_count"] > 0:
            key_trends.append(f"Identified {context['duplicate_count']} exact duplicate rows eligible for auto-cleaning.")
        else:
            key_trends.append("Zero duplicate rows detected.")

        if numeric_cols:
            col_stats = context.get("column_stats", {})
            first_num = numeric_cols[0]
            if first_num in col_stats:
                stats = col_stats[first_num]
                key_trends.append(f"Feature '{first_num}' averages {stats.get('mean', 0)} (range: {stats.get('min', 0)} to {stats.get('max', 0)}).")

        if models:
            key_trends.append(f"Machine learning model '{models[0]['name']}' ({models[0]['algorithm']}) ready for inference.")
        else:
            key_trends.append("No ML model trained yet. Execute Prompt-to-ML or AutoML to generate predictive pipeline.")

        return {
            "dataset_id": dataset_id,
            "dataset_name": ds_name,
            "executive_summary": executive_summary,
            "key_trends": key_trends,
            "quality_score": context["quality_score"],
            "trained_models_count": len(models)
        }

    @staticmethod
    def ask_data_scientist(prompt: str, dataset_id: Optional[int], db: Session) -> Dict[str, Any]:
        """Dataset-aware AI Data Scientist Agent responding using factual dataset context."""
        prompt_lower = prompt.lower().strip()

        # Check if question asks about trained models across ALL datasets
        if any(phrase in prompt_lower for phrase in ["which dataset has been trained", "which datasets have been trained", "what models have been trained", "trained datasets", "trained models"]):
            all_models = db.query(MLModel).all()
            if not all_models:
                return {
                    "answer": "No machine learning models have been trained yet on any dataset. Upload a dataset and run Prompt-to-ML or AutoML to train a model.",
                    "dataset_name": "None",
                    "suggested_actions": ["Upload Dataset", "Train Prompt-to-ML"],
                    "suggested_chart": "bar"
                }

            model_summaries = []
            for m in all_models:
                ds = db.query(Dataset).filter(Dataset.id == m.dataset_id).first()
                ds_name = ds.name if ds else f"Dataset #{m.dataset_id}"
                metrics = json.loads(m.metrics_json) if m.metrics_json else {}
                score_str = f"Score: {metrics.get('primary_score', 'N/A')}"
                model_summaries.append(f"• Dataset '{ds_name}': Target = '{m.target_column}', Task = '{m.task_type}', Best Algorithm = '{m.best_algorithm}' ({score_str})")

            answer_text = "Overall Summary of Trained Datasets & Models:\n" + "\n".join(model_summaries)
            return {
                "answer": answer_text,
                "dataset_name": "Platform Overview",
                "suggested_actions": ["Predict Model", "View Leaderboard"],
                "suggested_chart": "bar"
            }

        # For dataset-specific questions, dataset_id MUST be valid
        if not dataset_id:
            return {
                "answer": "Please upload or select a dataset first.",
                "error": "No dataset selected",
                "suggested_actions": ["Upload Dataset"],
                "suggested_chart": "bar"
            }

        context = AIService.get_dataset_context(dataset_id, db)
        if not context:
            return {
                "answer": "The selected dataset could not be found. Please upload or select a valid dataset.",
                "error": "Dataset not found",
                "suggested_actions": ["Upload Dataset"],
                "suggested_chart": "bar"
            }

        # 1. LLM Generation if Gemini API Key is configured
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                system_instruction = f"""
                You are PragyaDrishti AI Data Scientist Agent.
                Answer strictly using the supplied dataset and model context below. Do NOT invent columns, values, datasets, models, metrics, or correlations.

                ACTUAL DATASET CONTEXT:
                - Dataset Name: {context['dataset_name']}
                - Dataset ID: {context['dataset_id']}
                - Exact Row Count: {context['row_count']}
                - Exact Column Count: {context['col_count']}
                - Columns List: {context['column_names']}
                - Column Data Types: {context['data_types']}
                - Column Numeric Stats (mean, min, max, median): {context.get('column_stats')}
                - Missing Values Count: {context['missing_summary']}
                - Duplicate Rows Count: {context['duplicate_count']}
                - Numeric Columns: {context['numeric_columns']}
                - Categorical Columns: {context['categorical_columns']}
                - Quality Score: {context['quality_score']}%
                - Strongest Correlation: {context['strongest_correlation']}
                - Trained Models: {context['trained_models']}
                - Representative Sample Rows: {context['sample_rows']}

                User Question: "{prompt}"

                Answer factually and concisely based strictly on the actual dataset metrics.
                """
                response = model.generate_content(system_instruction)
                if response and response.text:
                    return {
                        "answer": response.text,
                        "dataset_name": context["dataset_name"],
                        "suggested_actions": ["Run Auto-Clean", "Train AutoML Model", "Generate PDF Report"],
                        "suggested_chart": "bar"
                    }
            except Exception as gemini_err:
                pass

        # 2. Deterministic Factual Data Scientist Response Engine (100% Dataset Aware)
        answer = ""
        suggested_actions = ["Run Auto-Clean", "Train AutoML Model", "Generate Report"]
        suggested_chart = "bar"

        # Check for specific column average queries
        matched_col = None
        for c in context['column_names']:
            if c.lower() in prompt_lower:
                matched_col = c
                break

        if ("average" in prompt_lower or "mean" in prompt_lower) and matched_col:
            stats = context.get('column_stats', {}).get(matched_col, {})
            if "mean" in stats:
                answer = f"The average value of '{matched_col}' in dataset '{context['dataset_name']}' is {round(stats['mean'], 4)} (min: {round(stats['min'], 2)}, max: {round(stats['max'], 2)})."
            else:
                answer = f"Column '{matched_col}' is categorical. Sample values: {', '.join(str(x) for x in context['sample_rows'][:2])}."
        elif "how many rows" in prompt_lower or "row count" in prompt_lower or "size" in prompt_lower:
            answer = f"Your selected dataset '{context['dataset_name']}' contains exactly {context['row_count']} rows and {context['col_count']} columns."
        elif "column" in prompt_lower or "feature" in prompt_lower and not "relationship" in prompt_lower:
            answer = f"Your dataset '{context['dataset_name']}' has {context['col_count']} columns: {', '.join(context['column_names'])}."
        elif "relationship" in prompt_lower or "correlation" in prompt_lower or "strongest" in prompt_lower or "related" in prompt_lower:
            corr = context.get("strongest_correlation", {})
            if corr:
                answer = f"In dataset '{context['dataset_name']}', the strongest numerical relationship is between '{corr.get('feature_1')}' and '{corr.get('feature_2')}' with a correlation coefficient of {corr.get('correlation')}."
            else:
                answer = f"Dataset '{context['dataset_name']}' contains numeric columns: {', '.join(context['numeric_columns'])}."
        elif "missing" in prompt_lower or "null" in prompt_lower or "clean" in prompt_lower:
            answer = f"Dataset '{context['dataset_name']}' has a quality score of {context['quality_score']}%. Missing values count: {context['missing_summary']}, Duplicate rows count: {context['duplicate_count']}."
            suggested_actions = ["Execute Auto-Clean"]
        elif "model" in prompt_lower or "predict" in prompt_lower or "trained" in prompt_lower or "accuracy" in prompt_lower:
            models = context.get("trained_models", [])
            if models:
                m_str = ", ".join([f"{m['name']} ({m['algorithm']})" for m in models])
                answer = f"Trained models for '{context['dataset_name']}': {m_str}. Target: '{models[0]['target']}' ({models[0]['task']}). You can trigger real-time predictions via `/api/v1/prompt-ml/predict`."
            else:
                answer = f"No ML model has been trained yet on the currently selected dataset '{context['dataset_name']}'."
                suggested_actions = ["Train AutoML Model"]
        else:
            answer = f"Analyzed '{prompt}' for dataset '{context['dataset_name']}' ({context['row_count']} rows, {context['col_count']} columns). Columns: {', '.join(context['column_names'][:5])}..."

        return {
            "answer": answer,
            "dataset_name": context["dataset_name"],
            "suggested_actions": suggested_actions,
            "suggested_chart": suggested_chart
        }
