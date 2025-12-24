#!/usr/bin/env python3
"""Table generator module for queue analysis"""

import statistics
from itertools import chain
from collections import defaultdict
from .table_utils import get_day_of_week, categorize_queue_size, calculate_stats
from ..utils.congestion_utils import get_congestion_level, get_congestion_bins, get_congestion_range


def generate_zone_by_day_table(data):
    zone_day_errors = defaultdict(lambda: defaultdict(list))

    for row in data:
        zone = row['zone_id']
        day = get_day_of_week(row['timestamp'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        zone_day_errors[zone][day].append(error_minutes)

    md = ["# Average Error by Zone and Day of Week\n"]
    md.append("## Average Error (minutes) - Positive: Over-estimation, Negative: Under-estimation\n")

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    zones = sorted(zone_day_errors.keys())

    md.append(f"| Zone | {' | '.join(days)} | Average |")
    md.append(f"|{'---|' * (len(days) + 2)}")

    for zone in zones:
        row_data = [f"**Zone {zone}**"]
        zone_all_errors = []

        for day in days:
            errors = zone_day_errors[zone][day]
            if errors:
                avg = statistics.mean(errors)
                row_data.append(f"{avg:+.2f}")
                zone_all_errors.extend(errors)
            else:
                row_data.append("-")

        if zone_all_errors:
            zone_avg = statistics.mean(zone_all_errors)
            row_data.append(f"**{zone_avg:+.2f}**")
        else:
            row_data.append("-")

        md.append("| " + " | ".join(row_data) + " |")

    return "\n".join(md)


def generate_zone_by_queue_table(data):
    zone_queue_errors = defaultdict(lambda: defaultdict(list))

    for row in data:
        zone = row['zone_id']
        queue_cat = categorize_queue_size(row['objectCount'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        zone_queue_errors[zone][queue_cat].append(error_minutes)

    queue_cats = sorted(
        set(chain.from_iterable(zone_data.keys() for zone_data in zone_queue_errors.values())),
        key=lambda x: int(x.split('-')[0])
    )
    zones = sorted(zone_queue_errors.keys())

    md = ["\n\n# Average Error by Zone and Queue Size\n"]
    md.append("## Average Error (minutes) - Positive: Over-estimation, Negative: Under-estimation\n")

    md.append(f"| Zone | {' | '.join(queue_cats)} | Average |")
    md.append(f"|{'---|' * (len(queue_cats) + 2)}")

    for zone in zones:
        row_data = [f"**Zone {zone}**"]
        zone_all_errors = []

        for queue in queue_cats:
            errors = zone_queue_errors[zone][queue]
            if errors:
                avg = statistics.mean(errors)
                row_data.append(f"{avg:+.2f}")
                zone_all_errors.extend(errors)
            else:
                row_data.append("-")

        if zone_all_errors:
            zone_avg = statistics.mean(zone_all_errors)
            row_data.append(f"**{zone_avg:+.2f}**")
        else:
            row_data.append("-")

        md.append("| " + " | ".join(row_data) + " |")

    return "\n".join(md)


def generate_queue_by_day_table(data):
    queue_day_errors = defaultdict(lambda: defaultdict(list))

    for row in data:
        queue_cat = categorize_queue_size(row['objectCount'])
        day = get_day_of_week(row['timestamp'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        queue_day_errors[queue_cat][day].append(error_minutes)

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    queue_cats = sorted(queue_day_errors.keys(), key=lambda x: int(x.split('-')[0]))

    md = ["\n\n# Average Error by Queue Size and Day of Week\n"]
    md.append("## Average Error (minutes) - Positive: Over-estimation, Negative: Under-estimation\n")

    md.append(f"| Queue Size | {' | '.join(days)} | Average |")
    md.append(f"|{'---|' * (len(days) + 2)}")

    for queue in queue_cats:
        row_data = [f"**{queue} people**"]
        queue_all_errors = []

        for day in days:
            errors = queue_day_errors[queue][day]
            if errors:
                avg = statistics.mean(errors)
                row_data.append(f"{avg:+.2f}")
                queue_all_errors.extend(errors)
            else:
                row_data.append("-")

        if queue_all_errors:
            queue_avg = statistics.mean(queue_all_errors)
            row_data.append(f"**{queue_avg:+.2f}**")
        else:
            row_data.append("-")

        md.append("| " + " | ".join(row_data) + " |")

    return "\n".join(md)


def generate_sample_count_table(data):
    zone_day_counts = defaultdict(lambda: defaultdict(int))

    for row in data:
        zone = row['zone_id']
        day = get_day_of_week(row['timestamp'])
        zone_day_counts[zone][day] += 1

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    zones = sorted(zone_day_counts.keys())

    md = ["\n\n# Sample Count by Zone and Day of Week\n"]

    md.append(f"| Zone | {' | '.join(days)} | Total |")
    md.append(f"|{'---|' * (len(days) + 2)}")

    for zone in zones:
        row_data = [f"**Zone {zone}**"]
        zone_total = 0

        for day in days:
            count = zone_day_counts[zone][day]
            if count > 0:
                row_data.append(f"{count:,}")
                zone_total += count
            else:
                row_data.append("-")

        row_data.append(f"**{zone_total:,}**")
        md.append("| " + " | ".join(row_data) + " |")

    total_row = ["**Total**"]
    grand_total = 0
    for day in days:
        day_total = sum(zone_day_counts[zone][day] for zone in zones)
        total_row.append(f"**{day_total:,}**")
        grand_total += day_total
    total_row.append(f"**{grand_total:,}**")
    md.append("| " + " | ".join(total_row) + " |")

    return "\n".join(md)


def generate_summary_statistics_table(data):
    md = ["\n\n# Summary Statistics by Dimension\n"]

    zone_stats = defaultdict(list)
    for row in data:
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        zone_stats[row['zone_id']].append(error_minutes)

    md.append("\n## Statistics by Zone\n")
    md.append("| Zone | Sample Count | Mean Error | Median | Std Dev | Early Est. | Late Est. |")
    md.append("|---|---|---|---|---|---|---|")

    for zone in sorted(zone_stats.keys()):
        errors = zone_stats[zone]
        stats = calculate_stats(errors)
        md.append(f"| Zone {zone} | {stats['count']:,} | {stats['mean']:+.2f} min | "
                 f"{stats['median']:+.2f} min | {stats['std']:.2f} min | "
                 f"{stats['early_count']:,} | {stats['late_count']:,} |")

    day_stats = defaultdict(list)
    for row in data:
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        day = get_day_of_week(row['timestamp'])
        day_stats[day].append(error_minutes)

    md.append("\n## Statistics by Day of Week\n")
    md.append("| Day | Sample Count | Mean Error | Median | Std Dev | Early Est. | Late Est. |")
    md.append("|---|---|---|---|---|---|---|")

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for day in days:
        if day in day_stats:
            errors = day_stats[day]
            stats = calculate_stats(errors)
            md.append(f"| {day} | {stats['count']:,} | {stats['mean']:+.2f} min | "
                     f"{stats['median']:+.2f} min | {stats['std']:.2f} min | "
                     f"{stats['early_count']:,} | {stats['late_count']:,} |")

    queue_stats = defaultdict(list)
    for row in data:
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        queue_cat = categorize_queue_size(row['objectCount'])
        queue_stats[queue_cat].append(error_minutes)

    md.append("\n## Statistics by Queue Size\n")
    md.append("| Queue Size | Sample Count | Mean Error | Median | Std Dev | Early Est. | Late Est. |")
    md.append("|---|---|---|---|---|---|---|")

    queue_cats = sorted(queue_stats.keys(), key=lambda x: int(x.split('-')[0]))
    for queue in queue_cats:
        errors = queue_stats[queue]
        stats = calculate_stats(errors)
        md.append(f"| {queue} people | {stats['count']:,} | {stats['mean']:+.2f} min | "
                 f"{stats['median']:+.2f} min | {stats['std']:.2f} min | "
                 f"{stats['early_count']:,} | {stats['late_count']:,} |")

    return "\n".join(md)


def generate_zone_by_congestion_table(data):
    """
    Generate table showing average error by zone and congestion level.

    Uses get_congestion_level() abstraction to handle both CSV formats:
    - Legacy: Uses objectCount to determine congestion
    - New: Can use objectCount or inTime/outTime difference

    Congestion levels: Low (0-10), Medium (11-30), High (31-50), Very High (50+)

    Args:
        data: List of parsed records

    Returns:
        str: Markdown table
    """
    zone_congestion_errors = defaultdict(lambda: defaultdict(list))
    zone_congestion_counts = defaultdict(lambda: defaultdict(int))

    for row in data:
        zone = row['zone_id']
        congestion = get_congestion_level(row)
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0

        zone_congestion_errors[zone][congestion].append(error_minutes)
        zone_congestion_counts[zone][congestion] += 1

    md = ["# Average Error by Zone and Congestion Level\n"]
    md.append("## Congestion Level Definitions\n")

    for level in get_congestion_bins():
        md.append(f"- **{level}**: {get_congestion_range(level)}")

    md.append("\n## Average Error (minutes) - Positive: Over-estimation, Negative: Under-estimation\n")

    congestion_levels = get_congestion_bins()
    zones = sorted(zone_congestion_errors.keys())

    md.append(f"| Zone | {' | '.join(congestion_levels)} | Average |")
    md.append(f"|{'---|' * (len(congestion_levels) + 2)}")

    for zone in zones:
        row_data = [f"**Zone {zone}**"]
        zone_all_errors = []

        for level in congestion_levels:
            errors = zone_congestion_errors[zone][level]
            if errors:
                avg = statistics.mean(errors)
                count = zone_congestion_counts[zone][level]
                row_data.append(f"{avg:+.2f} ({count:,})")
                zone_all_errors.extend(errors)
            else:
                row_data.append("-")

        if zone_all_errors:
            zone_avg = statistics.mean(zone_all_errors)
            row_data.append(f"**{zone_avg:+.2f}**")
        else:
            row_data.append("-")

        md.append("| " + " | ".join(row_data) + " |")

    # Add overall averages row
    md.append("|---|" + "---|" * (len(congestion_levels) + 1))
    row_data = ["**Overall**"]

    for level in congestion_levels:
        all_errors = list(chain(*(zone_congestion_errors[z][level] for z in zones)))
        if all_errors:
            avg = statistics.mean(all_errors)
            total_count = sum(zone_congestion_counts[z][level] for z in zones)
            row_data.append(f"**{avg:+.2f}** ({total_count:,})")
        else:
            row_data.append("-")

    all_errors = list(chain(*(chain(*d.values()) for d in zone_congestion_errors.values())))
    if all_errors:
        overall_avg = statistics.mean(all_errors)
        row_data.append(f"**{overall_avg:+.2f}**")
    else:
        row_data.append("-")

    md.append("| " + " | ".join(row_data) + " |")

    return "\n".join(md)
