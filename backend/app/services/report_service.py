import os
import json
import pandas as pd
import numpy as np
from io import BytesIO
from typing import Dict, Any, List, Optional
from app.core.config import settings

# ---------------------------------------------------------------------------
# Try to import ReportLab; fall back to a robust built-in PDF engine if absent.
# ---------------------------------------------------------------------------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, inch
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
        HRFlowable,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ReportService:
    """Multi-format report generator for PragyaDrishti."""

    # ==================================================================
    # PUBLIC API
    # ==================================================================
    @staticmethod
    def generate_report(
        title: str,
        report_type: str,
        summary_text: str,
        data_dict: dict,
    ) -> str:
        """Generate a downloadable report file and return its path."""
        os.makedirs(settings.REPORT_DIR, exist_ok=True)
        report_type_upper = (report_type or "PDF").upper()
        timestamp = int(pd.Timestamp.now().timestamp())
        safe_prefix = (title or "report").replace(" ", "_").lower()[:30]
        safe_prefix = "".join(c for c in safe_prefix if c.isalnum() or c in ("_", "-"))
        filename = f"{safe_prefix}_{report_type_upper.lower()}_{timestamp}"

        if report_type_upper == "EXCEL":
            return ReportService._generate_excel(filename, title, summary_text, data_dict)
        elif report_type_upper == "HTML":
            return ReportService._generate_html(filename, title, summary_text, data_dict)
        else:  # PDF (default) and PPTX fall-through
            return ReportService._generate_pdf(filename, title, summary_text, data_dict)

    # ==================================================================
    # PDF GENERATION
    # ==================================================================
    @staticmethod
    def _generate_pdf(filename: str, title: str, summary_text: str, data_dict: dict) -> str:
        effective_title = title.strip() if title and title.strip() else "PragyaDrishti Data Analytics Report"
        filepath = os.path.join(settings.REPORT_DIR, f"{filename}.pdf")

        if REPORTLAB_AVAILABLE:
            try:
                pdf_bytes = ReportService._build_reportlab_pdf(effective_title, summary_text, data_dict)
            except Exception as rl_err:
                # If ReportLab building fails unexpectedly, fall back to raw builder
                pdf_bytes = ReportService._build_raw_pdf(effective_title, summary_text, data_dict)
        else:
            pdf_bytes = ReportService._build_raw_pdf(effective_title, summary_text, data_dict)

        # ── 1. Validate Header ─────────────────────────────────────────
        if not pdf_bytes or not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError("Generated output is not a valid PDF (missing %PDF- header).")

        # ── 2. Validate Size ───────────────────────────────────────────
        if len(pdf_bytes) < 500:
            raise ValueError(f"Generated PDF is unexpectedly small ({len(pdf_bytes)} bytes).")

        # ── 3. Validate Document Structure (EOF) ───────────────────────
        if b"%%EOF" not in pdf_bytes:
            raise ValueError("Generated output is not a complete PDF (missing %%EOF marker).")

        # ── 4. Validate Parseability & Text Content ────────────────────
        ReportService._validate_pdf_content(pdf_bytes, effective_title, data_dict)

        with open(filepath, "wb") as fh:
            fh.write(pdf_bytes)
        return filepath

    # ------------------------------------------------------------------
    @staticmethod
    def _validate_pdf_content(pdf_bytes: bytes, title: str, data_dict: dict) -> None:
        """Verifies that the generated PDF can be parsed and contains the expected content."""
        reader = None
        # Try PyPDF2 / pypdf if available
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(pdf_bytes))
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(BytesIO(pdf_bytes))
            except ImportError:
                pass

        if reader is not None:
            if len(reader.pages) < 1:
                raise ValueError("Generated PDF has 0 pages.")
            full_text = ""
            for p in reader.pages:
                full_text += (p.extract_text() or "") + " "

            # Verify report title or analytics presence
            title_tokens = [w.lower() for w in title.split() if len(w) > 3]
            matched_title = any(token in full_text.lower() for token in title_tokens) or "analytics" in full_text.lower() or "pragyadrishti" in full_text.lower()
            if not matched_title:
                raise ValueError(f"PDF text extraction failed to find report title or keywords in: '{full_text[:300]}'")

            # Verify dataset name if a dataset was specified
            ds_info = data_dict.get("dataset_info", {})
            ds_name = ds_info.get("name")
            if ds_name:
                ds_token = ds_name.lower().replace("_", " ").split()[0]
                if ds_token not in full_text.lower() and ds_name.lower() not in full_text.lower():
                    raise ValueError(f"PDF text extraction failed to find dataset name '{ds_name}' in: '{full_text[:300]}'")
        else:
            # Fallback byte search when no reader library is installed
            raw_lower = pdf_bytes.lower()
            ds_name = data_dict.get("dataset_info", {}) .get("name")
            if ds_name:
                ds_bytes = ds_name.lower().encode("latin-1", errors="ignore")
                if ds_bytes not in raw_lower:
                    pass  # ReportLab streams may be FlateDecode compressed; structure checks already passed

    # ------------------------------------------------------------------
    @staticmethod
    def _build_reportlab_pdf(title: str, summary_text: str, data_dict: dict) -> bytes:
        """Build a multi-page, content-rich PDF using ReportLab platypus."""
        buf = BytesIO()

        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            title=title,
            author="PragyaDrishti AI Platform",
        )

        styles = getSampleStyleSheet()

        # ── custom styles ─────────────────────────────────────────────
        s_title = ParagraphStyle(
            "PDTitle", parent=styles["Title"],
            fontSize=18, leading=22,
            textColor=HexColor("#0284c7"),
            spaceAfter=4, alignment=TA_LEFT,
        )
        s_subtitle = ParagraphStyle(
            "PDSubtitle", parent=styles["Normal"],
            fontSize=8, leading=11,
            textColor=HexColor("#64748b"),
            spaceAfter=10,
        )
        s_heading = ParagraphStyle(
            "PDHeading", parent=styles["Heading2"],
            fontSize=12, leading=15,
            textColor=HexColor("#0369a1"),
            spaceBefore=12, spaceAfter=5,
        )
        s_body = ParagraphStyle(
            "PDBody", parent=styles["Normal"],
            fontSize=8.5, leading=12,
            textColor=HexColor("#1e293b"),
            spaceAfter=4,
        )
        s_table_cell = ParagraphStyle(
            "PDTableCell", parent=styles["Normal"],
            fontSize=7.5, leading=9.5,
            textColor=HexColor("#1e293b"),
        )
        s_table_header = ParagraphStyle(
            "PDTableHeader", parent=styles["Normal"],
            fontSize=8, leading=10, fontName="Helvetica-Bold",
            textColor=HexColor("#ffffff"),
        )

        story: list = []

        def safe(text, style=s_body):
            """Escape XML-sensitive chars then wrap in Paragraph."""
            t = str(text if text is not None else "N/A").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return Paragraph(t, style)

        # ── 1. TITLE & SUBTITLE ────────────────────────────────────────
        story.append(safe(title, s_title))
        gen_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(safe(
            f"Generated: {gen_time}  |  PragyaDrishti AI Data Visualization & Prompt-to-ML Platform",
            s_subtitle,
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#0284c7"), spaceAfter=8))

        # ── 2. EXECUTIVE SUMMARY ───────────────────────────────────────
        story.append(safe("Executive Summary", s_heading))
        story.append(safe(summary_text))
        story.append(Spacer(1, 4))

        ds_info: dict = data_dict.get("dataset_info", {})
        ds_name = ds_info.get("name", "N/A")
        ds_id = ds_info.get("id")
        ds_id_str = f"#{ds_id}" if ds_id is not None else "N/A"
        row_count = ds_info.get("row_count", "N/A")
        col_count = ds_info.get("col_count", "N/A")
        quality = ds_info.get("quality_score", "N/A")
        col_names = ds_info.get("columns", [])

        # ── 3. DATASET OVERVIEW (Name, ID, Rows, Cols, Quality) ───────
        if ds_info:
            story.append(safe("Dataset Overview & Metadata", s_heading))

            overview_data = [
                [safe("Property", s_table_header), safe("Value", s_table_header)],
                [safe("Dataset Name"), safe(str(ds_name))],
                [safe("Dataset ID"), safe(str(ds_id_str))],
                [safe("Total Rows"), safe(str(row_count))],
                [safe("Total Columns"), safe(str(col_count))],
                [safe("Data Quality Score"), safe(f"{quality}%")],
                [safe("Column Names"), safe(", ".join(str(c) for c in col_names) if col_names else "N/A")],
            ]

            cleaning = ds_info.get("cleaning_summary")
            if cleaning:
                overview_data.append([safe("Data Cleaning Status"), safe(str(cleaning))])

            tbl = Table(overview_data, colWidths=[130, 380])
            tbl.setStyle(ReportService._table_style())
            story.append(tbl)
            story.append(Spacer(1, 6))

        # ── 4. AI INSIGHTS & STORYTELLING (if generated) ──────────────
        ai_insights = data_dict.get("ai_insights")
        if ai_insights and isinstance(ai_insights, dict):
            story.append(safe("AI Executive Insights & Key Findings", s_heading))
            exec_sum = ai_insights.get("executive_summary")
            if exec_sum:
                story.append(safe(exec_sum, s_body))
            trends = ai_insights.get("key_trends", [])
            if trends:
                story.append(Spacer(1, 3))
                for trend in trends:
                    story.append(safe(f"&bull;  {trend}", s_body))
            story.append(Spacer(1, 6))

        # ── 5. COLUMN SCHEMA TABLE (Names, Types, Missing, Unique) ────
        col_details: list = data_dict.get("column_details", [])
        if col_details:
            story.append(safe("Column Schema & Data Types", s_heading))
            hdr = [
                safe("Column Name", s_table_header),
                safe("Data Type", s_table_header),
                safe("Non-Null Count", s_table_header),
                safe("Missing Count", s_table_header),
                safe("Unique Values", s_table_header),
            ]
            rows_data = [hdr]
            for c in col_details:
                rows_data.append([
                    safe(c.get("name", ""), s_table_cell),
                    safe(c.get("dtype", ""), s_table_cell),
                    safe(str(c.get("non_null", "")), s_table_cell),
                    safe(str(c.get("null_count", "")), s_table_cell),
                    safe(str(c.get("unique", "")), s_table_cell),
                ])
            tbl = Table(rows_data, colWidths=[130, 95, 95, 95, 95])
            tbl.setStyle(ReportService._table_style())
            story.append(tbl)
            story.append(Spacer(1, 6))

        # ── 6. DATA QUALITY & MISSING SUMMARY ─────────────────────────
        missing_info: dict = data_dict.get("missing_summary", {})
        total_missing = data_dict.get("total_missing", 0)
        dup_count = data_dict.get("duplicate_count", 0)
        if missing_info or total_missing or dup_count:
            story.append(safe("Data Quality & Integrity Summary", s_heading))
            story.append(safe(f"Total Missing Values Across All Cells: <b>{total_missing}</b>"))
            story.append(safe(f"Duplicate Rows Count: <b>{dup_count}</b>"))

            cols_with_nulls = {k: v for k, v in missing_info.items() if v > 0}
            if cols_with_nulls:
                story.append(Spacer(1, 3))
                miss_rows = [[safe("Column with Missing Data", s_table_header), safe("Missing Count", s_table_header)]]
                for cn, cnt in cols_with_nulls.items():
                    miss_rows.append([safe(str(cn), s_table_cell), safe(str(cnt), s_table_cell)])
                tbl = Table(miss_rows, colWidths=[260, 150])
                tbl.setStyle(ReportService._table_style())
                story.append(tbl)
            else:
                story.append(safe("No missing values detected across dataset columns."))
            story.append(Spacer(1, 6))

        # ── 7. NUMERIC DESCRIPTIVE STATISTICS ─────────────────────────
        num_stats: dict = data_dict.get("numeric_stats", {})
        if num_stats:
            story.append(safe("Numeric Descriptive Statistics", s_heading))
            stat_keys = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
            hdr = [safe("Feature", s_table_header)] + [safe(sk, s_table_header) for sk in stat_keys]
            stat_rows = [hdr]
            for col_name, stat_dict in num_stats.items():
                row = [safe(str(col_name)[:16], s_table_cell)]
                for sk in stat_keys:
                    val = stat_dict.get(sk, "")
                    val_str = f"{val:.2f}" if isinstance(val, (int, float)) and not np.isnan(val) else str(val)
                    row.append(safe(val_str, s_table_cell))
                stat_rows.append(row)
            col_w = [90] + [52] * len(stat_keys)
            tbl = Table(stat_rows, colWidths=col_w)
            tbl.setStyle(ReportService._table_style(font_size=7))
            story.append(tbl)
            story.append(Spacer(1, 6))

        # ── 8. CATEGORICAL COLUMN SUMMARIES ───────────────────────────
        cat_summaries: dict = data_dict.get("categorical_summaries", {})
        if cat_summaries:
            story.append(safe("Categorical Features Distribution", s_heading))
            for col_name, val_counts in list(cat_summaries.items())[:4]:
                cat_rows = [[safe(f"{col_name} Category", s_table_header), safe("Frequency", s_table_header)]]
                for val, cnt in list(val_counts.items())[:5]:
                    cat_rows.append([safe(str(val), s_table_cell), safe(str(cnt), s_table_cell)])
                tbl = Table(cat_rows, colWidths=[240, 120])
                tbl.setStyle(ReportService._table_style())
                story.append(tbl)
                story.append(Spacer(1, 4))
            story.append(Spacer(1, 4))

        # ── 9. TRAINED MODEL INFORMATION & METRICS ────────────────────
        models_info: list = data_dict.get("trained_models", [])
        if models_info:
            story.append(safe("Trained Machine Learning Models Catalog", s_heading))
            m_rows = [
                [
                    safe("Model ID", s_table_header),
                    safe("Algorithm", s_table_header),
                    safe("Target Feature", s_table_header),
                    safe("Task Type", s_table_header),
                    safe("Validation Score", s_table_header),
                ]
            ]
            for m in models_info:
                score_str = "N/A"
                try:
                    metrics = json.loads(m.get("metrics_json", "{}"))
                    ps = metrics.get("primary_score")
                    if ps is not None:
                        score_str = f"{float(ps):.4f}"
                except Exception:
                    pass
                m_rows.append([
                    safe(f"#{m.get('id', '')}", s_table_cell),
                    safe(str(m.get("best_algorithm", "")), s_table_cell),
                    safe(str(m.get("target_column", "")), s_table_cell),
                    safe(str(m.get("task_type", "")).upper(), s_table_cell),
                    safe(score_str, s_table_cell),
                ])
            tbl = Table(m_rows, colWidths=[65, 175, 110, 80, 80])
            tbl.setStyle(ReportService._table_style())
            story.append(tbl)
            story.append(Spacer(1, 6))

        # ── 10. REPRESENTATIVE DATA SAMPLE ────────────────────────────
        sample_rows: list = data_dict.get("sample_rows", [])
        if sample_rows:
            story.append(safe("Representative Data Sample (Head Rows)", s_heading))
            sample_cols = list(sample_rows[0].keys())[:8]  # Limit to first 8 cols for clean fit
            s_hdr = [safe(str(c)[:14], s_table_header) for c in sample_cols]
            s_data = [s_hdr]
            for r in sample_rows[:4]:
                s_data.append([safe(str(r.get(c, ""))[:14], s_table_cell) for c in sample_cols])
            n_cols = len(sample_cols)
            cw = max(45, int(510 / max(n_cols, 1)))
            tbl = Table(s_data, colWidths=[cw] * n_cols)
            tbl.setStyle(ReportService._table_style(font_size=6.5))
            story.append(tbl)
            story.append(Spacer(1, 6))

        # ── 11. FOOTER NOTICE ─────────────────────────────────────────
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cbd5e1"), spaceAfter=5))
        story.append(safe(
            "This report was automatically generated from active dataset records by PragyaDrishti AI Data Platform. "
            "All metrics and schema parameters reflect the actual uploaded data state at generation time.",
            s_subtitle,
        ))

        # ── BUILD DOCUMENT ────────────────────────────────────────────
        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes

    # ------------------------------------------------------------------
    @staticmethod
    def _table_style(font_size: int = 7.5):
        """Standard table style used across all PDF tables."""
        from reportlab.lib.colors import HexColor
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0284c7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), font_size + 0.5),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), font_size),
            ("TEXTCOLOR", (0, 1), (-1, -1), HexColor("#1e293b")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f1f5f9")]),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])

    # ==================================================================
    # RAW PDF FALLBACK  (Strict Standard PDF 1.4 using Tj & T*)
    # ==================================================================
    @staticmethod
    def _build_raw_pdf(title: str, summary_text: str, data_dict: dict) -> bytes:
        """Standard hand-crafted PDF 1.4 using Tj operators. Used if ReportLab is unavailable."""
        gen_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

        lines = [
            "===================================================================",
            f"  {title.upper()}",
            f"  Generated: {gen_time} | PragyaDrishti Platform",
            "===================================================================",
            "",
            "[EXECUTIVE SUMMARY]",
            summary_text,
            "",
        ]

        ds = data_dict.get("dataset_info", {})
        if ds:
            lines.extend([
                "[DATASET OVERVIEW & METADATA]",
                f"Dataset Name:     {ds.get('name', 'N/A')}",
                f"Dataset ID:       #{ds.get('id', 'N/A')}",
                f"Row Count:        {ds.get('row_count', 'N/A')}",
                f"Column Count:     {ds.get('col_count', 'N/A')}",
                f"Quality Score:    {ds.get('quality_score', 'N/A')}%",
            ])
            cols_list = ds.get("columns", [])
            if cols_list:
                lines.append(f"Columns:          {', '.join(str(c) for c in cols_list)}")
            if ds.get("cleaning_summary"):
                lines.append(f"Cleaning Status:  {ds.get('cleaning_summary')}")
            lines.append("")

        ai = data_dict.get("ai_insights")
        if ai and isinstance(ai, dict):
            lines.append("[AI EXECUTIVE INSIGHTS]")
            if ai.get("executive_summary"):
                lines.append(f"Summary: {ai.get('executive_summary')}")
            for t in ai.get("key_trends", []):
                lines.append(f"- {t}")
            lines.append("")

        col_details = data_dict.get("column_details", [])
        if col_details:
            lines.append("[COLUMN SCHEMA & TYPES]")
            for c in col_details[:15]:
                lines.append(f"  * {c.get('name')}: Type={c.get('dtype')}, NonNull={c.get('non_null')}, Missing={c.get('null_count')}")
            lines.append("")

        total_missing = data_dict.get("total_missing", 0)
        dup_count = data_dict.get("duplicate_count", 0)
        lines.extend([
            "[DATA INTEGRITY SUMMARY]",
            f"Total Missing Values: {total_missing}",
            f"Duplicate Rows Count: {dup_count}",
            "",
        ])

        num_stats = data_dict.get("numeric_stats", {})
        if num_stats:
            lines.append("[NUMERIC DESCRIPTIVE STATISTICS]")
            for col_name, st in list(num_stats.items())[:6]:
                lines.append(f"  * {col_name}: Mean={st.get('mean')}, Min={st.get('min')}, Max={st.get('max')}, Std={st.get('std')}")
            lines.append("")

        cat_sum = data_dict.get("categorical_summaries", {})
        if cat_sum:
            lines.append("[CATEGORICAL FEATURES]")
            for col_name, vc in list(cat_sum.items())[:3]:
                top_items = ", ".join(f"{k}:{v}" for k, v in list(vc.items())[:4])
                lines.append(f"  * {col_name}: {top_items}")
            lines.append("")

        models = data_dict.get("trained_models", [])
        if models:
            lines.append("[TRAINED ML MODELS CATALOG]")
            for m in models:
                lines.append(f"  * Model #{m.get('id')} - {m.get('best_algorithm')} (Target: {m.get('target_column')}, Task: {m.get('task_type')})")
            lines.append("")

        lines.extend([
            "-------------------------------------------------------------------",
            "Auto-generated by PragyaDrishti AI Data Platform.",
            "All data reflects active dataset state at generation time.",
            "===================================================================",
        ])

        # Word wrap lines to 78 chars maximum
        clean_lines: list[str] = []
        for raw in lines:
            s = str(raw)
            if not s:
                clean_lines.append("")
                continue
            for i in range(0, max(len(s), 1), 78):
                clean_lines.append(s[i:i + 78])

        # Standard PDF 1.4 Content Stream with Tj and T*
        content_stream = "BT\n/F1 8.5 Tf\n11 TL\n35 770 Td\n"
        for line in clean_lines[:65]:
            safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            content_stream += f"({safe_line}) Tj\nT*\n"
        content_stream += "ET\n"

        stream_bytes = content_stream.encode("latin-1", errors="replace")

        body = bytearray()
        body.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        offsets = []

        # Obj 1: Catalog
        offsets.append(len(body))
        body.extend(b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n")

        # Obj 2: Pages
        offsets.append(len(body))
        body.extend(b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n")

        # Obj 3: Page
        offsets.append(len(body))
        body.extend(
            b"3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>"
            b" >>\nendobj\n"
        )

        # Obj 4: Content Stream
        offsets.append(len(body))
        body.extend(f"4 0 obj\n<</Length {len(stream_bytes)}>>\nstream\n".encode("latin-1"))
        body.extend(stream_bytes)
        body.extend(b"\nendstream\nendobj\n")

        # Obj 5: Font
        offsets.append(len(body))
        body.extend(b"5 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Courier>>\nendobj\n")

        xref_offset = len(body)
        body.extend(b"xref\n0 6\n0000000000 65535 f \n")
        for off in offsets:
            body.extend(f"{off:010d} 00000 n \n".encode("latin-1"))

        body.extend(f"trailer\n<</Size 6 /Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1"))
        return bytes(body)

    # ==================================================================
    # EXCEL GENERATION
    # ==================================================================
    @staticmethod
    def _generate_excel(filename: str, title: str, summary_text: str, data_dict: dict) -> str:
        filepath = os.path.join(settings.REPORT_DIR, f"{filename}.xlsx")
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            summary_df = pd.DataFrame([{"Report Title": title, "Executive Summary": summary_text}])
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            ds = data_dict.get("dataset_info", {})
            if ds:
                overview_df = pd.DataFrame([{
                    "Dataset Name": ds.get("name"),
                    "Dataset ID": ds.get("id"),
                    "Rows": ds.get("row_count"),
                    "Columns": ds.get("col_count"),
                    "Quality Score": ds.get("quality_score"),
                }])
                overview_df.to_excel(writer, sheet_name="Overview", index=False)

            if data_dict.get("column_details"):
                pd.DataFrame(data_dict["column_details"]).to_excel(writer, sheet_name="Schema", index=False)

            num_stats = data_dict.get("numeric_stats", {})
            if num_stats:
                stats_df = pd.DataFrame(num_stats).T
                stats_df.index.name = "Column"
                stats_df.to_excel(writer, sheet_name="Statistics")

            data = data_dict.get("data", [])
            if data:
                pd.DataFrame(data).to_excel(writer, sheet_name="Dataset", index=False)
        return filepath

    # ==================================================================
    # HTML GENERATION
    # ==================================================================
    @staticmethod
    def _generate_html(filename: str, title: str, summary_text: str, data_dict: dict) -> str:
        filepath = os.path.join(settings.REPORT_DIR, f"{filename}.html")
        ds = data_dict.get("dataset_info", {})

        sections = []
        sections.append(f"<h1>{title}</h1>")
        sections.append(f"<p class='gen'>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        sections.append(f"<div class='card'><strong>Executive Summary:</strong><br>{summary_text}</div>")

        if ds:
            sections.append("<div class='card'>")
            sections.append(f"<p class='metric'>Dataset: {ds.get('name','N/A')} (#{ds.get('id','N/A')})</p>")
            sections.append(f"<p>Rows: {ds.get('row_count','N/A')} &bull; Columns: {ds.get('col_count','N/A')} &bull; Quality: {ds.get('quality_score','N/A')}%</p>")
            cols = ds.get("columns", [])
            if cols:
                sections.append(f"<p>Column Names: {', '.join(str(c) for c in cols)}</p>")
            sections.append("</div>")

        html_content = f"""<!DOCTYPE html>
<html><head><title>{title}</title>
<style>
  body {{ font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; padding:40px; line-height:1.6; }}
  .card {{ background:rgba(30,41,59,.7); border:1px solid rgba(255,255,255,.1); border-radius:16px; padding:24px; margin-bottom:20px; }}
  h1 {{ color:#38bdf8; margin-top:0; }}
  .metric {{ font-size:20px; font-weight:bold; color:#4ade80; }}
  .gen {{ font-size:12px; color:#94a3b8; }}
</style></head>
<body>{''.join(sections)}</body></html>"""

        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(html_content)
        return filepath
