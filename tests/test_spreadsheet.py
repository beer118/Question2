import pandas as pd
from openpyxl import Workbook, load_workbook
from spreadsheet.analysis import summarize, top_values
from spreadsheet.writer import write_cell
from spreadsheet.formatting import format_header, highlight_negative
from spreadsheet.charts import create_chart

def make_book(path):
    wb=Workbook()
    ws=wb.active
    ws.append(["Item","Revenue"])
    ws.append(["A",10])
    ws.append(["B",-5])
    ws.append(["C",30])
    wb.save(path)

def test_summary_and_top_values():
    df=pd.DataFrame({"Item":["A","B","C"],"Revenue":[10,-5,30]})
    assert summarize(df)["rows"] == 3
    assert top_values(df,"Revenue",2)["Revenue"].tolist() == [30,10]

def test_write_format_conditional_and_chart(tmp_path):
    path=str(tmp_path/"sample.xlsx")
    make_book(path)
    write_cell(path,"C2","=SUM(B2:B4)")
    format_header(path)
    highlight_negative(path)
    create_chart(path,"bar","Item","Revenue")
    wb=load_workbook(path, data_only=False)
    ws=wb.active
    assert ws["C2"].value == "=SUM(B2:B4)"
    assert ws["A1"].font.bold is True
    assert len(ws._charts) == 1
    assert len(ws.conditional_formatting) > 0
