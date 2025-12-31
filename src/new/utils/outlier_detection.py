#!/usr/bin/env python3
"""이상치 탐지 모듈 - Outlier detection using IQR method and adaptive zone-congestion filtering"""

import statistics
from collections import defaultdict
from .statistics_utils import calculate_quartiles


# Hard-coded actualPassTime bounds by zone group and congestion level (in seconds)
ZONE_CONGESTION_BOUNDS = {
    # Zone group 1-4 (Identity zones)
    'identity': {
        'Low': (0, 8 * 60),
        'Medium': (4 * 60, 15 * 60),
        'High': (6 * 60, 30 * 60),
        'Very High': (8 * 60, 40 * 60)
    },
    # Zone group 5-17 (Security zones)
    'security': {
        'Low': (0, 8 * 60),
        'Medium': (2 * 60, 15 * 60),
        'High': (3 * 60, 20 * 60),
        'Very High': (4 * 60, 30 * 60)
    }
}


@DeprecationWarning
def detect_outliers_iqr(values, multiplier=1.5):
    q1, q2, q3 = calculate_quartiles(values)
    if q1 is None:
        return set()

    interquartile_range = q3 - q1
    lower_bound = q1 - multiplier * interquartile_range
    upper_bound = q3 + multiplier * interquartile_range

    # Clamp lower bound to 0 for non-negative measurements
    if lower_bound < 0:
        lower_bound = 0

    outlier_indices = {
        i for i, val in enumerate(values)
        if val < lower_bound or val > upper_bound
    }

    return outlier_indices


def get_zone_group(zone_id):
    """Determine zone group based on zone_id"""
    return 'identity' if zone_id <= 4 else 'security'


def check_hard_bounds(record):
    """
    Check if record passes hard-coded zone-congestion bounds

    Args:
        record: Record dict with zone_id, congestion_level, actualPassTime

    Returns:
        bool: True if within bounds, False otherwise
    """
    zone_id = record.get('zone_id')
    congestion_level = record.get('congestion_level')
    actual_time = record.get('actualPassTime')

    if zone_id is None or congestion_level is None or actual_time is None:
        return False

    zone_group = get_zone_group(zone_id)
    bounds = ZONE_CONGESTION_BOUNDS.get(zone_group, {}).get(congestion_level)

    if bounds is None:
        return False

    lower, upper = bounds
    return lower < actual_time < upper


def compute_group_statistics(data, min_sample_threshold, lower_mult, upper_mult):
    """
    Compute statistical bounds for each (zone, congestion) group

    Args:
        data: List of records
        min_sample_threshold: Minimum samples for adaptive filtering
        lower_mult: Lower bound multiplier (e.g., 0.3)
        upper_mult: Upper bound multiplier (e.g., 1.7)

    Returns:
        dict: Group statistics keyed by (zone_id, congestion_level)
    """
    # Group actualPassTime values by (zone, congestion)
    group_data = defaultdict(list)
    for row in data:
        if 'zone_id' in row and 'congestion_level' in row and 'actualPassTime' in row:
            key = (row['zone_id'], row['congestion_level'])
            group_data[key].append(row['actualPassTime'])

    # Calculate statistics using dictionary comprehension with walrus operator
    group_stats = {
        key: {
            'avg_pass_time': (avg := statistics.mean(times)),
            'sample_count': (count := len(times)),
            'skip_adaptive_filter': count < min_sample_threshold,
            'min_time': min(times),
            'max_time': max(times),
            **({'lower_bound': avg * lower_mult, 'upper_bound': avg * upper_mult}
               if count >= min_sample_threshold else {})
        }
        for key, times in group_data.items() if times
    }

    return group_stats


def build_outlier_statistics(original_data, filtered_data, group_stats, tracking, config):
    """
    Build comprehensive outlier statistics dictionary

    Args:
        original_data: Original unfiltered data
        filtered_data: Data after filtering
        group_stats: Group statistics dictionary
        tracking: Tracking dictionary with removal reasons
        config: Configuration parameters dict

    Returns:
        dict: Comprehensive outlier statistics
    """
    total_count = len(original_data)
    removed_count = len(original_data) - len(filtered_data)
    removal_rate = (removed_count / total_count * 100) if total_count > 0 else 0

    # Build per-group statistics
    group_removal_stats = defaultdict(lambda: {
        'total_in_group': 0,
        'removed_by_hard_bounds_stage1': 0,
        'removed_adaptive': 0,
        'kept': 0,
        'skipped_adaptive': 0
    })

    # Count removals per group
    for record in tracking.get('removed_by_hard_bounds_stage1', []):
        key = (record['zone_id'], record['congestion_level'])
        group_removal_stats[key]['removed_by_hard_bounds_stage1'] += 1
        group_removal_stats[key]['total_in_group'] += 1

    for record in tracking['removed_by_adaptive']:
        key = (record['zone_id'], record['congestion_level'])
        group_removal_stats[key]['removed_adaptive'] += 1
        group_removal_stats[key]['total_in_group'] += 1

    for record in tracking['kept_records']:
        key = (record['zone_id'], record['congestion_level'])
        group_removal_stats[key]['kept'] += 1
        group_removal_stats[key]['total_in_group'] += 1

    for record in tracking['skipped_adaptive_groups']:
        key = (record['zone_id'], record['congestion_level'])
        group_removal_stats[key]['skipped_adaptive'] += 1
        group_removal_stats[key]['total_in_group'] += 1

    # Merge with group_stats
    detailed_group_stats = {
        key: {
            **group_removal_stats[key],
            'avg_pass_time': group_stats[key]['avg_pass_time'],
            'sample_count': group_stats[key]['sample_count'],
            'bounds': {
                'lower': group_stats[key].get('lower_bound'),
                'upper': group_stats[key].get('upper_bound')
            } if not group_stats[key]['skip_adaptive_filter'] else None,
            'skipped_group': group_stats[key]['skip_adaptive_filter']
        }
        for key in group_stats
    }

    return {
        # Backward compatible fields
        'total_records': total_count,
        'removed_records': removed_count,
        'filtered_records': len(filtered_data),
        'removal_rate_pct': removal_rate,

        # New fields
        'removal_breakdown': {
            'removed_by_hard_bounds_stage1': len(tracking.get('removed_by_hard_bounds_stage1', [])),
            'removed_by_adaptive': len(tracking['removed_by_adaptive']),
            'skipped_groups_count': len(tracking['skipped_adaptive_groups']),
        },
        'group_statistics': detailed_group_stats,
        'config': config
    }


def print_filter_summary(outlier_stats):
    """Print filtering summary to console"""
    total = outlier_stats['total_records']
    removed = outlier_stats['removed_records']
    filtered = outlier_stats['filtered_records']
    rate = outlier_stats['removal_rate_pct']

    breakdown = outlier_stats['removal_breakdown']
    removed_stage1 = breakdown.get('removed_by_hard_bounds_stage1', 0)
    removed_adaptive = breakdown['removed_by_adaptive']
    skipped_groups = breakdown['skipped_groups_count']

    print(f"  총 레코드: {total:,}건")
    print(f"  Stage 1 - 하드 바운드로 제거: {removed_stage1:,}건")
    print(f"  Stage 2 - 적응형 필터로 제거: {removed_adaptive:,}건")
    print(f"  소규모 샘플 그룹 레코드: {skipped_groups:,}건")
    print(f"  총 제거: {removed:,}건 ({rate:.1f}%)")
    print(f"  필터링 후 레코드: {filtered:,}건")

    # Print group statistics summary
    group_stats = outlier_stats['group_statistics']
    total_groups = len(group_stats)
    skipped_group_count = sum(1 for stats in group_stats.values() if stats['skipped_group'])

    print(f"\n  그룹 통계:")
    print(f"    총 그룹 수: {total_groups}")
    print(f"    적응형 필터링 적용: {total_groups - skipped_group_count}")
    print(f"    스킵된 그룹 (< {outlier_stats['config']['min_sample_threshold']} samples): {skipped_group_count}")

    # Print congestion level breakdown
    from collections import defaultdict
    congestion_stats = defaultdict(lambda: {'kept': 0, 'removed_stage1': 0, 'removed_adaptive': 0})

    for (zone_id, congestion_level), stats in group_stats.items():
        congestion_stats[congestion_level]['kept'] += stats.get('kept', 0)
        congestion_stats[congestion_level]['removed_stage1'] += stats.get('removed_by_hard_bounds_stage1', 0)
        congestion_stats[congestion_level]['removed_adaptive'] += stats.get('removed_adaptive', 0)

    print(f"\n  혼잡도별 통계:")
    for congestion_level in ['Low', 'Medium', 'High', 'Very High']:
        stats = congestion_stats.get(congestion_level, {'kept': 0, 'removed_stage1': 0, 'removed_adaptive': 0})
        total_cong = stats['kept'] + stats['removed_stage1'] + stats['removed_adaptive']
        if total_cong > 0:
            kept_pct = (stats['kept'] / total_cong * 100)
            print(f"    {congestion_level:12s}: 유지 {stats['kept']:6,}건 ({kept_pct:5.1f}%) | "
                  f"Stage1 제거 {stats['removed_stage1']:5,}건 | Stage2 제거 {stats['removed_adaptive']:5,}건")