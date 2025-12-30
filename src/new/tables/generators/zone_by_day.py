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
            day_eng = get_day_of_week(row['timestamp'])
            day = super().DAY_MAPPING.get(day_eng, day_eng)
            error_minutes = self._calculate_error_minutes(row)
            zone_day_errors[zone][day].append(error_minutes)

        md = ["# 구역별 요일별 평균 오차\n"]
        md.append("## 평균 오차 (분) | +: 과대추정, -: 과소추정\n")

        headers = ['구역'] + super().DAYS + ['평균']

        rows = []
        for zone in super().ALL_ZONES:
            zone_name = super().ZONE_NAME_DICT.get(zone, f'구역 {zone}')
            row_data = [f"**{zone_name}**"]
            zone_all_errors = []

            for day in super().DAYS:
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
