#!/usr/bin/env python3
"""Table generator module for queue analysis - class-based architecture"""

import statistics
from itertools import chain
from collections import defaultdict
from .table_utils import get_day_of_week, categorize_queue_size, calculate_stats
from ..utils.congestion_utils import get_congestion_level, get_congestion_bins, get_congestion_range


class BaseTableGenerator:
    """Base class for table generators with common functionality"""

    def __init__(self, data):
        self.data = data
        self.days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    def _calculate_error_minutes(self, row):
        """Calculate error in minutes from a data row"""
        return (row['finalEstTime'] - row['actualPassTime']) / 60.0

    def _format_markdown_table(self, headers, rows, separator_count=None):
        """Format data as markdown table"""
        if separator_count is None:
            separator_count = len(headers)

        md = [f"| {' | '.join(headers)} |"]
        md.append(f"|{'---|' * separator_count}")
        md.extend(rows)
        return md


class ZoneByDayTableGenerator(BaseTableGenerator):
    """Generate average error by zone and day of week table"""

    def generate(self):
        zone_day_errors = defaultdict(lambda: defaultdict(list))

        for row in self.data:
            zone = row['zone_id']
            day = get_day_of_week(row['timestamp'])
            error_minutes = self._calculate_error_minutes(row)
            zone_day_errors[zone][day].append(error_minutes)

        md = ["# Average Error by Zone and Day of Week\n"]
        md.append("## Average Error (minutes) - Positive: Over-estimation, Negative: Under-estimation\n")

        zones = sorted(zone_day_errors.keys())
        headers = ['Zone'] + self.days + ['Average']

        rows = []
        for zone in zones:
            row_data = [f"**Zone {zone}**"]
            zone_all_errors = []

            for day in self.days:
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

            rows.append("| " + " | ".join(row_data) + " |")

        md.extend(self._format_markdown_table(headers, rows))
        return "\n".join(md)


class ZoneByQueueTableGenerator(BaseTableGenerator):
    """Generate average error by zone and queue size table"""

    def generate(self):
        zone_queue_errors = defaultdict(lambda: defaultdict(list))

        for row in self.data:
            zone = row['zone_id']
            queue_cat = categorize_queue_size(row['objectCount'])
            error_minutes = self._calculate_error_minutes(row)
            zone_queue_errors[zone][queue_cat].append(error_minutes)

        queue_cats = sorted(
            set(chain.from_iterable(zone_data.keys() for zone_data in zone_queue_errors.values())),
            key=lambda x: int(x.split('-')[0])
        )
        zones = sorted(zone_queue_errors.keys())

        md = ["\n\n# Average Error by Zone and Queue Size\n"]
        md.append("## Average Error (minutes) - Positive: Over-estimation, Negative: Under-estimation\n")

        headers = ['Zone'] + queue_cats + ['Average']
        rows = []

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

            rows.append("| " + " | ".join(row_data) + " |")

        md.extend(self._format_markdown_table(headers, rows))
        return "\n".join(md)


class ZoneByCongestionTableGenerator(BaseTableGenerator):
    """Generate average error by zone and congestion level table"""

    def generate(self):
        zone_congestion_errors = defaultdict(lambda: defaultdict(list))
        zone_congestion_counts = defaultdict(lambda: defaultdict(int))

        for row in self.data:
            zone = row['zone_id']
            congestion = get_congestion_level(row)
            error_minutes = self._calculate_error_minutes(row)

            zone_congestion_errors[zone][congestion].append(error_minutes)
            zone_congestion_counts[zone][congestion] += 1

        md = ["# Average Error by Zone and Congestion Level\n"]
        md.append("## Congestion Level Definitions\n")

        congestion_levels = get_congestion_bins()
        for level in congestion_levels:
            md.append(f"- **{level}**: {get_congestion_range(level)}")

        md.append("\n## Average Error (minutes) - Positive: Over-estimation, Negative: Under-estimation\n")

        zones = sorted(zone_congestion_errors.keys())
        headers = ['Zone'] + congestion_levels + ['Average']
        rows = []

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

            rows.append("| " + " | ".join(row_data) + " |")

        # Add overall averages row
        rows.append("|---|" + "---|" * (len(congestion_levels) + 1))
        overall_row = ["**Overall**"]

        for level in congestion_levels:
            all_errors = list(chain(*(zone_congestion_errors[z][level] for z in zones)))
            if all_errors:
                avg = statistics.mean(all_errors)
                total_count = sum(zone_congestion_counts[z][level] for z in zones)
                overall_row.append(f"**{avg:+.2f}** ({total_count:,})")
            else:
                overall_row.append("-")

        all_errors = list(chain(*(chain(*d.values()) for d in zone_congestion_errors.values())))
        if all_errors:
            overall_avg = statistics.mean(all_errors)
            overall_row.append(f"**{overall_avg:+.2f}**")
        else:
            overall_row.append("-")

        rows.append("| " + " | ".join(overall_row) + " |")

        md.extend(self._format_markdown_table(headers, rows[:-2]))
        md.extend(rows[-2:])
        return "\n".join(md)


class QueueByDayTableGenerator(BaseTableGenerator):
    """Generate average error by queue size and day of week table"""

    def generate(self):
        queue_day_errors = defaultdict(lambda: defaultdict(list))

        for row in self.data:
            queue_cat = categorize_queue_size(row['objectCount'])
            day = get_day_of_week(row['timestamp'])
            error_minutes = self._calculate_error_minutes(row)
            queue_day_errors[queue_cat][day].append(error_minutes)

        queue_cats = sorted(queue_day_errors.keys(), key=lambda x: int(x.split('-')[0]))

        md = ["\n\n# Average Error by Queue Size and Day of Week\n"]
        md.append("## Average Error (minutes) - Positive: Over-estimation, Negative: Under-estimation\n")

        headers = ['Queue Size'] + self.days + ['Average']
        rows = []

        for queue in queue_cats:
            row_data = [f"**{queue} people**"]
            queue_all_errors = []

            for day in self.days:
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

            rows.append("| " + " | ".join(row_data) + " |")

        md.extend(self._format_markdown_table(headers, rows))
        return "\n".join(md)


class SampleCountTableGenerator(BaseTableGenerator):
    """Generate sample count by zone and day of week table"""

    def generate(self):
        zone_day_counts = defaultdict(lambda: defaultdict(int))

        for row in self.data:
            zone = row['zone_id']
            day = get_day_of_week(row['timestamp'])
            zone_day_counts[zone][day] += 1

        zones = sorted(zone_day_counts.keys())

        md = ["\n\n# Sample Count by Zone and Day of Week\n"]

        headers = ['Zone'] + self.days + ['Total']
        rows = []

        for zone in zones:
            row_data = [f"**Zone {zone}**"]
            zone_total = 0

            for day in self.days:
                count = zone_day_counts[zone][day]
                if count > 0:
                    row_data.append(f"{count:,}")
                    zone_total += count
                else:
                    row_data.append("-")

            row_data.append(f"**{zone_total:,}**")
            rows.append("| " + " | ".join(row_data) + " |")

        # Add total row
        total_row_data = ["**Total**"]
        grand_total = 0
        for day in self.days:
            day_total = sum(zone_day_counts[zone][day] for zone in zones)
            total_row_data.append(f"**{day_total:,}**")
            grand_total += day_total
        total_row_data.append(f"**{grand_total:,}**")
        rows.append("| " + " | ".join(total_row_data) + " |")

        md.extend(self._format_markdown_table(headers, rows))
        return "\n".join(md)


class SummaryStatisticsTableGenerator(BaseTableGenerator):
    """Generate comprehensive summary statistics by multiple dimensions"""

    def generate(self):
        md = ["\n\n# Summary Statistics by Dimension\n"]

        # Statistics by Zone
        md.extend(self._generate_zone_statistics())

        # Statistics by Day of Week
        md.extend(self._generate_day_statistics())

        # Statistics by Queue Size
        md.extend(self._generate_queue_statistics())

        return "\n".join(md)

    def _generate_zone_statistics(self):
        zone_stats = defaultdict(list)
        for row in self.data:
            error_minutes = self._calculate_error_minutes(row)
            zone_stats[row['zone_id']].append(error_minutes)

        md = ["\n## Statistics by Zone\n"]
        md.append("| Zone | Sample Count | Mean Error | Median | Std Dev | Early Est. | Late Est. |")
        md.append("|---|---|---|---|---|---|---|")

        for zone in sorted(zone_stats.keys()):
            errors = zone_stats[zone]
            stats = calculate_stats(errors)
            md.append(f"| Zone {zone} | {stats['count']:,} | {stats['mean']:+.2f} min | "
                     f"{stats['median']:+.2f} min | {stats['std']:.2f} min | "
                     f"{stats['early_count']:,} | {stats['late_count']:,} |")

        return md

    def _generate_day_statistics(self):
        day_stats = defaultdict(list)
        for row in self.data:
            error_minutes = self._calculate_error_minutes(row)
            day = get_day_of_week(row['timestamp'])
            day_stats[day].append(error_minutes)

        md = ["\n## Statistics by Day of Week\n"]
        md.append("| Day | Sample Count | Mean Error | Median | Std Dev | Early Est. | Late Est. |")
        md.append("|---|---|---|---|---|---|---|")

        for day in self.days:
            if day in day_stats:
                errors = day_stats[day]
                stats = calculate_stats(errors)
                md.append(f"| {day} | {stats['count']:,} | {stats['mean']:+.2f} min | "
                         f"{stats['median']:+.2f} min | {stats['std']:.2f} min | "
                         f"{stats['early_count']:,} | {stats['late_count']:,} |")

        return md

    def _generate_queue_statistics(self):
        queue_stats = defaultdict(list)
        for row in self.data:
            error_minutes = self._calculate_error_minutes(row)
            queue_cat = categorize_queue_size(row['objectCount'])
            queue_stats[queue_cat].append(error_minutes)

        md = ["\n## Statistics by Queue Size\n"]
        md.append("| Queue Size | Sample Count | Mean Error | Median | Std Dev | Early Est. | Late Est. |")
        md.append("|---|---|---|---|---|---|---|")

        queue_cats = sorted(queue_stats.keys(), key=lambda x: int(x.split('-')[0]))
        for queue in queue_cats:
            errors = queue_stats[queue]
            stats = calculate_stats(errors)
            md.append(f"| {queue} people | {stats['count']:,} | {stats['mean']:+.2f} min | "
                     f"{stats['median']:+.2f} min | {stats['std']:.2f} min | "
                     f"{stats['early_count']:,} | {stats['late_count']:,} |")

        return md


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
