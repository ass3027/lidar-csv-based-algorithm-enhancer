#!/usr/bin/env python3
"""
Data loader for table generation, using the core data loader and outlier filtering.
"""

from new.core.data_loader import load_all_logs, filter_outliers

def load_and_process_data(data_dir="csv", format_hint=None):
    """
    Loads and processes log data from a given directory using the core data loader.

    This function acts as a wrapper around the core data loading and filtering
    functionality, providing a simple interface for table generation scripts.

    Args:
        data_dir (str): The directory where the log files are stored.
                        Defaults to "csv".
        format_hint (str, optional): A hint to force the format detection ('old' or 'new').
                                     Defaults to None for auto-detection.

    Returns:
        list: A list of dictionaries, where each dictionary represents a
              cleaned and processed log record.
    """
    print(f"--- Loading and processing data from '{data_dir}' ---")

    # Load all log files using the core data loader
    raw_data = load_all_logs(log_dir=data_dir, format_hint=format_hint)

    if not raw_data:
        print("Warning: No data was loaded. Please check the log directory and file formats.")
        return []

    # Filter outliers using the core outlier detection function
    filtered_data, _ = filter_outliers(raw_data)

    if not filtered_data:
        print("Warning: All data was filtered out as outliers.")
        return []

    print(f"--- Data loading and processing complete. {len(filtered_data)} records ready for analysis. ---")

    return filtered_data