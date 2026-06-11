from __future__ import annotations

import warnings
import subprocess
from pathlib import Path
from typing import Annotated, Literal

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import typer
from rich.console import Console
from rich.table import Table


app = typer.Typer(
    help="Inspect, clean, summarize, and plot CSV files from the command line.",
    no_args_is_help=True,
)
console = Console()

PlotKind = Literal["scatter", "line", "bar", "hist"]
FillStrategy = Literal["mean", "median", "mode", "zero", "unknown"]


def main() -> None:
    app()


def load_csv(csv_file: Path) -> pd.DataFrame:
    if not csv_file.exists():
        raise typer.BadParameter(f"File does not exist: {csv_file}")
    if not csv_file.is_file():
        raise typer.BadParameter(f"Path is not a file: {csv_file}")

    try:
        return pd.read_csv(csv_file)
    except pd.errors.EmptyDataError as exc:
        raise typer.BadParameter("CSV file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise typer.BadParameter(f"Could not parse CSV file: {exc}") from exc


def require_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        choices = ", ".join(str(col) for col in df.columns)
        raise typer.BadParameter(f"Column '{column}' was not found. Available columns: {choices}")


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    require_column(df, column)
    series = pd.to_numeric(df[column], errors="coerce")
    if series.dropna().empty:
        raise typer.BadParameter(f"Column '{column}' does not contain numeric values.")
    return series


def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    non_missing = series.dropna()
    if non_missing.empty:
        return "empty"

    numeric = pd.to_numeric(non_missing, errors="coerce")
    numeric_ratio = numeric.notna().mean()
    if numeric_ratio >= 0.9:
        return "numeric-like"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed_dates = pd.to_datetime(non_missing, errors="coerce")
    date_ratio = parsed_dates.notna().mean()
    if date_ratio >= 0.9:
        return "date-like"

    unique_ratio = non_missing.nunique() / len(non_missing)
    if unique_ratio <= 0.2 or non_missing.nunique() <= 20:
        return "categorical"

    return "text"


def format_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


@app.command()
def profile(
    csv_file: Annotated[Path, typer.Argument(help="Path to the CSV file to inspect.")],
    sample_rows: Annotated[int, typer.Option(help="Number of sample rows to display.")] = 5,
) -> None:
    """Show dataset shape, columns, missing values, duplicates, and inferred types."""
    df = load_csv(csv_file)

    console.print(f"[bold]File:[/bold] {csv_file}")
    console.print(f"[bold]Rows:[/bold] {len(df):,}")
    console.print(f"[bold]Columns:[/bold] {len(df.columns):,}")
    console.print(f"[bold]Duplicate rows:[/bold] {df.duplicated().sum():,}")

    table = Table(title="Column Profile")
    table.add_column("Column")
    table.add_column("Inferred Type")
    table.add_column("Pandas Type")
    table.add_column("Missing")
    table.add_column("Unique")
    table.add_column("Example")

    for column in df.columns:
        series = df[column]
        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))
        example = series.dropna().iloc[0] if not series.dropna().empty else ""
        table.add_row(
            str(column),
            infer_column_type(series),
            str(series.dtype),
            f"{missing:,}",
            f"{unique:,}",
            format_value(example),
        )

    console.print(table)

    warnings: list[str] = []
    empty_columns = [str(col) for col in df.columns if df[col].isna().all()]
    if empty_columns:
        warnings.append(f"Completely empty columns: {', '.join(empty_columns)}")

    columns_with_missing = [str(col) for col in df.columns if df[col].isna().any()]
    if columns_with_missing:
        warnings.append(f"Columns with missing values: {', '.join(columns_with_missing)}")

    unnamed_columns = [str(col) for col in df.columns if str(col).lower().startswith("unnamed")]
    if unnamed_columns:
        warnings.append(f"Possible accidental index columns: {', '.join(unnamed_columns)}")

    duplicate_columns = df.columns[df.columns.duplicated()].tolist()
    if duplicate_columns:
        warnings.append(f"Duplicate column names: {', '.join(str(col) for col in duplicate_columns)}")

    if warnings:
        console.print("[bold yellow]Warnings[/bold yellow]")
        for warning in warnings:
            console.print(f"- {warning}")

    if sample_rows > 0:
        console.print(f"[bold]First {sample_rows} rows[/bold]")
        console.print(df.head(sample_rows).to_string(index=False))


@app.command()
def stats(
    csv_file: Annotated[Path, typer.Argument(help="Path to the CSV file to summarize.")],
    column: Annotated[str | None, typer.Option(help="Column to summarize.")] = None,
    all_columns: Annotated[bool, typer.Option("--all-columns", help="Summarize every column.")] = False,
) -> None:
    """Compute summary statistics for one column or for every column."""
    df = load_csv(csv_file)

    if column is None and not all_columns:
        raise typer.BadParameter("Provide --column COLUMN or use --all-columns.")
    if column is not None and all_columns:
        raise typer.BadParameter("Use either --column or --all-columns, not both.")

    columns = list(df.columns) if all_columns else [column]
    assert columns is not None

    for selected_column in columns:
        assert selected_column is not None
        require_column(df, selected_column)
        series = df[selected_column]
        inferred_type = infer_column_type(series)

        console.print(f"\n[bold]{selected_column}[/bold] ({inferred_type})")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Metric")
        table.add_column("Value")

        table.add_row("count", f"{series.notna().sum():,}")
        table.add_row("missing", f"{series.isna().sum():,}")
        table.add_row("unique", f"{series.nunique(dropna=True):,}")

        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            table.add_row("mean", format_value(numeric.mean()))
            table.add_row("median", format_value(numeric.median()))
            table.add_row("std", format_value(numeric.std()))
            table.add_row("min", format_value(numeric.min()))
            table.add_row("25%", format_value(numeric.quantile(0.25)))
            table.add_row("75%", format_value(numeric.quantile(0.75)))
            table.add_row("max", format_value(numeric.max()))
        else:
            mode = series.mode(dropna=True)
            table.add_row("most common", format_value(mode.iloc[0]) if not mode.empty else "")

        console.print(table)

        if not numeric.notna().any():
            counts = series.value_counts(dropna=False).head(10)
            if not counts.empty:
                top_table = Table(title=f"Top values for {selected_column}")
                top_table.add_column("Value")
                top_table.add_column("Count")
                for value, count in counts.items():
                    top_table.add_row(format_value(value), f"{count:,}")
                console.print(top_table)


@app.command()
def clean(
    csv_file: Annotated[Path, typer.Argument(help="Path to the CSV file to clean.")],
    output: Annotated[Path, typer.Option(help="Where to write the cleaned CSV file.")],
    fill_missing: Annotated[
        FillStrategy | None,
        typer.Option(help="Fill missing values using mean, median, mode, zero, or unknown."),
    ] = None,
    drop_missing: Annotated[bool, typer.Option(help="Drop rows that contain missing values.")] = False,
    drop_duplicates: Annotated[bool, typer.Option(help="Drop duplicate rows.")] = False,
    strip_text: Annotated[bool, typer.Option(help="Strip whitespace from text columns.")] = True,
) -> None:
    """Clean a CSV and write the result to a new file."""
    if fill_missing and drop_missing:
        raise typer.BadParameter("Use either --fill-missing or --drop-missing, not both.")

    df = load_csv(csv_file)
    cleaned = df.copy()
    original_shape = cleaned.shape

    if strip_text:
        text_columns = cleaned.select_dtypes(include=["object", "string"]).columns
        for col in text_columns:
            cleaned[col] = cleaned[col].map(lambda value: value.strip() if isinstance(value, str) else value)

    if drop_duplicates:
        cleaned = cleaned.drop_duplicates()

    if drop_missing:
        cleaned = cleaned.dropna()

    if fill_missing:
        for col in cleaned.columns:
            if not cleaned[col].isna().any():
                continue

            numeric = pd.to_numeric(cleaned[col], errors="coerce")
            is_numeric_like = numeric.notna().sum() > 0 and numeric.notna().mean() >= 0.8

            if fill_missing == "mean":
                if is_numeric_like:
                    cleaned[col] = numeric.fillna(numeric.mean())
                else:
                    cleaned[col] = cleaned[col].fillna(most_common_value(cleaned[col], "unknown"))
            elif fill_missing == "median":
                if is_numeric_like:
                    cleaned[col] = numeric.fillna(numeric.median())
                else:
                    cleaned[col] = cleaned[col].fillna(most_common_value(cleaned[col], "unknown"))
            elif fill_missing == "mode":
                cleaned[col] = cleaned[col].fillna(most_common_value(cleaned[col], "unknown"))
            elif fill_missing == "zero":
                cleaned[col] = cleaned[col].fillna(0 if is_numeric_like else "0")
            elif fill_missing == "unknown":
                cleaned[col] = cleaned[col].fillna("unknown")

    output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output, index=False)

    console.print(f"[bold]Wrote cleaned CSV:[/bold] {output}")
    console.print(f"Original shape: {original_shape[0]:,} rows x {original_shape[1]:,} columns")
    console.print(f"Cleaned shape: {cleaned.shape[0]:,} rows x {cleaned.shape[1]:,} columns")


def most_common_value(series: pd.Series, fallback: object) -> object:
    mode = series.mode(dropna=True)
    if mode.empty:
        return fallback
    return mode.iloc[0]


@app.command()
def plot(
    csv_file: Annotated[Path, typer.Argument(help="Path to the CSV file to plot.")],
    kind: Annotated[PlotKind, typer.Option(help="Plot type: scatter, line, bar, or hist.")],
    x: Annotated[str, typer.Option(help="Column for the x-axis, histogram values, or bar categories.")],
    output: Annotated[Path, typer.Option(help="Where to save the generated plot image.")],
    y: Annotated[str | None, typer.Option(help="Column for the y-axis. Required for scatter, line, and bar.")] = None,
    title: Annotated[str | None, typer.Option(help="Optional chart title.")] = None,
    bins: Annotated[int, typer.Option(help="Number of histogram bins.")] = 20,
) -> None:
    """Create a scatter, line, bar, or histogram plot from CSV columns."""
    df = load_csv(csv_file)
    require_column(df, x)

    plt.figure(figsize=(9, 5.5))

    if kind == "hist":
        values = numeric_series(df, x).dropna()
        plt.hist(values, bins=bins, edgecolor="black")
        plt.xlabel(x)
        plt.ylabel("Count")
    else:
        if y is None:
            raise typer.BadParameter(f"--y is required for {kind} plots.")
        require_column(df, y)

        if kind == "scatter":
            x_values = numeric_series(df, x)
            y_values = numeric_series(df, y)
            plot_df = pd.DataFrame({x: x_values, y: y_values}).dropna()
            plt.scatter(plot_df[x], plot_df[y], alpha=0.75)
            plt.xlabel(x)
            plt.ylabel(y)
        elif kind == "line":
            plot_df = df[[x, y]].dropna().sort_values(by=x)
            plt.plot(plot_df[x], plot_df[y])
            plt.xlabel(x)
            plt.ylabel(y)
        elif kind == "bar":
            grouped = df.groupby(x, dropna=False)[y].mean(numeric_only=True).sort_values(ascending=False)
            if grouped.empty:
                raise typer.BadParameter(f"Could not compute numeric bar heights from '{y}'.")
            grouped.plot(kind="bar")
            plt.xlabel(x)
            plt.ylabel(f"Average {y}")

    plt.title(title or default_title(kind, x, y))
    plt.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=150)

    
    subprocess.run(["open", str(output)])

    plt.close()

    console.print(f"[bold]Wrote plot:[/bold] {output}")


def default_title(kind: str, x: str, y: str | None) -> str:
    if kind == "hist":
        return f"Distribution of {x}"
    if y is None:
        return kind.title()
    return f"{y} by {x}"


if __name__ == "__main__":
    main()
