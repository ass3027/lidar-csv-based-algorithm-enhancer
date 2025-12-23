#!/usr/bin/env python3
"""분석 엔진 모듈 - Analysis engine for queue prediction performance"""

import math
from datetime import datetime
from collections import defaultdict
from ..utils.statistics_utils import calculate_statistics


HIGH_ERROR_THRESHOLD = 100
UNDERESTIMATION_THRESHOLD = -30
OVERESTIMATION_THRESHOLD = 50
SHORT_TIME_THRESHOLD = 40
LONG_TIME_THRESHOLD = 500


def _calculate_percentage_error(error, actual_time):
    return (error / actual_time) * 100 if actual_time > 0 else 0


def _create_error_metrics(lidar_err, throughput_err, final_err, actual_pass_time):
    return {
        'lidar_abs_err': abs(lidar_err),
        'throughput_abs_err': abs(throughput_err),
        'final_abs_err': abs(final_err),
        'lidar_pct_err': _calculate_percentage_error(lidar_err, actual_pass_time),
        'throughput_pct_err': _calculate_percentage_error(throughput_err, actual_pass_time),
        'final_pct_err': _calculate_percentage_error(final_err, actual_pass_time)
    }


def _categorize_object_count(obj_count):
    if obj_count <= 10:
        return '1-10'
    elif obj_count <= 20:
        return '11-20'
    elif obj_count <= 30:
        return '21-30'
    elif obj_count <= 40:
        return '31-40'
    elif obj_count <= 50:
        return '41-50'
    else:
        return '50+'


def _track_issue_thresholds(errors, issues):
    lidar_err, throughput_err, final_err = errors

    error_types = [
        ('lidar', lidar_err),
        ('throughput', throughput_err),
        ('final', final_err)
    ]

    for error_type, error_value in error_types:
        if abs(error_value) > HIGH_ERROR_THRESHOLD:
            issues['high_error_cases'][error_type] += 1
        if error_value < UNDERESTIMATION_THRESHOLD:
            issues['underestimation'][error_type] += 1
        if error_value > OVERESTIMATION_THRESHOLD:
            issues['overestimation'][error_type] += 1


def _build_accuracy_metrics(errors, abs_errors, pct_errors):
    return {
        'mean_error': sum(errors) / len(errors),
        'mae': sum(abs_errors) / len(abs_errors),
        'rmse': math.sqrt(sum(e**2 for e in errors) / len(errors)),
        'median_error': calculate_statistics(errors)['median'],
        'median_abs_error': calculate_statistics(abs_errors)['median'],
        'mean_pct_error': sum(pct_errors) / len(pct_errors),
        'std_error': calculate_statistics(errors)['std']
    }


def _aggregate_zone_metrics(records):
    num_records = len(records)
    return {
        'record_count': num_records,
        'avg_object_count': sum(r['objectCount'] for r in records) / num_records,
        'avg_actual_pass_time': sum(r['actualPassTime'] for r in records) / num_records,
        'lidar_mae': sum(r['lidar_abs_err'] for r in records) / num_records,
        'throughput_mae': sum(r['throughput_abs_err'] for r in records) / num_records,
        'final_mae': sum(r['final_abs_err'] for r in records) / num_records,
        'lidar_mean_pct_error': sum(r['lidar_pct_err'] for r in records) / num_records,
        'throughput_mean_pct_error': sum(r['throughput_pct_err'] for r in records) / num_records,
        'final_mean_pct_error': sum(r['final_pct_err'] for r in records) / num_records
    }


def _aggregate_date_metrics(records):
    num_records = len(records)
    return {
        'record_count': num_records,
        'avg_object_count': sum(r['objectCount'] for r in records) / num_records,
        'lidar_mae': sum(r['lidar_abs_err'] for r in records) / num_records,
        'throughput_mae': sum(r['throughput_abs_err'] for r in records) / num_records,
        'final_mae': sum(r['final_abs_err'] for r in records) / num_records,
        'lidar_mean_pct_error': sum(r['lidar_pct_err'] for r in records) / num_records,
        'throughput_mean_pct_error': sum(r['throughput_pct_err'] for r in records) / num_records,
        'final_mean_pct_error': sum(r['final_pct_err'] for r in records) / num_records
    }


def _aggregate_correlation_metrics(records):
    num_records = len(records)
    return {
        'count': num_records,
        'avg_actual_time': sum(r['actual_time'] for r in records) / num_records,
        'lidar_mae': sum(r['lidar_abs_err'] for r in records) / num_records,
        'throughput_mae': sum(r['throughput_abs_err'] for r in records) / num_records,
        'final_mae': sum(r['final_abs_err'] for r in records) / num_records
    }


def analyze_logs(data):
    print(f"\n총 {len(data):,} 건의 로그 분석 중...\n")

    zone_data = defaultdict(list)
    date_data = defaultdict(list)

    error_lists = {
        'lidar': [], 'throughput': [], 'final': [],
        'lidar_abs': [], 'throughput_abs': [], 'final_abs': [],
        'lidar_pct': [], 'throughput_pct': [], 'final_pct': []
    }

    object_counts = []
    actual_times = []
    zones = set()
    dates = set()

    issues = {
        'high_error_cases': {'lidar': 0, 'throughput': 0, 'final': 0},
        'underestimation': {'lidar': 0, 'throughput': 0, 'final': 0},
        'overestimation': {'lidar': 0, 'throughput': 0, 'final': 0},
        'extreme_actual_times': {'short': 0, 'long': 0}
    }

    object_bins = defaultdict(list)

    for row in data:
        lidar_err = row['lidarEstTime'] - row['actualPassTime']
        throughput_err = row['throughputEstTime'] - row['actualPassTime']
        final_err = row['finalEstTime'] - row['actualPassTime']
        actual_pass_time = row['actualPassTime']

        error_lists['lidar'].append(lidar_err)
        error_lists['throughput'].append(throughput_err)
        error_lists['final'].append(final_err)

        error_lists['lidar_abs'].append(abs(lidar_err))
        error_lists['throughput_abs'].append(abs(throughput_err))
        error_lists['final_abs'].append(abs(final_err))

        if actual_pass_time > 0:
            error_lists['lidar_pct'].append(_calculate_percentage_error(lidar_err, actual_pass_time))
            error_lists['throughput_pct'].append(_calculate_percentage_error(throughput_err, actual_pass_time))
            error_lists['final_pct'].append(_calculate_percentage_error(final_err, actual_pass_time))

        object_counts.append(row['objectCount'])
        actual_times.append(actual_pass_time)
        zones.add(row['zone_id'])
        dates.add(row['date'])

        error_metrics = _create_error_metrics(lidar_err, throughput_err, final_err, actual_pass_time)

        zone_data[row['zone_id']].append({
            **error_metrics,
            'objectCount': row['objectCount'],
            'actualPassTime': actual_pass_time
        })

        date_data[row['date']].append({
            **error_metrics,
            'objectCount': row['objectCount']
        })

        bin_key = _categorize_object_count(row['objectCount'])
        object_bins[bin_key].append({
            'actual_time': actual_pass_time,
            'lidar_abs_err': abs(lidar_err),
            'throughput_abs_err': abs(throughput_err),
            'final_abs_err': abs(final_err)
        })

        _track_issue_thresholds((lidar_err, throughput_err, final_err), issues)

        if actual_pass_time < SHORT_TIME_THRESHOLD:
            issues['extreme_actual_times']['short'] += 1
        if actual_pass_time > LONG_TIME_THRESHOLD:
            issues['extreme_actual_times']['long'] += 1

    timestamps = [datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S') for row in data]
    min_time = min(timestamps)
    max_time = max(timestamps)

    results = {
        'summary': {
            'total_records': len(data),
            'date_range': {
                'start': min_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end': max_time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'zone_coverage': {
                'unique_zones': sorted(list(zones)),
                'total_zones': len(zones)
            },
            'object_count_stats': calculate_statistics(object_counts),
            'actual_pass_time_stats': calculate_statistics(actual_times)
        },
        'accuracy': {
            'lidarEstTime': _build_accuracy_metrics(
                error_lists['lidar'], error_lists['lidar_abs'], error_lists['lidar_pct']
            ),
            'throughputEstTime': _build_accuracy_metrics(
                error_lists['throughput'], error_lists['throughput_abs'], error_lists['throughput_pct']
            ),
            'finalEstTime': _build_accuracy_metrics(
                error_lists['final'], error_lists['final_abs'], error_lists['final_pct']
            )
        },
        'by_zone': {int(zone_id): _aggregate_zone_metrics(records) for zone_id, records in zone_data.items()},
        'by_date': {date: _aggregate_date_metrics(records) for date, records in date_data.items()},
        'issues': issues,
        'correlation': {
            bin_key: _aggregate_correlation_metrics(records)
            for bin_key, records in object_bins.items() if records
        }
    }

    return results
