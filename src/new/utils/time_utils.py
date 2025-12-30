#!/usr/bin/env python3
"""시간 유틸리티 - Time parsing and feature extraction utilities"""

from datetime import datetime


def parse_timestamp(timestamp_str):
    """
    Parse timestamp string to datetime object

    Args:
        timestamp_str: "2025-12-21 00:09:09" format

    Returns:
        datetime object
    """
    return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')


def extract_hour_from_timestamp(timestamp_str):
    """
    Extract hour (0-23) from timestamp

    Args:
        timestamp_str: "2025-12-21 00:09:09" or "00:09:09"

    Returns:
        int: Hour (0-23)

    Examples:
        >>> extract_hour_from_timestamp("2025-12-21 14:30:45")
        14
        >>> extract_hour_from_timestamp("08:15:00")
        8
    """
    if len(timestamp_str) <= 8:  # HH:MM:SS format
        return int(timestamp_str.split(':')[0])
    return parse_timestamp(timestamp_str).hour


def extract_hour_from_time(time_str):
    """
    Extract hour from inTime/outTime format

    Args:
        time_str: "00:09:03" format (HH:MM:SS)

    Returns:
        int: Hour (0-23)

    Examples:
        >>> extract_hour_from_time("14:30:45")
        14
        >>> extract_hour_from_time("08:15:00")
        8
    """
    return int(time_str.split(':')[0])


def time_to_seconds(time_str):
    """
    Convert HH:MM:SS to total seconds since midnight

    Args:
        time_str: "00:09:03" format

    Returns:
        int: Seconds since midnight

    Examples:
        >>> time_to_seconds("00:09:03")
        543
        >>> time_to_seconds("01:00:00")
        3600
        >>> time_to_seconds("14:30:45")
        52245
    """
    parts = time_str.split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
