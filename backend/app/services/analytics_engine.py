import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

class AnalyticsEngine:
    @staticmethod
    def extract_requested_columns(query: str, columns: List[str]) -> Tuple[List[str], List[str], List[str]]:
        """Extracts exact or case-insensitive column matches, missing column requests, and fuzzy suggestions.
        Returns (matched_cols, missing_cols, suggestions).
        """
        query_lower = query.lower()
        matched_cols = []
        missing_cols = []
        suggestions = []

        # 1. Exact & case-insensitive matching
        col_map = {str(c).lower(): c for c in columns}
        col_normalized_map = {str(c).lower().replace('_', ' '): c for c in columns}

        # Check for explicit token references in query
        words = re.findall(r'\b[a-zA-Z0-9_]+\b', query_lower)
        
        # Check full string matches for column names in query
        for c_lower, original_col in col_map.items():
            if c_lower in query_lower or c_lower.replace('_', ' ') in query_lower:
                if original_col not in matched_cols:
                    matched_cols.append(original_col)

        # Check if query asks for a specific column name that does not exist in dataset
        # E.g. "average Sales" -> extracts candidate "sales"
        keywords_to_ignore = {
            'what', 'is', 'the', 'average', 'mean', 'median', 'min', 'minimum', 'max', 'maximum',
            'sum', 'total', 'count', 'std', 'standard', 'deviation', 'show', 'plot', 'chart', 'graph',
            'give', 'me', 'calculate', 'of', 'by', 'in', 'for', 'a', 'an', 'are', 'my', 'dataset',
            'columns', 'rows', 'how', 'many', 'highest', 'lowest', 'top', 'bottom', 'which', 'who'
        }

        potential_col_tokens = [w for w in words if w not in keywords_to_ignore and len(w) > 2]
        
        for token in potential_col_tokens:
            if token not in col_map and token not in [c.lower() for c in matched_cols]:
                # Check if token is a substring of an available column (suggestion)
                possible_suggs = [c for c in columns if token in str(c).lower()]
                if possible_suggs:
                    for s in possible_suggs:
                        sugg_str = f"Did you mean '{s}'?"
                        if sugg_str not in suggestions:
                            suggestions.append(sugg_str)
                else:
                    if token.capitalize() not in missing_cols and token.upper() not in missing_cols:
                        missing_cols.append(token.capitalize())

        return matched_cols, missing_cols, suggestions

    @staticmethod
    def process_nl_query(query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Dataset-agnostic schema-first natural language query processor executing actual Pandas operations."""
        query_lower = query.lower().strip()
        columns = list(df.columns)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

        # 1. Handle Schema Questions
        if any(kw in query_lower for kw in ["what columns", "list columns", "show columns", "available columns", "what are the columns"]):
            return {
                "status": "SUCCESS",
                "intent": "SCHEMA",
                "summary": f"The active dataset contains {len(columns)} columns: {', '.join(columns)}.",
                "data": [{"column": str(c), "type": str(df[c].dtype)} for c in columns]
            }

        if any(kw in query_lower for kw in ["how many rows", "row count", "number of rows", "dataset size"]):
            return {
                "status": "SUCCESS",
                "intent": "SCHEMA",
                "summary": f"The active dataset contains {len(df)} rows and {len(columns)} columns.",
                "data": [{"row_count": len(df), "col_count": len(columns)}]
            }

        # 2. Extract Matched & Missing Columns
        matched_cols, missing_cols, suggestions = AnalyticsEngine.extract_requested_columns(query, columns)

        # CRITICAL RULE: If user requested a column that does NOT exist in active dataset, return clear error!
        if missing_cols and not matched_cols:
            missing_col_name = missing_cols[0]
            sugg_text = f" {suggestions[0]}" if suggestions else ""
            return {
                "status": "ERROR",
                "intent": "MISSING_COLUMN",
                "error_message": f"The active dataset does not contain a '{missing_col_name}' column.{sugg_text}",
                "missing_column": missing_col_name,
                "available_columns": columns,
                "suggestions": suggestions,
                "summary": f"The active dataset does not contain a '{missing_col_name}' column.{sugg_text} Available columns: {', '.join(columns)}"
            }

        # 3. Detect Operation
        op = None
        if any(w in query_lower for w in ["average", "mean"]):
            op = "mean"
        elif any(w in query_lower for w in ["median"]):
            op = "median"
        elif any(w in query_lower for w in ["max", "maximum", "highest"]):
            op = "max"
        elif any(w in query_lower for w in ["min", "minimum", "lowest"]):
            op = "min"
        elif any(w in query_lower for w in ["sum", "total"]):
            op = "sum"
        elif any(w in query_lower for w in ["count"]):
            op = "count"
        elif any(w in query_lower for w in ["std", "standard deviation"]):
            op = "std"

        # 4. Handle Top/Bottom Entity Queries (e.g. "Which product has the highest Sales?")
        if op in ["max", "min"] and len(matched_cols) >= 2:
            num_cols = [c for c in matched_cols if pd.api.types.is_numeric_dtype(df[c])]
            cat_cols = [c for c in matched_cols if not pd.api.types.is_numeric_dtype(df[c])]
            
            if num_cols and cat_cols:
                num_col = num_cols[0]
                cat_col = cat_cols[0]
                
                try:
                    grp = df.groupby(cat_col)[num_col].mean()
                    top_cat = grp.idxmax() if op == "max" else grp.idxmin()
                    top_val = float(grp.max() if op == "max" else grp.min())
                    val_fmt = round(top_val, 4)
                    
                    op_label = "highest" if op == "max" else "lowest"
                    return {
                        "status": "SUCCESS",
                        "intent": "TOP_ENTITY",
                        "operation": op.upper(),
                        "column": num_col,
                        "entity_column": cat_col,
                        "top_entity": str(top_cat),
                        "value": val_fmt,
                        "chart_type": "metric",
                        "summary": f"'{top_cat}' has the {op_label} average {num_col} ({val_fmt}) in the active dataset.",
                        "data": [{"metric": f"{op_label.capitalize()} {num_col} ({cat_col})", "value": f"{top_cat}: {val_fmt}"}]
                    }
                except Exception:
                    pass

        # 5. Handle Statistics / Aggregation Queries (e.g., "What is the average Sales?")
        if op and matched_cols:
            # Pick first numeric column if available, else first matched column
            num_candidates = [c for c in matched_cols if pd.api.types.is_numeric_dtype(df[c])]
            target_col = num_candidates[0] if num_candidates else matched_cols[0]
            
            # Numeric validation for math ops
            if op in ["mean", "median", "max", "min", "sum", "std"] and not pd.api.types.is_numeric_dtype(df[target_col]):
                return {
                    "status": "ERROR",
                    "intent": "TYPE_MISMATCH",
                    "error_message": f"Column '{target_col}' is not a numeric column, so {op} cannot be calculated.",
                    "summary": f"Column '{target_col}' is categorical/non-numeric. Cannot compute {op}."
                }

            # Calculate actual value on Pandas DataFrame
            series_clean = df[target_col].dropna()
            if series_clean.empty:
                return {
                    "status": "ERROR",
                    "intent": "EMPTY_COLUMN",
                    "error_message": f"Column '{target_col}' contains no valid data.",
                    "summary": f"Column '{target_col}' is empty."
                }

            if op == "mean":
                val = float(series_clean.mean())
            elif op == "median":
                val = float(series_clean.median())
            elif op == "max":
                val = float(series_clean.max()) if pd.api.types.is_numeric_dtype(df[target_col]) else str(series_clean.max())
            elif op == "min":
                val = float(series_clean.min()) if pd.api.types.is_numeric_dtype(df[target_col]) else str(series_clean.min())
            elif op == "sum":
                val = float(series_clean.sum())
            elif op == "count":
                val = int(series_clean.count())
            elif op == "std":
                val = float(series_clean.std())

            val_formatted = round(val, 4) if isinstance(val, float) else val

            return {
                "status": "SUCCESS",
                "intent": "STATISTICS",
                "operation": op.upper(),
                "column": target_col,
                "value": val_formatted,
                "chart_type": "metric",
                "summary": f"The {op} of '{target_col}' in the active dataset is {val_formatted}.",
                "data": [{"metric": f"{op.capitalize()} of {target_col}", "value": val_formatted}]
            }

        # 5. Handle GroupBy & Visualization Queries (e.g. "Sales by Region")
        if len(matched_cols) >= 2:
            col1, col2 = matched_cols[0], matched_cols[1]
            if pd.api.types.is_numeric_dtype(df[col2]):
                x_col, y_col = col1, col2
            elif pd.api.types.is_numeric_dtype(df[col1]):
                x_col, y_col = col2, col1
            else:
                x_col, y_col = col1, col2

            chart_type = "bar"
            if "pie" in query_lower or "share" in query_lower:
                chart_type = "pie"
            elif "line" in query_lower or "trend" in query_lower:
                chart_type = "line"
            elif "scatter" in query_lower:
                chart_type = "scatter"

            try:
                if pd.api.types.is_numeric_dtype(df[y_col]):
                    agg_df = df.groupby(x_col)[y_col].mean().reset_index().head(15)
                else:
                    agg_df = df.groupby(x_col)[y_col].count().reset_index().head(15)
                plot_data = agg_df.to_dict(orient="records")
            except Exception:
                plot_data = df[[x_col, y_col]].dropna().head(15).to_dict(orient="records")

            return {
                "status": "SUCCESS",
                "intent": "GROUPBY",
                "chart_type": chart_type,
                "title": f"{y_col} by {x_col}",
                "x_col": x_col,
                "y_col": y_col,
                "data": plot_data,
                "summary": f"Visualizing {y_col} across {x_col} for active dataset ({len(df)} rows)."
            }

        # Single column visualization fallback if matched
        if len(matched_cols) == 1:
            target_col = matched_cols[0]
            if pd.api.types.is_numeric_dtype(df[target_col]):
                counts, bins = np.histogram(df[target_col].dropna(), bins=10)
                plot_data = [{"range": f"{round(bins[i],1)}-{round(bins[i+1],1)}", "count": int(counts[i])} for i in range(len(counts))]
                return {
                    "status": "SUCCESS",
                    "intent": "HISTOGRAM",
                    "chart_type": "histogram",
                    "title": f"Distribution of {target_col}",
                    "x_col": target_col,
                    "data": plot_data,
                    "summary": f"Distribution histogram of '{target_col}' ({len(df)} rows)."
                }

        # Default Schema Summary if query cannot be matched
        return {
            "status": "SUCCESS",
            "intent": "SUMMARY",
            "summary": f"Analyzed query '{query}' on active dataset ({len(df)} rows, {len(columns)} columns). Available columns: {', '.join(columns)}.",
            "data": [{"column": c, "type": str(df[c].dtype)} for c in columns]
        }

    @staticmethod
    def get_correlation_matrix(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates pairwise correlation for all numeric columns."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {"columns": [], "matrix": []}
        
        cols = list(numeric_df.columns)
        corr_matrix = numeric_df.corr().fillna(0).round(3).values.tolist()
        return {"columns": cols, "matrix": corr_matrix}
