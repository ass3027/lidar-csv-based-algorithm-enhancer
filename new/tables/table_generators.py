#!/usr/bin/env python3
"""Table generator module for queue analysis - backward compatible API"""

from .generators import (
    ZoneByDayTableGenerator,
    ZoneByQueueTableGenerator,
    ZoneByCongestionTableGenerator,
    QueueByDayTableGenerator,
    SampleCountTableGenerator,
    SummaryStatisticsTableGenerator,
)


# Public API - backward compatible function interfaces
def generate_zone_by_day_table(data):
    """Generate average error by zone and day of week table"""
    return ZoneByDayTableGenerator(data).generate()


def generate_zone_by_queue_table(data):
    """Generate average error by zone and queue size table"""
    return ZoneByQueueTableGenerator(data).generate()


def generate_zone_by_congestion_table(data):
    """Generate average error by zone and congestion level table"""
    return ZoneByCongestionTableGenerator(data).generate()


def generate_queue_by_day_table(data):
    """Generate average error by queue size and day of week table"""
    return QueueByDayTableGenerator(data).generate()


def generate_sample_count_table(data):
    """Generate sample count by zone and day of week table"""
    return SampleCountTableGenerator(data).generate()


def generate_summary_statistics_table(data):
    """Generate comprehensive summary statistics by multiple dimensions"""
    return SummaryStatisticsTableGenerator(data).generate()

