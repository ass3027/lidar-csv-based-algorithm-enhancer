#!/usr/bin/env python3
"""Congestion level calculation utilities - format-agnostic"""


def get_congestion_level(record):
    """
    Calculate congestion level based on available data in the record.

    This function abstracts congestion level calculation to handle both:
    - Legacy CSV format (without inTime/outTime, only objectCount)
    - New CSV format (with inTime/outTime for actual time-in-queue)

    Congestion levels:
    - 'Low': 0-10 people in queue
    - 'Medium': 11-30 people in queue
    - 'High': 31-50 people in queue
    - 'Very High': 50+ people in queue

    Args:
        record: Dictionary with at least 'objectCount' field

    Returns:
        str: Congestion level category
    """
    object_count = record.get('objectCount', 0)

    if object_count <= 10:
        return 'Low'
    elif object_count <= 30:
        return 'Medium'
    elif object_count <= 50:
        return 'High'
    else:
        return 'Very High'


def get_congestion_bins():
    """
    Get the congestion level bins in order

    Returns:
        list: Ordered list of congestion level names
    """
    return ['Low', 'Medium', 'High', 'Very High']


def categorize_object_count(count):
    """
    Categorize object count into congestion level
    (Alias for get_congestion_level for backward compatibility)

    Args:
        count: Number of objects in queue

    Returns:
        str: Congestion level category
    """
    if count <= 10:
        return 'Low'
    elif count <= 30:
        return 'Medium'
    elif count <= 50:
        return 'High'
    else:
        return 'Very High'


def get_congestion_range(level):
    """
    Get the object count range for a congestion level

    Args:
        level: Congestion level name

    Returns:
        str: Human-readable range description
    """
    ranges = {
        'Low': '0-10 people',
        'Medium': '11-30 people',
        'High': '31-50 people',
        'Very High': '50+ people'
    }
    return ranges.get(level, 'Unknown')
