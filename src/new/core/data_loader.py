#!/usr/bin/env python3
"""CSV loading module supporting both old and new formats"""

import csv
from pathlib import Path
from datetime import datetime, timedelta
from ..utils.outlier_detection import detect_outliers_iqr


def _parse_time_to_seconds(time_str):
    """
    Parse time string to seconds

    Formats supported:
    - MM:SS (e.g., "00:06")     -> 6 seconds
    - HH:MM:SS (e.g., "01:23:45") -> 5025 seconds
    - M:SS (e.g., "1:30")       -> 90 seconds

    Args:
        time_str: Time string in various formats

    Returns:
        int: Time in seconds
    """
    parts = time_str.strip().split(':')

    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    else:
        return 0


def _parse_old_format_row(row, date_str):
    """
    Parse old CSV format and adapt to the new format structure.

    Old Format: timestamp,zone_id,objectCount,lidarEstTime,throughputEstTime,finalEstTime,actualPassTime
    New Structure: timestamp,zone_id,objectCount,inTime,outTime,actualPassTime,lidarEstTime,throughputEstTime,finalEstTime
    """
    # Basic data extraction and type conversion
    actual_pass_time_seconds = int(row['actualPassTime'])
    timestamp_str = row['timestamp']
    
    # Create datetime object from timestamp
    try:
        timestamp_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None  # Skip row if timestamp is malformed

    # Calculate inTime and outTime
    out_time_dt = timestamp_dt
    in_time_dt = out_time_dt - timedelta(seconds=actual_pass_time_seconds)

    return {
        'timestamp': timestamp_str,
        'object_id': None,  # Old format does not have object_id
        'zone_id': int(row['zone_id']),
        'objectCount': int(row['objectCount']),
        'inTime': in_time_dt.strftime('%H:%M:%S'),
        'outTime': out_time_dt.strftime('%H:%M:%S'),
        'actualPassTime': actual_pass_time_seconds,
        'lidarEstTime': float(row['lidarEstTime']),
        'throughputEstTime': float(row['throughputEstTime']),
        'finalEstTime': float(row['finalEstTime']),
        'actualPassTime_str': f"{actual_pass_time_seconds // 60:02d}:{actual_pass_time_seconds % 60:02d}",
        'date': date_str
    }


def _parse_new_format_row(row_values, date_str):
    """
    Parse new CSV format (no header, 10 columns)

    Header: timestamp,objectId,zoneId,zoneObjectCount,inTime,outTime,actualPassTime,lidarEstTime,throughputEstTime,finalEstTime

    Columns:
    0. timestamp         - Event timestamp (YYYY-MM-DD HH:MM:SS)
    1. objectId          - Object/Person identifier
    2. zoneId            - Zone identifier
    3. zoneObjectCount   - Number of objects in zone
    4. inTime            - Entry time (HH:MM:SS)
    5. outTime           - Exit time (HH:MM:SS)
    6. actualPassTime    - Duration in MM:SS or HH:MM:SS format
    7. lidarEstTime      - LiDAR estimate (seconds)
    8. throughputEstTime - Throughput estimate (decimal)
    9. finalEstTime      - Final estimate (seconds)

    Args:
        row_values: List of string values from CSV row
        date_str: Date extracted from filename (YYYYMMDD)

    Returns:
        dict: Parsed row with standardized field names
    """
    timestamp = row_values[0]
    object_id = int(row_values[1])
    zone_id = int(row_values[2])
    zone_object_count = int(row_values[3])

    in_time = row_values[4] if len(row_values) > 4 else None
    out_time = row_values[5] if len(row_values) > 5 else None
    actual_pass_time_str = row_values[6] if len(row_values) > 6 else "00:00"

    lidar_est_time = float(row_values[7]) if len(row_values) > 7 else 0.0
    throughput_est_time = float(row_values[8]) if len(row_values) > 8 else 0.0
    final_est_time = float(row_values[9]) if len(row_values) > 9 else 0.0

    actual_pass_time_seconds = _parse_time_to_seconds(actual_pass_time_str)

    return {
        'timestamp': timestamp,
        'object_id': object_id,
        'zone_id': zone_id,
        'objectCount': zone_object_count,
        'inTime': in_time,
        'outTime': out_time,
        'actualPassTime': actual_pass_time_seconds,
        'lidarEstTime': lidar_est_time,
        'throughputEstTime': throughput_est_time,
        'finalEstTime': final_est_time,
        'actualPassTime_str': actual_pass_time_str
    }


def load_all_logs(log_dir="../csv", format_hint=None, from_date=None, to_date=None):
    """
    Load all queue log CSV files from directory

    Automatically detects and handles both old and new CSV formats.

    Args:
        log_dir: Directory containing CSV files (default: 'csv')
        format_hint: Force format detection ('old' or 'new'), None for auto-detect
        from_date: Optional start date filter in YYYYMMDD format (inclusive)
        to_date: Optional end date filter in YYYYMMDD format (inclusive)

    Returns:
        list: Parsed log records with standardized fields
    """
    log_path = Path(log_dir)
    all_data = []

    if not log_path.exists():
        print(f"Warning: Directory '{log_dir}' not found.")
        return all_data

    csv_files = sorted(log_path.glob("passingObject_*.csv"))

    if not csv_files:
        print(f"Warning: No CSV files found in '{log_dir}' directory.")
        return all_data

    # Filter CSV files by date range if specified
    if from_date or to_date:
        filtered_files = []
        for csv_file in csv_files:
            date_str = csv_file.stem.replace('passingObject_', '')
            if from_date and date_str < from_date:
                continue
            if to_date and date_str > to_date:
                continue
            filtered_files.append(csv_file)
        csv_files = filtered_files
        print(f"Date filter applied: {len(csv_files)} files selected (from: {from_date or 'any'}, to: {to_date or 'any'})")

        if not csv_files:
            print(f"Warning: No CSV files match the date range filter.")
            return all_data

    for csv_file in csv_files:
        print(f"Loading: {csv_file.name}...")
        date_str = csv_file.stem.replace('passingObject_', '')

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            first_row = next(reader, None)

            if first_row is None:
                continue

            if format_hint:
                detected_format = format_hint
            else:
                if first_row[0] == 'timestamp':
                    detected_format = 'old'
                else:
                    detected_format = 'new'

            if detected_format == 'old':
                f.seek(0)
                reader_dict = csv.DictReader(f)
                for row in reader_dict:
                    try:
                        parsed_row = _parse_old_format_row(row, date_str)
                        if parsed_row:
                            all_data.append(parsed_row)
                    except (ValueError, KeyError):
                        continue
            else:
                if first_row[0] == 'timestamp':
                    first_row = next(reader, None)

                if first_row:
                    try:
                        parsed_row = _parse_new_format_row(first_row, date_str)
                        parsed_row['date'] = date_str
                        all_data.append(parsed_row)
                    except (ValueError, IndexError):
                        pass

                for row in reader:
                    try:
                        parsed_row = _parse_new_format_row(row, date_str)
                        parsed_row['date'] = date_str
                        all_data.append(parsed_row)
                    except (ValueError, IndexError):
                        continue

    print(f"Loaded a total of {len(all_data):,} records.")
    return all_data


def filter_outliers(data):
    """
    Remove outliers using IQR method across 4 metrics

    Args:
        data: List of parsed log records

    Returns:
        tuple: (filtered_data, outlier_stats)
    """
    print("\nDetecting outliers...")

    error_extractors = {
        'actual_time': lambda r: r['actualPassTime'],
        'lidar_error': lambda r: r['lidarEstTime'] - r['actualPassTime'],
        'throughput_error': lambda r: r['throughputEstTime'] - r['actualPassTime'],
        'final_error': lambda r: r['finalEstTime'] - r['actualPassTime']
    }

    outlier_sets = {
        name: detect_outliers_iqr([extractor(row) for row in data])
        for name, extractor in error_extractors.items()
    }

    all_outlier_indices = set().union(*outlier_sets.values())

    filtered_data = [
        row for i, row in enumerate(data)
        if i not in all_outlier_indices
    ]

    total_count = len(data)
    removed_count = len(all_outlier_indices)
    removal_rate = (removed_count / total_count) * 100 if total_count > 0 else 0

    outlier_stats = {
        'total_records': total_count,
        'removed_records': removed_count,
        'filtered_records': len(filtered_data),
        'removal_rate_pct': removal_rate,
        'outliers_by_type': {name: len(indices) for name, indices in outlier_sets.items()}
    }

    print(f"  Total records: {total_count:,}")
    print(f"  Removed records: {removed_count:,} ({removal_rate:.1f}%)")
    print(f"  Records after filtering: {len(filtered_data):,}")

    return filtered_data, outlier_stats
