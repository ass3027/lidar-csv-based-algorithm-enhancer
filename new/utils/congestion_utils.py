#!/usr/bin/env python3
"""Congestion level calculation utilities - format-agnostic"""
congestion_level_table = {
    "identity": [40, 80, 140],
    'security': [5, 11, 16]
}

def get_congestion_level(record):
    zone_id = record.get('zone_id')
    object_count = record.get('objectCount', 0)

    zone_group = 'identity' if zone_id < 4 else 'security'
    congestion_level = congestion_level_table.get(zone_group)


    if object_count <= congestion_level[0]:
        return 'Low'
    elif object_count <= congestion_level[1]:
        return 'Medium'
    elif object_count <= congestion_level[2]:
        return 'High'
    else:
        return 'Very High'


def get_congestion_bins():
    return ['Low', 'Medium', 'High', 'Very High']


def categorize_object_count(count):
    if count <= 10:
        return 'Low'
    elif count <= 30:
        return 'Medium'
    elif count <= 50:
        return 'High'
    else:
        return 'Very High'


def get_congestion_range(level, zone_group='identity'):
    """
    Get the object count range for a congestion level by zone group

    Args:
        level: Congestion level name ('Low', 'Medium', 'High', 'Very High')
        zone_group: 'identity' (zones 1-3) or 'security' (zones 4-17)

    Returns:
        str: Human-readable range description
    """
    thresholds = congestion_level_table.get(zone_group, congestion_level_table['identity'])

    ranges = {
        'Low': f'0-{thresholds[0]} people',
        'Medium': f'{thresholds[0]+1}-{thresholds[1]} people',
        'High': f'{thresholds[1]+1}-{thresholds[2]} people',
        'Very High': f'{thresholds[2]+1}+ people'
    }
    return ranges.get(level, 'Unknown')


def get_congestion_ranges_for_all_groups():
    """Get congestion ranges for both zone groups"""
    identity_ranges = {level: get_congestion_range(level, 'identity') for level in get_congestion_bins()}
    security_ranges = {level: get_congestion_range(level, 'security') for level in get_congestion_bins()}

    return {
        'identity': identity_ranges,
        'security': security_ranges
    }
