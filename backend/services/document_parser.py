"""Document parser service for extracting text and data from PDF and Excel files."""
import os
import pdfplumber
import pandas as pd
from openpyxl import load_workbook


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text content from a PDF file."""
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text}")

                # Also extract tables
                tables = page.extract_tables()
                for j, table in enumerate(tables):
                    if table:
                        text_parts.append(f"\n[Table {j + 1} on Page {i + 1}]")
                        for row in table:
                            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                            text_parts.append(" | ".join(cleaned_row))
    except Exception as e:
        text_parts.append(f"[Error extracting PDF: {str(e)}]")

    return "\n".join(text_parts)


def extract_text_from_excel(file_path: str) -> str:
    """Extract all data from an Excel file as formatted text."""
    text_parts = []
    try:
        xl = pd.ExcelFile(file_path)
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            text_parts.append(f"--- Sheet: {sheet_name} ---")

            # Add column headers
            text_parts.append(" | ".join(str(col) for col in df.columns))
            text_parts.append("-" * 80)

            # Add rows
            for _, row in df.iterrows():
                cleaned_row = [str(val).strip() if pd.notna(val) else "" for val in row]
                text_parts.append(" | ".join(cleaned_row))

            text_parts.append("")
    except Exception as e:
        text_parts.append(f"[Error extracting Excel: {str(e)}]")

    return "\n".join(text_parts)


def extract_text_from_csv(file_path: str) -> str:
    """Extract all data from a CSV file as formatted text."""
    text_parts = []
    try:
        df = pd.read_csv(file_path)
        text_parts.append(" | ".join(str(col) for col in df.columns))
        text_parts.append("-" * 80)

        for _, row in df.iterrows():
            cleaned_row = [str(val).strip() if pd.notna(val) else "" for val in row]
            text_parts.append(" | ".join(cleaned_row))
    except Exception as e:
        text_parts.append(f"[Error extracting CSV: {str(e)}]")

    return "\n".join(text_parts)


def parse_document(file_path: str) -> str:
    """
    Parse a document and return extracted text.
    Supports PDF, Excel (.xlsx/.xls), and CSV files.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".xlsx", ".xls"):
        return extract_text_from_excel(file_path)
    elif ext == ".csv":
        return extract_text_from_csv(file_path)
    else:
        return f"[Unsupported file format: {ext}]"
