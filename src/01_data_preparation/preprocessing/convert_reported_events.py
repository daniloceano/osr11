#!/usr/bin/env python3
"""
Convert reported events Excel file to CSV format.

This script reads the reported_events_Karine_sc.xlsx file and converts it to CSV
for easier manipulation and version control.
"""

import logging
from pathlib import Path
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_excel_to_csv(
    excel_path: Path,
    csv_path: Path,
    sheet_name: int | str = 0,
    skiprows: int = 1
) -> None:
    """
    Convert Excel file to CSV format.
    
    Parameters
    ----------
    excel_path : Path
        Path to input Excel file
    csv_path : Path
        Path to output CSV file
    sheet_name : int or str, optional
        Sheet name or index to read (default: 0 - first sheet)
    skiprows : int, optional
        Number of rows to skip at the beginning (default: 1, to skip table description)
    """
    logger.info(f"Reading Excel file: {excel_path}")
    
    # Read Excel file, skipping description row
    df = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=skiprows)
    
    logger.info(f"Excel file loaded. Shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Basic cleaning: strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Create output directory if needed
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    logger.info(f"Saving CSV file: {csv_path}")
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    logger.info(f"Conversion completed. CSV saved with {len(df)} rows and {len(df.columns)} columns.")


def main():
    """Main execution function."""
    # Define paths
    repo_root = Path(__file__).resolve().parents[2]
    excel_path = repo_root / "data" / "reported events" / "reported_events_Karine_sc.xlsx"
    csv_path = repo_root / "data" / "reported events" / "reported_events_Karine_sc.csv"
    
    # Check if Excel file exists
    if not excel_path.exists():
        logger.error(f"Excel file not found: {excel_path}")
        raise FileNotFoundError(f"Excel file not found: {excel_path}")
    
    # Convert
    convert_excel_to_csv(excel_path, csv_path)
    
    logger.info("Done!")


if __name__ == "__main__":
    main()
