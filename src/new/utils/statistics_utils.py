#!/usr/bin/env python3
"""통계 유틸리티 모듈 - Statistical utility functions for data analysis"""

import math


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


def calculate_statistics(values):
    if not values:
        return {}

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mean = sum(sorted_vals) / n
    variance = sum((x - mean) ** 2 for x in sorted_vals) / n
    std_deviation = math.sqrt(variance)

    if n % 2 == 0:
        median = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
    else:
        median = sorted_vals[n//2]

    min_val, max_val = sorted_vals[0], sorted_vals[-1]

    return {
        'min': min_val,
        'max': max_val,
        'mean': mean,
        'median': median,
        'std': std_deviation
    }
