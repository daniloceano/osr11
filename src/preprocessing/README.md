# src/preprocessing/

Data preprocessing scripts for converting raw data files to analysis-ready formats.

## Scripts

### `convert_reported_events.py`

Converts the Excel file `reported_events_Karine_sc.xlsx` to CSV format.

**Usage:**

```bash
python src/preprocessing/convert_reported_events.py
```

**What it does:**

1. Reads the Excel file from `data/reported events/`
2. Skips the first row (table caption)
3. Strips whitespace from column names
4. Saves as UTF-8 CSV to the same directory

**Output:** `data/reported events/reported_events_Karine_sc.csv`

**Why CSV?**

- Faster to read (no Excel parsing overhead)
- Better for version control (text-based diffs)
- No external dependencies on Excel libraries for routine analysis
- Easier manipulation in most data science workflows

## When to run

Re-run the conversion script if:
- The original Excel file is updated
- You need to regenerate the CSV from source

The CSV file is tracked in git and should be kept in sync with the Excel source.
