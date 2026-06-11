# CSV Tool

CSV Tool is a Python command-line tool for quickly inspecting, cleaning, summarizing, and plotting CSV files. It is useful when you want to understand a dataset before opening a notebook or writing custom analysis code.

## Usage

Install dependencies and run the tool from the project folder:

```bash
uv sync
uv run csv-tool --help
```

Download a few example datasets:

```bash
mkdir -p data plots
curl -L -o data/tips.csv https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv
curl -L -o data/penguins.csv https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv
curl -L -o data/gapminder.csv https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv
```

Inspect a CSV file:

```bash
uv run csv-tool profile data/penguins.csv
```

Show statistics for one column:

```bash
uv run csv-tool stats data/tips.csv --column total_bill
```

Show statistics for every column:

```bash
uv run csv-tool stats data/tips.csv --all-columns
```

Clean a CSV file by filling missing values:

```bash
uv run csv-tool clean data/penguins.csv --fill-missing median --output data/penguins_clean.csv
```

Drop rows with missing values:

```bash
uv run csv-tool clean data/penguins.csv --drop-missing --output data/penguins_no_missing.csv
```

Create a scatter plot:

```bash
uv run csv-tool plot data/tips.csv --kind scatter --x total_bill --y tip --output plots/tips_scatter.png
```

Create a histogram:

```bash
uv run csv-tool plot data/penguins.csv --kind hist --x bill_length_mm --output plots/bill_length_hist.png
```

Create a bar chart:

```bash
uv run csv-tool plot data/tips.csv --kind bar --x day --y total_bill --output plots/day_total_bill.png
```

Create a line chart:

```bash
uv run csv-tool plot data/gapminder.csv --kind line --x year --y lifeExp --output plots/life_expectancy.png
```
