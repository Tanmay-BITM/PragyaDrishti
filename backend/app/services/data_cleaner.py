import pandas as pd
import numpy as np
import json
from typing import Dict, Any, Tuple

def safe_float(val: Any, default: float = 0.0) -> float:
    """Converts numpy/pandas numeric values into strict JSON-compliant floats."""
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        return round(f, 4)
    except Exception:
        return default

class DataCleaner:
    @staticmethod
    def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyzes a pandas DataFrame and returns statistical schema metrics."""
        total_cells = df.shape[0] * df.shape[1]
        null_count = int(df.isnull().sum().sum())
        duplicate_count = int(df.duplicated().sum())
        
        # Calculate quality score (0 to 100)
        null_pct = (null_count / max(total_cells, 1)) * 100
        dup_pct = (duplicate_count / max(df.shape[0], 1)) * 100
        quality_score = round(max(0.0, 100.0 - (null_pct * 0.5 + dup_pct * 0.5)), 1)
        
        columns_info = []
        missing_per_col = {}
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            missing = int(df[col].isnull().sum())
            missing_per_col[str(col)] = missing
            unique_vals = int(df[col].nunique())
            sample_vals = df[col].dropna().head(3).tolist()
            
            stats = {}
            if pd.api.types.is_numeric_dtype(df[col]):
                series_clean = df[col].dropna()
                stats = {
                    "mean": safe_float(series_clean.mean()) if not series_clean.empty else 0.0,
                    "std": safe_float(series_clean.std()) if not series_clean.empty else 0.0,
                    "min": safe_float(series_clean.min()) if not series_clean.empty else 0.0,
                    "max": safe_float(series_clean.max()) if not series_clean.empty else 0.0,
                    "median": safe_float(series_clean.median()) if not series_clean.empty else 0.0
                }
            
            columns_info.append({
                "name": str(col),
                "type": dtype_str,
                "missing": missing,
                "missing_pct": round((missing / max(df.shape[0], 1)) * 100, 1),
                "unique": unique_vals,
                "sample": [str(x) for x in sample_vals],
                "stats": stats
            })
            
        return {
            "row_count": df.shape[0],
            "col_count": df.shape[1],
            "null_count": null_count,
            "duplicate_count": duplicate_count,
            "quality_score": quality_score,
            "missing_per_column": missing_per_col,
            "columns": columns_info
        }

    @staticmethod
    def auto_clean(
        df: pd.DataFrame,
        fill_missing: bool = True,
        remove_duplicates: bool = True,
        handle_outliers: bool = True,
        outlier_strategy: str = "clip" # "clip" or "remove"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Executes full automated data cleaning pipeline creating a new cleaned dataset version."""
        
        # Ingestion cleanup: Replace infinite values with NaN
        cleaned = df.replace([np.inf, -np.inf], np.nan).copy()
        
        rows_before = len(df)
        cols_before = len(df.columns)
        nulls_before = int(cleaned.isnull().sum().sum())
        dups_before = int(cleaned.duplicated().sum())

        operations = []
        cols_affected = set()

        # 1. Remove duplicate rows
        dups_removed = 0
        if remove_duplicates and dups_before > 0:
            dups_removed = dups_before
            cleaned = cleaned.drop_duplicates().reset_index(drop=True)
            operations.append(f"Removed {dups_removed} exact duplicate rows.")

        # 2. Fill missing values (Median for numeric, Mode for categorical)
        filled_summary = {}
        if fill_missing:
            for col in cleaned.columns:
                null_c = int(cleaned[col].isnull().sum())
                if null_c > 0:
                    cols_affected.add(str(col))
                    if pd.api.types.is_numeric_dtype(cleaned[col]):
                        med_val = cleaned[col].median()
                        if pd.isna(med_val):
                            med_val = 0.0
                        cleaned[col] = cleaned[col].fillna(med_val)
                        msg = f"Imputed {null_c} missing values using median ({safe_float(med_val)})"
                    else:
                        mode_s = cleaned[col].mode()
                        mode_val = mode_s[0] if not mode_s.empty else "Unknown"
                        cleaned[col] = cleaned[col].fillna(mode_val)
                        msg = f"Imputed {null_c} missing values using mode ('{mode_val}')"

                    filled_summary[str(col)] = msg
                    operations.append(f"Column '{col}': {msg}")

        # 3. Handle Outliers via IQR
        outliers_summary = {}
        if handle_outliers:
            for col in cleaned.select_dtypes(include=[np.number]).columns:
                q1 = cleaned[col].quantile(0.25)
                q3 = cleaned[col].quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outlier_mask = (cleaned[col] < lower_bound) | (cleaned[col] > upper_bound)
                    outliers_count = int(outlier_mask.sum())
                    if outliers_count > 0:
                        cols_affected.add(str(col))
                        if outlier_strategy == "remove":
                            cleaned = cleaned[~outlier_mask].reset_index(drop=True)
                            msg = f"Removed {outliers_count} outlier rows beyond range [{safe_float(lower_bound)}, {safe_float(upper_bound)}]"
                        else:
                            cleaned[col] = np.clip(cleaned[col], lower_bound, upper_bound)
                            msg = f"Clipped {outliers_count} outliers to range [{safe_float(lower_bound)}, {safe_float(upper_bound)}]"

                        outliers_summary[str(col)] = msg
                        operations.append(f"Column '{col}': {msg}")

        rows_after = len(cleaned)
        nulls_after = int(cleaned.isnull().sum().sum())
        dups_after = int(cleaned.duplicated().sum())

        new_inspection = DataCleaner.inspect_dataset(cleaned)

        if not operations:
            operations.append("Dataset passed inspection with 0 missing values and 0 duplicates.")

        report = {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "cols_count": cols_before,
            "missing_before": nulls_before,
            "missing_after": nulls_after,
            "duplicates_before": dups_before,
            "duplicates_after": dups_after,
            "duplicates_removed": dups_removed,
            "columns_affected": list(cols_affected),
            "operations": operations,
            "operations_performed": operations,
            "original_quality_score": DataCleaner.inspect_dataset(df)["quality_score"],
            "new_quality_score": new_inspection["quality_score"]
        }

        return cleaned, report
