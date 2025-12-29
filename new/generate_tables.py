#!/usr/bin/env python3
"""
Main entry point for summary table generation

Usage:
    python new/generate_tables.py [data_dir]

Example:
    python new/generate_tables.py csv

Output:
    Saves to result/대기시간_통계분석_YYYYMMDD_YYYYMMDD.md
    Date range is extracted from CSV filenames in the data directory
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))



from new.tables.table_data_loader import load_and_process_data

from new.tables.table_generators import (
    generate_zone_by_day_table,
    generate_zone_by_queue_table,
    generate_zone_by_congestion_table,
    generate_queue_by_day_table,
    generate_sample_count_table,
    generate_summary_statistics_table,
)



def extract_date_range_from_csv_dir(data_dir):
    """Extract the date range (from-to) from CSV filenames in directory"""
    csv_files = list(Path(data_dir).glob("passingObject_*.csv"))
    if not csv_files:
        today = datetime.now().strftime('%Y%m%d')
        return today, today

    # Extract dates from filenames (format: passingObject_YYYYMMDD.csv)
    dates = []
    for csv_file in csv_files:
        try:
            date_str = csv_file.stem.split('_')[1]  # Get YYYYMMDD part
            dates.append(date_str)
        except (IndexError, ValueError):
            continue

    if not dates:
        today = datetime.now().strftime('%Y%m%d')
        return today, today

    return min(dates), max(dates)


def main(data_dir):
    """
    Main pipeline for generating summary tables.

    Args:
        data_dir: Directory containing CSV files
    """
    print("--- Summary Table Generation Pipeline ---")

    # Load and process data
    print(f"Loading data from '{data_dir}'...")
    data = load_and_process_data(data_dir)

    if not data:
        print("No data loaded. Exiting.")
        return

    print(f"Loaded and filtered {len(data)} records.")

    # Generate all tables
    print("Generating tables...")
    zone_by_day_table = generate_zone_by_day_table(data)
    zone_by_queue_table = generate_zone_by_queue_table(data)
    zone_by_congestion_table = generate_zone_by_congestion_table(data)
    queue_by_day_table = generate_queue_by_day_table(data)
    sample_count_table = generate_sample_count_table(data)
    summary_stats_table = generate_summary_statistics_table(data)

    # Combine tables into a single document
    full_report = (
        f"{zone_by_day_table}\n\n"
        f"{zone_by_queue_table}\n\n"
        f"{zone_by_congestion_table}\n\n"
        f"{queue_by_day_table}\n\n"
        f"{sample_count_table}\n\n"
        f"{summary_stats_table}"
    )

    # Extract date range from CSV filenames
    from_date, to_date = extract_date_range_from_csv_dir(data_dir)

    # Create result directory if it doesn't exist
    result_dir = project_root / "result"
    result_dir.mkdir(exist_ok=True)

    # Generate output filename with date range
    output_filename = f"대기시간_통계분석_{from_date}_{to_date}.md"
    output_path = result_dir / output_filename

    # Save to output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"Successfully generated summary tables in '{output_path}'")



if __name__ == '__main__':
    project_root = Path(__file__).parent.parent

    # Use command-line arguments if provided, otherwise use defaults relative to project root
    data_dir_arg = sys.argv[1] if len(sys.argv) > 1 else "csv"

    # Resolve paths
    _data_dir = project_root / data_dir_arg

    main(_data_dir)
