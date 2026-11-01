from pathlib import Path
import pandas as pd
from openpyxl import load_workbook

def load_tabular(path: str, sheet_name=None) -> pd.DataFrame:
    suffix = Path(path).suffix.lower()
    if suffix in {".csv", ".tsv"}:
        sep = "\t" if suffix == ".tsv" else None
        return pd.read_csv(path, sep=sep, engine="python", encoding_errors="replace")
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(path, sheet_name=sheet_name or 0, engine="openpyxl")
    raise ValueError(f"Unsupported file extension: {suffix}")

def workbook_info(path: str) -> dict:
    suffix = Path(path).suffix.lower()
    if suffix in {".csv", ".tsv"}:
        df = load_tabular(path)
        return {"sheets": ["Data"], "active": "Data", "dimensions": {"Data": (len(df)+1, len(df.columns))}}
    wb = load_workbook(path, read_only=True, keep_vba=suffix == ".xlsm", data_only=False)
    try:
        dims = {ws.title: (ws.max_row, ws.max_column) for ws in wb.worksheets}
        return {"sheets": wb.sheetnames, "active": wb.active.title, "dimensions": dims}
    finally:
        wb.close()
