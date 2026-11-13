import os
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.report import Report
from app.models.ml_model import MLModel
from app.services.report_service import ReportService
from app.services.dataset_loader import DatasetLoader
from app.services.data_cleaner import DataCleaner, safe_float

reports_router = APIRouter(prefix="/reports", tags=["Report Generator"])


def _build_report_data(ds, df, dataset_id: int, db: Session) -> dict:
    """Build a comprehensive data dictionary from the active dataset."""
    import numpy as np

    inspection = DataCleaner.inspect_dataset(df)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    # ── column details ────────────────────────────────────────────────
    column_details = []
    for col_info in inspection.get("columns", []):
        column_details.append({
            "name": col_info["name"],
            "dtype": col_info["type"],
            "non_null": int(df[col_info["name"]].notna().sum()),
            "null_count": col_info["missing"],
            "unique": col_info["unique"],
        })

    # ── numeric descriptive stats via df.describe() ───────────────────
    numeric_stats = {}
    if numeric_cols:
        desc = df[numeric_cols].describe()
        for col in desc.columns:
            numeric_stats[str(col)] = {
                str(k): safe_float(v) for k, v in desc[col].items()
            }

    # ── categorical summaries (top-10 value counts) ───────────────────
    categorical_summaries = {}
    for col in categorical_cols:
        vc = df[col].dropna().value_counts().head(10)
        if not vc.empty:
            categorical_summaries[str(col)] = {str(k): int(v) for k, v in vc.items()}

    # ── missing value summary ─────────────────────────────────────────
    missing_summary = inspection.get("missing_per_column", {})
    total_missing = inspection.get("null_count", 0)
    duplicate_count = inspection.get("duplicate_count", 0)

    # ── cleaning summary ──────────────────────────────────────────────
    cleaning_summary = None
    if ds.cleaned_file_path:
        cleaning_summary = f"Dataset has been cleaned (version {ds.version}). Cleaned file stored."

    # ── trained models ────────────────────────────────────────────────
    models = db.query(MLModel).filter(MLModel.dataset_id == dataset_id).all()
    trained_models = []
    for m in models:
        trained_models.append({
            "id": m.id,
            "name": m.name,
            "best_algorithm": m.best_algorithm,
            "target_column": m.target_column,
            "task_type": m.task_type,
            "metrics_json": m.metrics_json,
        })

    # ── AI insights ───────────────────────────────────────────────────
    ai_insights = None
    try:
        from app.services.ai_service import AIService
        ai_insights = AIService.get_executive_insights(dataset_id, db)
    except Exception:
        pass

    # ── sample rows ───────────────────────────────────────────────────
    sample_rows = df.head(5).fillna("").to_dict(orient="records")

    return {
        "dataset_info": {
            "name": ds.name,
            "id": ds.id,
            "row_count": len(df),
            "col_count": len(df.columns),
            "quality_score": ds.quality_score,
            "columns": list(df.columns),
            "cleaning_summary": cleaning_summary,
        },
        "column_details": column_details,
        "numeric_stats": numeric_stats,
        "categorical_summaries": categorical_summaries,
        "missing_summary": missing_summary,
        "total_missing": total_missing,
        "duplicate_count": duplicate_count,
        "trained_models": trained_models,
        "ai_insights": ai_insights,
        "sample_rows": sample_rows,
        "data": df.head(100).fillna("").to_dict(orient="records"),
    }


@reports_router.post("/generate")
def generate_report(
    title: str = "PragyaDrishti Data Analytics Report",
    report_type: str = "PDF",
    summary: str = "Automated AI Analysis",
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    # ── load dataset context ──────────────────────────────────────────
    data_dict: dict = {"data": []}
    if dataset_id:
        try:
            ds, df, file_path = DatasetLoader.load_dataset(db, dataset_id, version="latest")
            data_dict = _build_report_data(ds, df, dataset_id, db)
        except HTTPException:
            raise  # propagate 404 / 400 from loader
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load dataset #{dataset_id} for report: {exc}",
            )

    # ── generate report file ──────────────────────────────────────────
    try:
        os.makedirs(settings.REPORT_DIR, exist_ok=True)
        filepath = ReportService.generate_report(title, report_type, summary, data_dict)
    except ValueError as val_err:
        raise HTTPException(
            status_code=500,
            detail=f"PDF validation failed: {val_err}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {exc}",
        )

    # ── persist record ────────────────────────────────────────────────
    report = Report(
        title=title,
        report_type=report_type.upper(),
        file_path=filepath,
        summary_text=summary,
        owner_id=None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@reports_router.get("/list")
def list_reports(db: Session = Depends(get_db)):
    return db.query(Report).order_by(Report.created_at.desc()).all()


@reports_router.get("/download/{report_id}")
def download_report(report_id: int, db: Session = Depends(get_db)):
    rep = db.query(Report).filter(Report.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report record not found.")
    if not os.path.exists(rep.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk.")

    file_size = os.path.getsize(rep.file_path)
    if file_size == 0:
        raise HTTPException(status_code=500, detail="Report file on disk is empty (0 bytes).")

    basename = os.path.basename(rep.file_path)
    ext = os.path.splitext(basename)[1].lower()
    media_map = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".html": "text/html",
    }
    media_type = media_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=rep.file_path,
        filename=basename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{basename}"'},
    )
