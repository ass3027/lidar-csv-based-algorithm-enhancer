#!/usr/bin/env python3
"""Zone by day of week table generator"""

import statistics
from collections import defaultdict
from .base import BaseTableGenerator
from ..table_utils import get_day_of_week


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
