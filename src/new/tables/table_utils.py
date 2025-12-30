#!/usr/bin/env python3
"""Utility functions for table generation"""

import statistics
from datetime import datetime


def get_day_of_week(timestamp_str):
    """
    Get the day of the week from a timestamp string.
    """
    try:
        # Parse the timestamp string
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        # English day names
        days_english = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return days_english[timestamp.weekday()]
    except (ValueError, TypeError):
        return "Invalid Day"


def categorize_queue_size(count):
    if count <= 0:
        return "0"

    bucket_size = 50
    bucket_number = ((count - 1) // bucket_size + 1)
    bucket_max = bucket_number * bucket_size
    bucket_min = bucket_max - bucket_size + 1

    return f"{bucket_min}-{bucket_max}"


def calculate_stats(errors):
    if not errors:
        return {
            'count': 0, 'mean': 0, 'median': 0, 'std': 0,
            'early_count': 0, 'late_count': 0
        }

    return {
        'count': len(errors),
        'mean': statistics.mean(errors),
        'median': statistics.median(errors),
        'std': statistics.stdev(errors) if len(errors) > 1 else 0,
        'early_count': sum(1 for e in errors if e < 0),
        'late_count': sum(1 for e in errors if e > 0),
    }
