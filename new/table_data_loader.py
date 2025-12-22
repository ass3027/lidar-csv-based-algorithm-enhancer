#!/usr/bin/env python3
"""테이블 데이터 로더 모듈 - Data loader with built-in outlier filtering"""

import csv
import glob
from datetime import datetime


def load_and_process_data(data_dir="passing_log"):
    csv_files = glob.glob(f'{data_dir}/*.csv')
    raw_data = []

    if not csv_files:
        print(f"경고: '{data_dir}' 디렉토리에 CSV 파일이 없습니다.")
        return raw_data

    for file_path in csv_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    parsed_row = {
                        'timestamp': datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'),
                        'zone_id': int(row['zone_id']),
                        'objectCount': int(row['objectCount']),
                        'finalEstTime': float(row['finalEstTime']),
                        'actualPassTime': float(row['actualPassTime'])
                    }
                    raw_data.append(parsed_row)
                except (ValueError, KeyError):
                    continue

    clean_data = _filter_outliers_by_iqr(raw_data)
    return clean_data


def _filter_outliers_by_iqr(data):
    if not data:
        return data

    prediction_errors = [abs(row['finalEstTime'] - row['actualPassTime']) for row in data]
    sorted_errors = sorted(prediction_errors)
    n = len(sorted_errors)

    q1_index = n // 4
    q3_index = 3 * n // 4
    q1 = sorted_errors[q1_index]
    q3 = sorted_errors[q3_index]
    iqr = q3 - q1

    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    max_acceptable_time = 7200

    clean_data = []
    for i, row in enumerate(data):
        error = prediction_errors[i]
        is_error_outlier = error < lower_fence or error > upper_fence
        is_time_extreme = row['actualPassTime'] > max_acceptable_time or row['finalEstTime'] > max_acceptable_time

        if not is_error_outlier and not is_time_extreme:
            clean_data.append(row)

    return clean_data
