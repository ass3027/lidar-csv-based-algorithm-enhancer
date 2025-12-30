#!/usr/bin/env python3
"""
Data loader for table generation, using the core data loader and outlier filtering.
"""

from src.new.core.data_loader import load_all_logs, filter_outliers

def load_and_process_data(data_dir="csv", format_hint=None, from_date=None, to_date=None):
    """
    Loads and processes log data from a given directory using the core data loader.

    This function acts as a wrapper around the core data loading and filtering
    functionality, providing a simple interface for table generation scripts.

    Args:
        data_dir (str): The directory where the log files are stored.
                        Defaults to "csv".
        format_hint (str, optional): A hint to force the format detection ('old' or 'new').
                                     Defaults to None for auto-detection.
        from_date (str, optional): Start date filter in YYYYMMDD format (inclusive).
        to_date (str, optional): End date filter in YYYYMMDD format (inclusive).

    Returns:
        tuple: (filtered_data, outlier_stats) where filtered_data is a list of cleaned records
               and outlier_stats is a dictionary containing outlier detection statistics
    """
    print(f"--- Loading and processing data from '{data_dir}' ---")

    # Load all log files using the core data loader
    raw_data = load_all_logs(log_dir=data_dir, format_hint=format_hint, from_date=from_date, to_date=to_date)

    if not raw_data:
        print("Warning: No data was loaded. Please check the log directory and file formats.")
        return [], {}

    # Filter outliers using the core outlier detection function
    filtered_data, outlier_stats = filter_outliers(raw_data)

    if not filtered_data:
        print("Warning: All data was filtered out as outliers.")
        return [], outlier_stats

    print(f"--- Data loading and processing complete. {len(filtered_data)} records ready for analysis. ---")

    return filtered_data, outlier_stats