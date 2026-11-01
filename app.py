import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from agent.engine import plan_request
from spreadsheet.reader import load_tabular, workbook_info
from spreadsheet.analysis import summarize, top_values
from spreadsheet.writer import write_cell, export_dataframe
from spreadsheet.formatting import format_header, highlight_negative
from spreadsheet.charts import create_chart

st.set_page_config(page_title="Excel Agent", page_icon="📊", layout="wide")
st.title("📊 Excel Agent")
st.caption("A local-first spreadsheet assistant · XLSX, XLSM, CSV and TSV")

if "work_path" not in st.session_state:
    st.session_state.work_path = None
if "original_name" not in st.session_state:
    st.session_state.original_name = None
if "chat" not in st.session_state:
    st.session_state.chat = []
if "pending_plan" not in st.session_state:
    st.session_state.pending_plan = None

with st.sidebar:
    st.subheader("Workbook")
    uploaded = st.file_uploader("Upload a spreadsheet", type=["xlsx", "xlsm", "csv", "tsv"])
    if uploaded:
        suffix = Path(uploaded.name).suffix.lower()
        if st.session_state.original_name != uploaded.name or st.session_state.work_path is None:
            fd, p = tempfile.mkstemp(suffix=suffix, prefix="excel_agent_")
            os.close(fd)
            with open(p, "wb") as f:
                f.write(uploaded.getvalue())
            st.session_state.work_path = p
            st.session_state.original_name = uploaded.name
            st.session_state.chat = []
            st.session_state.pending_plan = None
    st.caption("Edits apply to a working copy. Your uploaded original is not overwritten.")
    if st.session_state.work_path and st.button("Reset working copy"):
        fd, p = tempfile.mkstemp(suffix=Path(st.session_state.original_name).suffix.lower(), prefix="excel_agent_")
        os.close(fd)
        with open(p, "wb") as f:
            f.write(uploaded.getvalue())
        st.session_state.work_path = p
        st.session_state.chat = []
        st.session_state.pending_plan = None
        st.rerun()

path = st.session_state.work_path
if not path:
    st.info("Upload an Excel or delimited-text file in the sidebar to begin.")
    st.markdown("### Try asking")
    st.markdown("- Summarize this sheet\n- Show the five largest values in a numeric column\n- Make the header row bold and blue\n- Highlight negative values\n- Create a bar chart")
    st.stop()

try:
    info = workbook_info(path)
    suffix = Path(path).suffix.lower()
    sheet = "Data"
    if suffix in {".xlsx", ".xlsm"}:
        sheet = st.selectbox("Worksheet", info["sheets"], index=info["sheets"].index(info["active"]) if info["active"] in info["sheets"] else 0)
    df = load_tabular(path, sheet_name=sheet if suffix in {".xlsx", ".xlsm"} else None)
except Exception as e:
    st.error(f"Could not read workbook: {e}")
    st.stop()

m1, m2, m3 = st.columns(3)
m1.metric("Rows", f"{len(df):,}")
m2.metric("Columns", f"{len(df.columns):,}")
m3.metric("Format", suffix.upper().replace(".", ""))

tab_data, tab_analysis, tab_edit, tab_agent = st.tabs(["Data preview", "Analysis & charts", "Edit workbook", "AI agent"])

with tab_data:
    st.subheader("Data preview")
    st.dataframe(df.head(500), use_container_width=True, height=420)
    st.caption(f"Showing up to 500 rows · {len(df.columns)} columns")
    st.download_button("Download current data as CSV", df.to_csv(index=False).encode("utf-8"), file_name="spreadsheet-preview.csv", mime="text/csv")

with tab_analysis:
    st.subheader("Data summary")
    summary = summarize(df)
    c1, c2 = st.columns(2)
    c1.json({"rows": summary["rows"], "columns": summary["columns"], "columns_names": summary["column_names"]})
    c2.dataframe(pd.DataFrame({"Missing values": summary["missing_by_column"]}), use_container_width=True)
    with st.expander("Numeric statistics"):
        st.dataframe(df.describe(include="number").T if not df.select_dtypes(include="number").empty else pd.DataFrame(), use_container_width=True)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    if len(df.columns) >= 2:
        cols = st.columns(3)
        xcol = cols[0].selectbox("Category / X", list(df.columns), key="chart_x")
        ychoices = numeric_cols or list(df.columns)
        ycol = cols[1].selectbox("Values / Y", ychoices, key="chart_y")
        kind = cols[2].selectbox("Chart type", ["bar", "line", "pie"])
        try:
            plot_df = df[[xcol, ycol]].copy()
            plot_df[ycol] = pd.to_numeric(plot_df[ycol], errors="coerce")
            plot_df = plot_df.dropna().head(100)
            if kind == "pie":
                st.pyplot(__import__("matplotlib.pyplot", fromlist=["pyplot"]).figure())
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots()
                ax.pie(plot_df[ycol], labels=plot_df[xcol].astype(str), autopct="%1.1f%%")
                ax.set_title(f"{ycol} by {xcol}")
                st.pyplot(fig)
                plt.close(fig)
            else:
                plot_df = plot_df.set_index(xcol)
                st.bar_chart(plot_df) if kind == "bar" else st.line_chart(plot_df)
        except Exception as e:
            st.warning(f"Could not plot these columns: {e}")
    else:
        st.info("A chart needs at least two columns.")

with tab_edit:
    st.subheader("Edit workbook")
    if suffix in {".xlsx", ".xlsm"}:
        with st.form("write_cell_form"):
            st.markdown("**Write a cell value or formula**")
            cell = st.text_input("Cell address", value="A1")
            value = st.text_input("Value (start with = for an Excel formula)")
            submitted = st.form_submit_button("Write cell")
        if submitted:
            try:
                write_cell(path, cell.strip().upper(), value)
                st.success(f"Wrote {cell.upper()} successfully.")
                st.rerun()
            except Exception as e:
                st.error(str(e))
        c1, c2 = st.columns(2)
        if c1.button("Format header row"):
            try:
                format_header(path)
                st.success("Header formatted, filter enabled, and first row frozen.")
                st.rerun()
            except Exception as e: st.error(str(e))
        if c2.button("Highlight negative values"):
            try:
                highlight_negative(path)
                st.success("Conditional formatting added.")
                st.rerun()
            except Exception as e: st.error(str(e))
        st.markdown("**Create an embedded chart**")
        cc1, cc2, cc3 = st.columns(3)
        chart_kind = cc1.selectbox("Type", ["bar", "line", "pie"], key="embedded_kind")
        xname = cc2.selectbox("X column", list(df.columns), key="embedded_x")
        yname = cc3.selectbox("Y column", list(df.columns), index=min(1, len(df.columns)-1), key="embedded_y")
        if st.button("Add chart to workbook"):
            try:
                create_chart(path, chart_kind, str(xname), str(yname))
                st.success("Chart added at cell G2.")
            except Exception as e: st.error(str(e))
    else:
        st.info("CSV and TSV do not support Excel formatting, embedded charts, or multiple worksheets. Edit the table below and export it.")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        out_fmt = st.selectbox("Export format", ["xlsx", "csv", "tsv"])
        if st.button("Export edited table"):
            fd, out = tempfile.mkstemp(suffix="."+out_fmt, prefix="excel_agent_export_")
            os.close(fd)
            export_dataframe(edited, out)
            with open(out, "rb") as f:
                st.download_button("Download edited file", f.read(), file_name="edited."+out_fmt)

with tab_agent:
    st.subheader("Ask the Excel agent")
    st.caption("Optional local LLM via Ollama. If no model is available, use the quick actions below.")
    prompt = st.text_area("What would you like to do?", placeholder="e.g. Summarize the data and show the five largest values in Revenue", height=90)
    if st.button("Plan request", type="primary", disabled=not prompt.strip()):
        context = f"File: {st.session_state.original_name}\nSheet: {sheet}\nColumns: {list(df.columns)}\nSample:\n{df.head(8).to_string(index=False)}"
        try:
            st.session_state.pending_plan = {"request": prompt, "plan": plan_request(prompt, context)}
        except Exception as e:
            st.error(f"Could not contact Ollama: {e}. Start Ollama and pull a model, or use the quick actions below.")
    pending = st.session_state.pending_plan
    if pending:
        st.markdown("**Proposed plan — review before applying**")
        st.code(json.dumps(pending["plan"], indent=2, ensure_ascii=False), language="json")
        if pending["plan"].get("clarification"):
            st.info(pending["plan"]["clarification"])
        else:
            a, b = st.columns(2)
            if a.button("Apply plan", type="primary"):
                try:
                    outputs = []
                    allowed = {"summarize", "top_values", "write_cell", "format_header", "highlight_negative", "create_chart"}
                    for call in pending["plan"].get("calls", []):
                        tool = call.get("tool")
                        args = call.get("args", {})
                        if tool not in allowed:
                            raise ValueError(f"Tool not allowed: {tool}")
                        if tool == "summarize":
                            outputs.append(summarize(load_tabular(path, sheet if suffix in {".xlsx", ".xlsm"} else None)))
                        elif tool == "top_values":
                            outputs.append(top_values(load_tabular(path, sheet if suffix in {".xlsx", ".xlsm"} else None), args["column"], args.get("n", 5)).to_dict(orient="records"))
                        elif tool == "write_cell":
                            write_cell(path, args["cell"], args["value"]); outputs.append(f"Wrote {args['cell']}")
                        elif tool == "format_header":
                            format_header(path); outputs.append("Formatted header")
                        elif tool == "highlight_negative":
                            highlight_negative(path, args.get("cell_range")); outputs.append("Added negative-value formatting")
                        elif tool == "create_chart":
                            create_chart(path, args.get("kind", "bar"), args.get("x_column"), args.get("y_column")); outputs.append("Created chart")
                    st.success("Plan applied.")
                    st.json(outputs)
                    st.session_state.pending_plan = None
                    st.rerun()
                except Exception as e: st.error(f"Plan failed: {e}")
            if b.button("Discard plan"):
                st.session_state.pending_plan = None
                st.rerun()
    st.divider()
    st.markdown("**Quick actions (no LLM required)**")
    if st.button("Summarize active sheet"):
        st.json(summarize(df))
    if len(df.columns):
        col = st.selectbox("Column for top values", list(df.columns), key="quick_top_col")
        n = st.slider("Number of rows", 1, 20, 5, key="quick_top_n")
        if st.button("Show top values"):
            try: st.dataframe(top_values(df, col, n), use_container_width=True)
            except Exception as e: st.error(str(e))

st.divider()
if suffix in {".xlsx", ".xlsm"}:
    mime = "application/vnd.ms-excel.sheet.macroEnabled.12" if suffix == ".xlsm" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
elif suffix == ".tsv":
    mime = "text/tab-separated-values"
else:
    mime = "text/csv"
with open(path, "rb") as f:
    current_bytes = f.read()
st.download_button("⬇ Download modified workbook", current_bytes, file_name="edited_"+(st.session_state.original_name or "workbook"), mime=mime, type="primary")
