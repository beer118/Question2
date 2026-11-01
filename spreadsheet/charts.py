from pathlib import Path
from openpyxl import load_workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
import pandas as pd

def create_chart(path: str, kind="bar", x_column=None, y_column=None):
    suffix = Path(path).suffix.lower()
    if suffix not in {".xlsx", ".xlsm"}:
        raise ValueError("Embedded Excel charts require XLSX or XLSM.")
    wb = load_workbook(path, keep_vba=suffix == ".xlsm")
    try:
        ws = wb.active
        headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
        x_idx = headers.index(x_column) + 1 if x_column in headers else 1
        y_idx = headers.index(y_column) + 1 if y_column in headers else (2 if ws.max_column >= 2 else 1)
        kind = kind.lower()
        chart_cls = {"bar": BarChart, "line": LineChart, "pie": PieChart}.get(kind)
        if not chart_cls:
            raise ValueError("Chart kind must be bar, line, or pie.")
        chart = chart_cls()
        if kind == "pie":
            data = Reference(ws, min_col=y_idx, min_row=1, max_row=ws.max_row)
            chart.add_data(data, titles_from_data=True)
            cats = Reference(ws, min_col=x_idx, min_row=2, max_row=ws.max_row)
            chart.set_categories(cats)
        else:
            data = Reference(ws, min_col=y_idx, min_row=1, max_row=ws.max_row)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(Reference(ws, min_col=x_idx, min_row=2, max_row=ws.max_row))
        chart.title = f"{kind.title()} chart"
        chart.height, chart.width = 8, 16
        ws.add_chart(chart, "G2")
        wb.save(path)
    finally:
        wb.close()
