#!/usr/bin/env python3
"""데이터 로딩 모듈 - CSV loading module for queue logs"""

import csv
from pathlib import Path


def load_all_logs(log_dir="passing_log"):
    log_path = Path(log_dir)
    all_data = []

    if not log_path.exists():
        print(f"경고: 디렉토리 '{log_dir}'를 찾을 수 없습니다.")
        return all_data

    csv_files = sorted(log_path.glob("passingObject_*.csv"))

    if not csv_files:
        print(f"경고: '{log_dir}' 디렉토리에 CSV 파일이 없습니다.")
        return all_data

    for csv_file in csv_files:
        print(f"로딩중: {csv_file.name}...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    parsed_row = {
                        'timestamp': row['timestamp'],
                        'date': csv_file.stem.replace('passingObject_', ''),
                        'zone_id': int(row['zone_id']),
                        'objectCount': int(row['objectCount']),
                        'lidarEstTime': float(row['lidarEstTime']),
                        'throughputEstTime': float(row['throughputEstTime']),
                        'finalEstTime': float(row['finalEstTime']),
                        'actualPassTime': int(row['actualPassTime'])
                    }
                    all_data.append(parsed_row)
                except (ValueError, KeyError):
                    continue

    return all_data
