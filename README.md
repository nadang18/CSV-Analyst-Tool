# CSV Tool

CSV Tool is a Python command-line tool for quickly inspecting, cleaning, summarizing, and plotting CSV files. It is designed for fast CSV exploration directly from the terminal before doing deeper analysis in a script, notebook, or project.

## Setup

Clone this repository to your local machine:

```bash
git clone https://github.com/nadang18/CSV-Analyst-Tool.git
cd CSV-Analyst-Tool
```

This project uses `uv` to manage dependencies. Make sure `uv` is installed, then install the project dependencies:

```bash
uv sync
```

Check that the command-line tool is working:

```bash
uv run csv-tool --help
```

## Example Data

This repository includes example CSV files in the `data/` folder. These files can be used directly with the CLI commands below.

Common example files include:

```text
data/tips.csv
data/penguins.csv
data/gapminder.csv
```

## Usage

### Inspect a CSV file

```bash
uv run csv-tool profile data/penguins.csv
```

This shows basic information about the CSV file, including rows, columns, missing values, duplicate rows, inferred column types, and sample rows.

### Show statistics for one column

```bash
uv run csv-tool stats data/tips.csv --column total_bill
```

### Show statistics for every column

```bash
uv run csv-tool stats data/tips.csv --all-columns
```

## Cleaning CSV Files

The `clean` command creates a cleaned CSV file and saves it to the path provided with `--output`.

### Fill missing values

```bash
uv run csv-tool clean data/penguins.csv --fill-missing median --output data/penguins_clean.csv
```

### Drop rows with missing values

```bash
uv run csv-tool clean data/penguins.csv --drop-missing --output data/penguins_no_missing.csv
```

The original CSV file is not changed unless the same file path is used for `--output`.

For example, this creates a new cleaned file:

```bash
uv run csv-tool clean data/penguins.csv --fill-missing median --output data/penguins_clean.csv
```

This would overwrite the original file:

```bash
uv run csv-tool clean data/penguins.csv --fill-missing median --output data/penguins.csv
```

## Creating Plots

The `plot` command creates a plot image and saves it to the path provided with `--output`.

Generated plots are saved locally. If the output folder does not exist, the tool creates it automatically.

### Create a scatter plot

```bash
uv run csv-tool plot data/tips.csv --kind scatter --x total_bill --y tip --output plots/tips_scatter.png
```

### Create a histogram

```bash
uv run csv-tool plot data/penguins.csv --kind hist --x bill_length_mm --output plots/bill_length_hist.png
```

### Create a bar chart

```bash
uv run csv-tool plot data/tips.csv --kind bar --x day --y total_bill --output plots/day_total_bill.png
```

### Create a line chart

```bash
uv run csv-tool plot data/gapminder.csv --kind line --x year --y lifeExp --output plots/life_expectancy.png
```

## Local Output Files

This tool runs locally on your machine.

Generated files, such as cleaned CSV files and plot images, are saved locally to the paths provided with `--output`.

Running the CLI does not automatically update GitHub. To share generated files, you would need to manually add, commit, and push them.
