#!/usr/bin/env python3
"""이상치 탐지 모듈 - Outlier detection using IQR method"""

from .statistics_utils import calculate_quartiles


def detect_outliers_iqr(values, multiplier=1.5):
    q1, q2, q3 = calculate_quartiles(values)
    if q1 is None:
        return set()

    interquartile_range = q3 - q1
    lower_bound = q1 - multiplier * interquartile_range
    upper_bound = q3 + multiplier * interquartile_range

    outlier_indices = {
        i for i, val in enumerate(values)
        if val < lower_bound or val > upper_bound
    }

    return outlier_indices


def filter_outliers(data):
    print("\n이상치 탐지 중...")

    actual_times = [row['actualPassTime'] for row in data]
    lidar_errors = [row['lidarEstTime'] - row['actualPassTime'] for row in data]
    throughput_errors = [row['throughputEstTime'] - row['actualPassTime'] for row in data]
    final_errors = [row['finalEstTime'] - row['actualPassTime'] for row in data]

    outliers_actual = detect_outliers_iqr(actual_times)
    outliers_lidar = detect_outliers_iqr(lidar_errors)
    outliers_throughput = detect_outliers_iqr(throughput_errors)
    outliers_final = detect_outliers_iqr(final_errors)

    all_outlier_indices = outliers_actual | outliers_lidar | outliers_throughput | outliers_final

    filtered_data = [
        row for i, row in enumerate(data)
        if i not in all_outlier_indices
    ]

    total_count = len(data)
    removed_count = len(all_outlier_indices)
    filtered_count = len(filtered_data)
    removal_rate = (removed_count / total_count) * 100

    outlier_stats = {
        'total_records': total_count,
        'removed_records': removed_count,
        'filtered_records': filtered_count,
        'removal_rate_pct': removal_rate,
        'outliers_by_type': {
            'actual_time': len(outliers_actual),
            'lidar_error': len(outliers_lidar),
            'throughput_error': len(outliers_throughput),
            'final_error': len(outliers_final)
        }
    }

    print(f"  총 레코드: {total_count:,} 건")
    print(f"  제거된 레코드: {removed_count:,} 건 ({removal_rate:.1f}%)")
    print(f"  필터링 후: {filtered_count:,} 건")

    return filtered_data, outlier_stats
