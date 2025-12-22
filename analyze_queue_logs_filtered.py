#!/usr/bin/env python3
"""대기열 예상시간 알고리즘 로그 분석 스크립트 (이상치 필터링 버전) - Analyzes queue estimation algorithm logs with outlier filtering"""

import csv
import json
import bisect
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import math

HIGH_ERROR_THRESHOLD = 100
UNDERESTIMATION_THRESHOLD = -30
OVERESTIMATION_THRESHOLD = 50
SHORT_TIME_THRESHOLD = 40
LONG_TIME_THRESHOLD = 500

BIN_EDGES = [10, 20, 30, 40, 50]
BIN_LABELS = ['1-10', '11-20', '21-30', '31-40', '41-50', '50+']

CSV_FIELD_TYPES = {
    'timestamp': str,
    'zone_id': int,
    'objectCount': int,
    'lidarEstTime': float,
    'throughputEstTime': float,
    'finalEstTime': float,
    'actualPassTime': int
}

def calculate_quartiles(values):
    if not values:
        return None, None, None

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def _get_median(arr):
        m = len(arr)
        if m == 0:
            return 0
        if m % 2 == 0:
            return (arr[m//2 - 1] + arr[m//2]) / 2
        return arr[m//2]

    q2_median = _get_median(sorted_vals)
    q1_lower_quartile = _get_median(sorted_vals[:n//2])
    q3_upper_quartile = _get_median(sorted_vals[(n+1)//2:])

    return q1_lower_quartile, q2_median, q3_upper_quartile

def detect_outliers_iqr(values, multiplier=1.5):
    q1, q2, q3 = calculate_quartiles(values)
    if q1 is None:
        return set()

    interquartile_range = q3 - q1
    lower_bound = q1 - multiplier * interquartile_range
    upper_bound = q3 + multiplier * interquartile_range

    return {
        i for i, val in enumerate(values)
        if val < lower_bound or val > upper_bound
    }

def load_all_logs(log_dir="passing_log"):
    log_path = Path(log_dir)
    all_data = []

    for csv_file in sorted(log_path.glob("passingObject_*.csv")):
        print(f"로딩중: {csv_file.name}...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            date_value = csv_file.stem.replace('passingObject_', '')

            all_data.extend([
                {
                    'date': date_value,
                    **{field: converter(row[field]) for field, converter in CSV_FIELD_TYPES.items()}
                }
                for row in reader
            ])

    return all_data

def filter_outliers(data):
    print("\n이상치 탐지 중...")

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
    removal_rate = (removed_count / total_count) * 100

    outlier_stats = {
        'total_records': total_count,
        'removed_records': removed_count,
        'filtered_records': len(filtered_data),
        'removal_rate_pct': removal_rate,
        'outliers_by_type': {name: len(indices) for name, indices in outlier_sets.items()}
    }

    print(f"  총 레코드: {total_count:,} 건")
    print(f"  제거된 레코드: {removed_count:,} 건 ({removal_rate:.1f}%)")
    print(f"  필터링 후: {len(filtered_data):,} 건")

    return filtered_data, outlier_stats

def calculate_statistics(values):
    if not values:
        return {}

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mean = sum(sorted_vals) / n
    variance = sum((x - mean) ** 2 for x in sorted_vals) / n
    std_deviation = math.sqrt(variance)

    median = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2 if n % 2 == 0 else sorted_vals[n//2]

    return {
        'min': sorted_vals[0],
        'max': sorted_vals[-1],
        'mean': mean,
        'median': median,
        'std': std_deviation
    }

def _calculate_percentage_error(error, actual_time):
    return (error / actual_time) * 100 if actual_time > 0 else 0

def _create_error_metrics(errors_dict, actual_time):
    return {
        **{f'{name}_abs_err': abs(err) for name, err in errors_dict.items()},
        **{f'{name}_pct_err': _calculate_percentage_error(err, actual_time) for name, err in errors_dict.items()}
    }

def _categorize_object_count(obj_count):
    return BIN_LABELS[bisect.bisect_right(BIN_EDGES, obj_count)]

def _track_issue_thresholds(errors_dict, issues):
    for name, err in errors_dict.items():
        if abs(err) > HIGH_ERROR_THRESHOLD:
            issues['high_error_cases'][name] += 1
        if err < UNDERESTIMATION_THRESHOLD:
            issues['underestimation'][name] += 1
        if err > OVERESTIMATION_THRESHOLD:
            issues['overestimation'][name] += 1

def _build_accuracy_metrics(errors, abs_errors, pct_errors):
    return {
        'mean_error': sum(errors) / len(errors),
        'mae': sum(abs_errors) / len(abs_errors),
        'rmse': math.sqrt(sum(e**2 for e in errors) / len(errors)),
        'median_error': calculate_statistics(errors)['median'],
        'median_abs_error': calculate_statistics(abs_errors)['median'],
        'mean_pct_error': sum(pct_errors) / len(pct_errors) if pct_errors else 0,
        'std_error': calculate_statistics(errors)['std']
    }

def _aggregate_zone_metrics(records):
    n = len(records)
    return {
        'record_count': n,
        'avg_object_count': sum(r['objectCount'] for r in records) / n,
        'avg_actual_pass_time': sum(r['actualPassTime'] for r in records) / n,
        **{
            f'{metric}_mae': sum(r[f'{metric}_abs_err'] for r in records) / n
            for metric in ['lidar', 'throughput', 'final']
        },
        **{
            f'{metric}_mean_pct_error': sum(r[f'{metric}_pct_err'] for r in records) / n
            for metric in ['lidar', 'throughput', 'final']
        }
    }

def _aggregate_date_metrics(records):
    n = len(records)
    return {
        'record_count': n,
        'avg_object_count': sum(r['objectCount'] for r in records) / n,
        **{
            f'{metric}_mae': sum(r[f'{metric}_abs_err'] for r in records) / n
            for metric in ['lidar', 'throughput', 'final']
        },
        **{
            f'{metric}_mean_pct_error': sum(r[f'{metric}_pct_err'] for r in records) / n
            for metric in ['lidar', 'throughput', 'final']
        }
    }

def _aggregate_correlation_metrics(records):
    n = len(records)
    return {
        'count': n,
        'avg_actual_time': sum(r['actual_time'] for r in records) / n,
        **{
            f'{metric}_mae': sum(r[f'{metric}_abs_err'] for r in records) / n
            for metric in ['lidar', 'throughput', 'final']
        }
    }

def analyze_logs(data):
    print(f"\n총 {len(data):,} 건의 로그 분석 중...\n")

    zone_data = defaultdict(list)
    date_data = defaultdict(list)
    object_bins = defaultdict(list)

    error_lists = {
        f'{metric}_{suffix}': []
        for metric in ['lidar', 'throughput', 'final']
        for suffix in ['errors', 'abs_errors', 'pct_errors']
    }

    object_counts = []
    actual_times = []
    zones = set()
    dates = set()

    issues = {
        'high_error_cases': defaultdict(int),
        'underestimation': defaultdict(int),
        'overestimation': defaultdict(int),
        'extreme_actual_times': {'short': 0, 'long': 0}
    }

    for row in data:
        errors = {
            'lidar': row['lidarEstTime'] - row['actualPassTime'],
            'throughput': row['throughputEstTime'] - row['actualPassTime'],
            'final': row['finalEstTime'] - row['actualPassTime']
        }

        for name, err in errors.items():
            error_lists[f'{name}_errors'].append(err)
            error_lists[f'{name}_abs_errors'].append(abs(err))
            if row['actualPassTime'] > 0:
                error_lists[f'{name}_pct_errors'].append(_calculate_percentage_error(err, row['actualPassTime']))

        object_counts.append(row['objectCount'])
        actual_times.append(row['actualPassTime'])
        zones.add(row['zone_id'])
        dates.add(row['date'])

        error_metrics = _create_error_metrics(errors, row['actualPassTime'])

        zone_data[row['zone_id']].append({
            **error_metrics,
            'objectCount': row['objectCount'],
            'actualPassTime': row['actualPassTime']
        })

        date_data[row['date']].append({
            **error_metrics,
            'objectCount': row['objectCount']
        })

        bin_key = _categorize_object_count(row['objectCount'])
        object_bins[bin_key].append({
            'actual_time': row['actualPassTime'],
            **{f'{name}_abs_err': abs(err) for name, err in errors.items()}
        })

        _track_issue_thresholds(errors, issues)

        if row['actualPassTime'] < SHORT_TIME_THRESHOLD:
            issues['extreme_actual_times']['short'] += 1
        if row['actualPassTime'] > LONG_TIME_THRESHOLD:
            issues['extreme_actual_times']['long'] += 1

    timestamps = [datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S') for row in data]
    min_time, max_time = min(timestamps), max(timestamps)

    error_data = {
        name: (
            error_lists[f'{name}_errors'],
            error_lists[f'{name}_abs_errors'],
            error_lists[f'{name}_pct_errors']
        )
        for name in ['lidar', 'throughput', 'final']
    }

    return {
        'summary': {
            'total_records': len(data),
            'date_range': {
                'start': min_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end': max_time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'zone_coverage': {
                'unique_zones': sorted(zones),
                'total_zones': len(zones)
            },
            'object_count_stats': calculate_statistics(object_counts),
            'actual_pass_time_stats': calculate_statistics(actual_times)
        },
        'accuracy': {
            f'{name}EstTime': _build_accuracy_metrics(*data)
            for name, data in error_data.items()
        },
        'by_zone': {
            int(zone_id): _aggregate_zone_metrics(records)
            for zone_id, records in zone_data.items()
        },
        'by_date': {
            date: _aggregate_date_metrics(records)
            for date, records in date_data.items()
        },
        'issues': dict(issues),
        'correlation': {
            bin_key: _aggregate_correlation_metrics(records)
            for bin_key, records in object_bins.items() if records
        }
    }

def main():
    print("=== 대기열 예상시간 알고리즘 로그 분석 (이상치 필터링) ===\n")

    all_data = load_all_logs()

    print("\n--- 원본 데이터 분석 ---")
    results_original = analyze_logs(all_data)

    filtered_data, outlier_stats = filter_outliers(all_data)

    print("\n--- 필터링된 데이터 분석 ---")
    results_filtered = analyze_logs(filtered_data)

    combined_results = {
        'outlier_removal': outlier_stats,
        'original': results_original,
        'filtered': results_filtered
    }

    output_file = 'queue_analysis_results_filtered.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, indent=2, ensure_ascii=False)

    print(f"\n분석 결과가 {output_file} 에 저장되었습니다.\n")

    comparison_metrics = ['lidarEstTime', 'throughputEstTime', 'finalEstTime']

    print("=== 이상치 제거 전후 비교 ===\n")
    print("원본 데이터:")
    for metric in comparison_metrics:
        mae = results_original['accuracy'][metric]['mae']
        print(f"  - {metric} MAE: {mae:.2f} 초")
    print(f"  - LiDAR RMSE: {results_original['accuracy']['lidarEstTime']['rmse']:.2f} 초")

    print("\n필터링 후:")
    for metric in comparison_metrics:
        mae = results_filtered['accuracy'][metric]['mae']
        print(f"  - {metric} MAE: {mae:.2f} 초")
    print(f"  - LiDAR RMSE: {results_filtered['accuracy']['lidarEstTime']['rmse']:.2f} 초")

    improvements = {
        metric: (
            (results_original['accuracy'][metric]['mae'] - results_filtered['accuracy'][metric]['mae']) /
            results_original['accuracy'][metric]['mae'] * 100
        )
        for metric in comparison_metrics
    }

    print("\n개선율:")
    for metric, improvement in improvements.items():
        print(f"  - {metric}: {improvement:.1f}%")

if __name__ == '__main__':
    main()
