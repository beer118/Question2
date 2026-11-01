from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils.cell import range_boundaries

def _open(path):
    suffix = Path(path).suffix.lower()
    if suffix not in {".xlsx", ".xlsm"}:
        raise ValueError("Excel formatting requires XLSX or XLSM.")
    return load_workbook(path, keep_vba=suffix == ".xlsm")

def format_header(path: str):
    wb = _open(path)
    try:
        ws = wb.active
        fill = PatternFill("solid", fgColor="1D4ED8")
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = fill
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        wb.save(path)
    finally:
        wb.close()

def highlight_negative(path: str, cell_range=None):
    wb = _open(path)
    try:
        ws = wb.active
        target = cell_range or ws.dimensions
        # Ensure a syntactically valid range.
        range_boundaries(target)
        rule = CellIsRule(operator="lessThan", formula=["0"],
                          fill=PatternFill("solid", fgColor="FECACA"),
                          font=Font(color="991B1B"))
        ws.conditional_formatting.add(target, rule)
        wb.save(path)
    finally:
        wb.close()
