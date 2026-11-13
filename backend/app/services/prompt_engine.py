import re
import pandas as pd
from typing import Dict, Any, Optional, List
from app.services.automl_engine import AutoMLEngine

class PromptEngine:
    @staticmethod
    def analyze_prompt_and_dataset(prompt: str, df: pd.DataFrame, target_override: Optional[str] = None) -> Dict[str, Any]:
        """Dataset-agnostic natural language prompt parser for target selection, feature extraction & task inference.
        
        Priority for Target Selection:
        1. Explicit target specified by user in Target Column selector (target_override)
        2. Target explicitly mentioned in natural language prompt (e.g., 'Predict Sales using...')
        3. Schema-based automatic inference (last non-ID, non-constant column)
        """
        columns = list(df.columns)
        col_types = AutoMLEngine.identify_column_types(df)
        usable_cols = [c for c in columns if c not in col_types["id_cols"] and c not in col_types["constant_cols"]]
        
        prompt_lower = prompt.lower().strip()
        target_column = None
        target_selection_source = ""
        reasoning = ""
        needs_target_selection = False

        # --- TIER 1: User Selector Override ---
        if target_override and target_override in columns:
            target_column = target_override
            target_selection_source = "Selected by user"
            reasoning = f"Target column '{target_column}' explicitly selected by user."

        # --- TIER 2: Extract Target from Prompt ---
        if not target_column and prompt_lower:
            # Check for patterns like "Predict [TARGET] using/with/from/based on [FEATURES]"
            # or "Forecast [TARGET]...", "Estimate [TARGET]...", "Classify [TARGET]..."
            verb_pattern = r'\b(predict|forecast|estimate|detect|classify|find|determine)\s+(?:the\s+)?([a-zA-Z0-9_\s]+?)(?=\s+\b(using|with|based\s+on|from|on|for|where|in)\b|$)'
            match = re.search(verb_pattern, prompt_lower)
            if match:
                target_phrase = match.group(2).strip()
                # Find best matching column in usable_cols for the target phrase
                for col in usable_cols:
                    col_lower = str(col).lower().replace('_', ' ')
                    if col_lower == target_phrase or col_lower in target_phrase or target_phrase in col_lower:
                        target_column = col
                        target_selection_source = "Inferred from prompt"
                        reasoning = f"Target column '{target_column}' inferred from prompt intent ('{match.group(0)}')."
                        break

            # Fallback: check exact column matches in the portion before "using"/"with"/"based on"/"from"
            if not target_column:
                split_kw = re.split(r'\b(using|with|based\s+on|from|on)\b', prompt_lower)
                pre_using_text = split_kw[0] if split_kw else prompt_lower
                
                for col in usable_cols:
                    col_lower = str(col).lower().replace('_', ' ')
                    if col_lower in pre_using_text:
                        target_column = col
                        target_selection_source = "Inferred from prompt"
                        reasoning = f"Target column '{target_column}' inferred from prompt keywords before feature clause."
                        break

            # Keyword heuristics fallback
            if not target_column:
                for col in usable_cols:
                    col_lower = str(col).lower()
                    if any(kw in prompt_lower for kw in [col_lower, col_lower.replace('_', ' ')]):
                        target_column = col
                        target_selection_source = "Inferred from prompt"
                        reasoning = f"Target column '{target_column}' matched from prompt text."
                        break

        # --- TIER 3: Automatic Schema Inference ---
        if not target_column:
            if usable_cols:
                target_column = usable_cols[-1]
                target_selection_source = "Automatically inferred from dataset schema"
                reasoning = f"Target column '{target_column}' automatically inferred from dataset schema."
            else:
                needs_target_selection = True
                target_selection_source = "Unspecified"
                reasoning = "Target column could not be inferred. Please select a target column."

        # --- FEATURE EXTRACTION FROM PROMPT ---
        specified_features: Optional[List[str]] = None
        if prompt_lower:
            # Extract features mentioned after "using", "with", "based on", "from"
            feature_split = re.split(r'\b(using|with|based\s+on|from)\b', prompt_lower)
            if len(feature_split) > 2:
                feature_text = feature_split[2]
                matched_features = []
                for col in columns:
                    if col != target_column:
                        col_lower = str(col).lower().replace('_', ' ')
                        if col_lower in feature_text or any(token in feature_text.split() for token in col_lower.split() if len(token) > 2):
                            matched_features.append(col)
                if matched_features:
                    specified_features = matched_features

        # --- TASK TYPE INFERENCE ---
        task_type = "auto"
        if target_column and target_column in df.columns:
            target_series = df[target_column].dropna()
            nunique = target_series.nunique()
            is_num = pd.api.types.is_numeric_dtype(target_series)

            if is_num and nunique > 10:
                task_type = "regression"
                reasoning += f" Target '{target_column}' is continuous numeric ({nunique} unique values) -> Regression."
            else:
                task_type = "classification"
                reasoning += f" Target '{target_column}' is discrete/categorical ({nunique} unique values) -> Classification."

        return {
            "task_type": task_type,
            "target_column": target_column,
            "target_selection_source": target_selection_source,
            "prompt_features": specified_features,
            "candidate_columns": usable_cols,
            "needs_target_selection": needs_target_selection,
            "reasoning": reasoning.strip()
        }
