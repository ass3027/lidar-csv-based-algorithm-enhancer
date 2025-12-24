#!/usr/bin/env python3
"""Summary statistics table generator"""

from collections import defaultdict
from .base import BaseTableGenerator
from ..table_utils import get_day_of_week, categorize_queue_size, calculate_stats


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
