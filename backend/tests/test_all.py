import pytest
import os
import json
import tempfile
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.services.data_cleaner import DataCleaner
from app.services.prompt_engine import PromptEngine
from app.services.automl_engine import AutoMLEngine
from app.services.dataset_loader import DatasetLoader
from app.services.analytics_engine import AnalyticsEngine
from app.services.ai_service import AIService
from app.services.report_service import ReportService
from app.main import app
from app.models.dataset import Dataset
from app.models.ml_model import MLModel
from app.api.v1.datasets import deduplicate_dataset_records

def test_password_hashing():
    pw = "SuperSecurePassword2026"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPw", hashed) is False

def test_jwt_token_generation():
    token = create_access_token(subject=42)
    payload = decode_access_token(token)
    assert payload is not None
    assert str(payload["sub"]) == "42"

# 1. Student dataset: target = CGPA (Regression)
def test_scenario_1_student_cgpa_regression():
    df = pd.DataFrame({
        "student_id": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        "attendance": [90, 85, 92, 70, 60, 95, 88, 75, 82, 91],
        "study_hours": [5.5, 4.0, 6.0, 2.5, 1.5, 7.0, 5.0, 3.0, 4.5, 6.5],
        "CGPA": [8.8, 7.9, 9.2, 6.5, 5.8, 9.6, 8.4, 6.9, 8.0, 9.1]
    })
    res = AutoMLEngine.train_and_evaluate(df, target_column="CGPA", task_type="regression")
    assert res["task_type"] == "regression"
    assert res["target_column"] == "CGPA"
    assert "student_id" not in res["used_features"] # ID column automatically excluded
    assert len(res["leaderboard"]) > 0
    assert res["leaderboard"][0]["status"] == "SUCCESS"

# 2. Student dataset: target = Placement (Classification)
def test_scenario_2_student_placement_classification():
    df = pd.DataFrame({
        "student_code": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"],
        "cgpa": [9.0, 6.0, 8.5, 5.5, 9.2, 7.0, 8.8, 6.2, 7.5, 9.5],
        "internships": [2, 0, 1, 0, 3, 1, 2, 0, 1, 2],
        "Placement": ["Placed", "Not Placed", "Placed", "Not Placed", "Placed", "Not Placed", "Placed", "Not Placed", "Placed", "Placed"]
    })
    res = AutoMLEngine.train_and_evaluate(df, target_column="Placement", task_type="classification")
    assert res["task_type"] == "classification"
    assert res["target_column"] == "Placement"
    assert "student_code" not in res["used_features"]
    assert len(res["leaderboard"]) > 0
    assert res["leaderboard"][0]["status"] == "SUCCESS"

# 3. Sales dataset: target = Sales (Regression)
def test_scenario_3_sales_regression():
    df = pd.DataFrame({
        "Store_ID": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "Advertising_Spend": [1000, 2500, 1500, 3000, 4500, 2000, 3500, 5000, 1200, 2800],
        "Region": ["North", "South", "North", "East", "West", "East", "West", "North", "South", "East"],
        "Sales": [15000, 28000, 21000, 35000, 48000, 24000, 39000, 52000, 18000, 31000]
    })
    res = AutoMLEngine.train_and_evaluate(df, target_column="Sales")
    assert res["task_type"] == "regression"
    assert res["target_column"] == "Sales"
    assert "Store_ID" not in res["used_features"]
    assert res["leaderboard"][0]["status"] == "SUCCESS"

# 4. Dataset Loader Verification for CSV & XLSX
def test_dataset_loader_csv_and_xlsx():
    df_sample = pd.DataFrame({
        "Order_ID": [1, 2, 3],
        "Date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "Region": ["North", "South", "East"],
        "Product": ["Laptops", "Phones", "Tablets"],
        "Quantity": [10, 20, 15],
        "Unit_Price": [100, 200, 150],
        "Discount": [0.0, 0.1, 0.05],
        "Sales": [1000, 4000, 2250],
        "Profit": [200, 800, 450]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test_sales.csv")
        xlsx_path = os.path.join(tmpdir, "test_sales.xlsx")
        
        df_sample.to_csv(csv_path, index=False)
        df_sample.to_excel(xlsx_path, engine="openpyxl", index=False)
        
        csv_df = DatasetLoader.read_dataset_file(csv_path)
        xlsx_df = DatasetLoader.read_dataset_file(xlsx_path)
        
        assert csv_df.shape == (3, 9)
        assert xlsx_df.shape == (3, 9)
        assert list(csv_df.columns) == list(df_sample.columns)
        assert list(xlsx_df.columns) == list(df_sample.columns)

# 5. M7 NL Analytics Verification
def test_m7_nl_analytics():
    df_sales = pd.DataFrame({
        "Order_ID": [1, 2, 3],
        "Region": ["North", "South", "North"],
        "Product": ["Laptops", "Phones", "Laptops"],
        "Sales": [1000.0, 2000.0, 3000.0],
        "Profit": [100.0, 200.0, 300.0]
    })
    
    # 1. Average Sales
    res1 = AnalyticsEngine.process_nl_query("What is the average Sales?", df_sales)
    assert res1["status"] == "SUCCESS"
    assert res1["value"] == 2000.0
    
    # 2. Top Entity
    res2 = AnalyticsEngine.process_nl_query("Which product has the highest Sales?", df_sales)
    assert res2["status"] == "SUCCESS"
    assert "Laptops" in str(res2["top_entity"])
    
    # 3. Missing Column
    res3 = AnalyticsEngine.process_nl_query("What is the average Salary?", df_sales)
    assert res3["status"] == "ERROR"
    assert "Salary" in res3["error_message"]

# 6. M10 Model Inference using Saved Feature Metadata
def test_m10_model_inference_pipeline():
    df = pd.DataFrame({
        "Region": ["North", "South", "East", "West", "North", "South", "East", "West"],
        "Product": ["Laptops", "Phones", "Tablets", "Laptops", "Phones", "Tablets", "Laptops", "Phones"],
        "Quantity": [10, 25, 15, 30, 8, 12, 18, 22],
        "Unit_Price": [500, 200, 150, 600, 220, 180, 520, 210],
        "Discount": [0.05, 0.1, 0.0, 0.15, 0.05, 0.0, 0.1, 0.05],
        "Profit": [120, 80, 50, 150, 65, 45, 130, 75]
    })
    res = AutoMLEngine.train_and_evaluate(df, target_column="Profit", task_type="regression")
    model_path = res["model_file_path"]
    assert os.path.exists(model_path)
    
    artifact = joblib.load(model_path)
    feature_cols = artifact["feature_cols"]
    assert "Profit" not in feature_cols
    assert "Quantity" in feature_cols
    assert "Region" in feature_cols
    
    # Execute inference
    input_data = pd.DataFrame([{
        "Region": "North",
        "Product": "Laptops",
        "Quantity": 15,
        "Unit_Price": 550,
        "Discount": 0.05
    }])[feature_cols]
    
    pred = artifact["pipeline"].predict(input_data)
    assert len(pred) == 1
    assert isinstance(float(pred[0]), float)

# 7. M11 — PDF generation with REAL content (non-blank)
def test_m11_pdf_has_visible_content():
    """Verify the generated PDF is not blank and contains expected text."""
    data_dict = {
        "dataset_info": {
            "name": "pragyadrishti_sales_test_dataset",
            "row_count": 102,
            "col_count": 9,
            "quality_score": 98.5,
            "columns": ["Order_ID", "Date", "Region", "Product", "Quantity",
                         "Unit_Price", "Discount", "Sales", "Profit"],
        },
        "column_details": [
            {"name": "Order_ID", "dtype": "int64", "non_null": 102, "null_count": 0, "unique": 102},
            {"name": "Region", "dtype": "object", "non_null": 102, "null_count": 0, "unique": 4},
            {"name": "Sales", "dtype": "float64", "non_null": 102, "null_count": 0, "unique": 95},
        ],
        "numeric_stats": {
            "Sales": {"count": 102.0, "mean": 2500.0, "std": 500.0,
                      "min": 100.0, "25%": 2000.0, "50%": 2500.0, "75%": 3000.0, "max": 5000.0},
        },
        "categorical_summaries": {
            "Region": {"North": 30, "South": 25, "East": 25, "West": 22},
        },
        "missing_summary": {"Order_ID": 0, "Sales": 0},
        "total_missing": 0,
        "duplicate_count": 0,
        "trained_models": [],
        "sample_rows": [
            {"Order_ID": 1, "Region": "North", "Product": "Laptops", "Sales": 1500.0, "Profit": 200.0},
        ],
        "data": [],
    }

    pdf_path = ReportService.generate_report(
        "PragyaDrishti Data Analytics Report",
        "PDF",
        "Executive report for pragyadrishti_sales_test_dataset (102 rows, 9 columns). Quality score: 98.5%.",
        data_dict,
    )

    # 1. File must exist
    assert os.path.exists(pdf_path), "PDF file was not created"

    # 2. Must be reasonably sized (not tiny stub)
    file_size = os.path.getsize(pdf_path)
    assert file_size > 500, f"PDF is only {file_size} bytes — likely blank"

    # 3. Valid PDF header
    with open(pdf_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-", f"Invalid PDF header: {header}"

    # 4. Text extraction — requires PyPDF2 (optional but highly recommended)
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        assert len(reader.pages) >= 1, "PDF has zero pages"
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or ""

        # The extracted text MUST contain our report title and dataset name
        assert "PragyaDrishti" in full_text or "Analytics" in full_text, \
            f"PDF text does not contain report title. Extracted: {full_text[:300]}"
        assert "pragyadrishti_sales_test_dataset" in full_text, \
            f"PDF text does not contain dataset name. Extracted: {full_text[:300]}"
        assert "102" in full_text, \
            f"PDF text does not contain row count. Extracted: {full_text[:300]}"
    except ImportError:
        # PyPDF2 not installed — fall back to byte-level check
        with open(pdf_path, "rb") as f:
            raw = f.read()
        # PDF content stream should contain at least our dataset name
        assert b"pragyadrishti" in raw.lower() or b"sales" in raw.lower(), \
            "PDF raw bytes do not contain any dataset reference"


def test_m11_excel_report():
    """Excel report contains overview and data sheets."""
    data_dict = {
        "dataset_info": {"name": "Sales2026", "row_count": 102, "col_count": 9, "quality_score": 98.5,
                         "columns": ["Sales", "Profit"]},
        "column_details": [
            {"name": "Sales", "dtype": "float64", "non_null": 102, "null_count": 0, "unique": 95},
        ],
        "numeric_stats": {"Sales": {"count": 102, "mean": 2500}},
        "data": [{"Sales": 100, "Profit": 20}, {"Sales": 200, "Profit": 40}],
    }
    path = ReportService.generate_report("Excel Report", "EXCEL", "Summary", data_dict)
    assert os.path.exists(path)
    assert path.endswith(".xlsx")
    # Verify the file is a valid workbook
    xl = pd.ExcelFile(path, engine="openpyxl")
    assert "Summary" in xl.sheet_names


def test_m11_html_report():
    """HTML report contains expected content."""
    data_dict = {
        "dataset_info": {"name": "HouseDS", "row_count": 5, "col_count": 3, "quality_score": 100},
    }
    path = ReportService.generate_report("HTML Report", "HTML", "Summary", data_dict)
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    assert "HouseDS" in html
    assert "HTML Report" in html


def test_m11_pdf_empty_dataset():
    """PDF generated without a dataset should still be valid (no crash)."""
    path = ReportService.generate_report(
        "No Dataset Report", "PDF", "Generated without a dataset.", {"data": []}
    )
    assert os.path.exists(path)
    size = os.path.getsize(path)
    assert size >= 500
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-"

def test_m11_invalid_dataset_id():
    """Generating report with non-existent dataset ID raises 404."""
    from app.api.v1.reports import generate_report
    from app.core.database import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    with pytest.raises(HTTPException) as exc_info:
        generate_report(title="Test", report_type="PDF", summary="Sum", dataset_id=99999, db=session)
    assert exc_info.value.status_code == 404

def test_m11_missing_dataset_file():
    """Generating report where dataset file is missing from disk raises 404."""
    from app.api.v1.reports import generate_report
    from app.core.database import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    ds = Dataset(name="MissingFileDS", filename="missing.csv", file_path="/non/existent/path/missing.csv")
    session.add(ds)
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        generate_report(title="Test", report_type="PDF", summary="Sum", dataset_id=ds.id, db=session)
    assert exc_info.value.status_code == 404

def test_m11_house_vs_sales_isolation():
    """Verify House report contains House metrics and Sales report contains Sales metrics (no cross-contamination)."""
    from app.api.v1.reports import generate_report
    with tempfile.TemporaryDirectory() as tmpdir:
        house_csv = os.path.join(tmpdir, "House.csv")
        sales_csv = os.path.join(tmpdir, "Sales.csv")

        pd.DataFrame({
            "House_Name": ["Villa A", "Cottage B", "Penthouse C"],
            "SquareFeet": [2500, 1200, 3400],
            "Price": [750000, 320000, 1100000]
        }).to_csv(house_csv, index=False)

        pd.DataFrame({
            "Order_ID": [101, 102],
            "Product": ["Laptops", "Phones"],
            "Sales": [1200.0, 800.0]
        }).to_csv(sales_csv, index=False)

        from app.core.database import Base
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        ds_house = Dataset(name="House", filename="House.csv", file_path=house_csv)
        ds_sales = Dataset(name="pragyadrishti_sales_test_dataset", filename="Sales.csv", file_path=sales_csv)
        session.add(ds_house)
        session.add(ds_sales)
        session.commit()

        # Generate House report
        rep_house = generate_report("House Report", "PDF", "House Summary", dataset_id=ds_house.id, db=session)
        assert os.path.exists(rep_house.file_path)
        assert os.path.getsize(rep_house.file_path) >= 500

        # Generate Sales report
        rep_sales = generate_report("Sales Report", "PDF", "Sales Summary", dataset_id=ds_sales.id, db=session)
        assert os.path.exists(rep_sales.file_path)
        assert os.path.getsize(rep_sales.file_path) >= 500

        with open(rep_house.file_path, "rb") as f:
            house_bytes = f.read()
        with open(rep_sales.file_path, "rb") as f:
            sales_bytes = f.read()

        assert b"%PDF-" in house_bytes
        assert b"%PDF-" in sales_bytes

        # If PyPDF2 is available, verify exact text isolation
        try:
            from PyPDF2 import PdfReader
            reader_h = PdfReader(rep_house.file_path)
            text_h = "".join(p.extract_text() or "" for p in reader_h.pages)
            assert "House" in text_h
            assert "SquareFeet" in text_h
            assert "Order_ID" not in text_h

            reader_s = PdfReader(rep_sales.file_path)
            text_s = "".join(p.extract_text() or "" for p in reader_s.pages)
            assert "pragyadrishti_sales_test_dataset" in text_s
            assert "Laptops" in text_s
            assert "SquareFeet" not in text_s
        except ImportError:
            pass

def test_m11_download_endpoint_validation():
    """Verify download_report endpoint returns 404 for invalid report ID and FileResponse with correct headers for valid report."""
    from app.api.v1.reports import download_report
    from app.core.database import Base
    from app.models.report import Report
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    with pytest.raises(HTTPException) as exc_info:
        download_report(report_id=99999, db=session)
    assert exc_info.value.status_code == 404

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(b"%PDF-1.4\n1 0 obj\n<</Type/Catalog>>\nendobj\n%%EOF\n")
        temp_pdf = tf.name

    try:
        rep = Report(title="Test DL", report_type="PDF", file_path=temp_pdf, summary_text="Sum")
        session.add(rep)
        session.commit()

        resp = download_report(report_id=rep.id, db=session)
        assert resp.media_type == "application/pdf"
        assert os.path.basename(temp_pdf) in resp.headers["Content-Disposition"]
    finally:
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)

# 8. M4 Auto Data Cleaning Returns Both Operations Keys
def test_m4_data_cleaning_operations():
    df_dirty = pd.DataFrame({
        "A": [1, 2, None, 4, 1],
        "B": ["X", "Y", "Z", None, "X"],
        "C": [10.0, 20.0, 30.0, 1000.0, 10.0]
    })
    cleaned_df, report = DataCleaner.auto_clean(df_dirty)
    assert "operations" in report
    assert "operations_performed" in report
    assert len(report["operations"]) > 0
    assert report["duplicates_removed"] == 1
    assert report["missing_after"] == 0

# 9. Verification that Face Recognition is Completely Removed
def test_face_recognition_permanently_removed():
    route_paths = [route.path for route in app.routes]
    for p in route_paths:
        assert "/face-recognition" not in p, f"Found lingering face-recognition route: {p}"
        assert "recognize" not in p, f"Found lingering face recognize route: {p}"

# 10. Dataset Deduplication Logic
def test_dataset_deduplication():
    from app.core.database import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    d1 = Dataset(name="TestDS", filename="test.csv", file_path="/tmp/test.csv")
    d2 = Dataset(name="TestDS", filename="test.csv", file_path="/tmp/test.csv")
    session.add(d1)
    session.add(d2)
    session.commit()

    all_before = session.query(Dataset).all()
    assert len(all_before) == 2

    deduplicate_dataset_records(session)

    all_after = session.query(Dataset).all()
    assert len(all_after) == 1
    assert all_after[0].filename == "test.csv"
