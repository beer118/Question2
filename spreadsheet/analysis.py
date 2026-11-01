import pandas as pd

def summarize(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [str(c) for c in df.columns],
        "missing_by_column": {str(k): int(v) for k, v in df.isna().sum().items()},
        "numeric_summary": df.describe(include="number").round(3).to_dict(),
    }

def top_values(df: pd.DataFrame, column: str, n: int = 5) -> pd.DataFrame:
    if column not in df.columns:
        raise ValueError(f"Unknown column '{column}'. Available: {list(df.columns)}")
    if not pd.api.types.is_numeric_dtype(df[column]):
        df = df.copy()
        df[column] = pd.to_numeric(df[column], errors="coerce")
    n = max(1, min(int(n), 100))
    return df.nlargest(n, column)
