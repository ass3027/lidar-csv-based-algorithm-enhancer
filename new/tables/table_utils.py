#!/usr/bin/env python3
"""테이블 유틸리티 모듈 - Utility functions for table generation"""

import statistics


def get_day_of_week(timestamp):
    days_korean = ['월', '화', '수', '목', '금', '토', '일']
    return days_korean[timestamp.weekday()]


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
        return None

    return {
        'count': len(errors),
        'mean': statistics.mean(errors),
        'median': statistics.median(errors),
        'std': statistics.stdev(errors) if len(errors) > 1 else 0,
        'early_count': sum(1 for e in errors if e < 0),
        'late_count': sum(1 for e in errors if e > 0),
    }
