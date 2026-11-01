from pathlib import Path
import csv
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.cell import coordinate_from_string

def write_cell(path: str, cell: str, value):
    suffix = Path(path).suffix.lower()
    if suffix not in {".xlsx", ".xlsm"}:
        raise ValueError("Cell editing is supported for XLSX/XLSM files. Export CSV/TSV data separately.")
    wb = load_workbook(path, keep_vba=suffix == ".xlsm")
    try:
        ws = wb.active
        # Validate the address before assignment.
        coordinate_from_string(cell)
        ws[cell] = value
        wb.save(path)
    finally:
        wb.close()

def export_dataframe(df: pd.DataFrame, path: str):
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix == ".tsv":
        df.to_csv(path, sep="\t", index=False)
    else:
        df.to_excel(path, index=False, engine="openpyxl")
