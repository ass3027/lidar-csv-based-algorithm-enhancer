#!/usr/bin/env python3
"""Sample count table generator"""

from collections import defaultdict
from .base import BaseTableGenerator
from ..table_utils import get_day_of_week


class SampleCountTableGenerator(BaseTableGenerator):
    """Generate sample count by zone and day of week table"""

    def generate(self):
        zone_day_counts = defaultdict(lambda: defaultdict(int))

        for row in self.data:
            zone = row['zone_id']
            day_eng = get_day_of_week(row['timestamp'])
            day = self.day_mapping.get(day_eng, day_eng)
            zone_day_counts[zone][day] += 1

        md = ["\n\n# 구역별 요일별 샘플 수\n"]

        headers = ['구역'] + self.days + ['합계']
        rows = []

        for zone in self.all_zones:
            zone_name = self.zone_name_dict.get(zone, f'구역 {zone}')
            row_data = [f"**{zone_name}**"]
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
        total_row_data = ["**전체**"]
        grand_total = 0
        for day in self.days:
            day_total = sum(zone_day_counts[zone][day] for zone in self.all_zones)
            total_row_data.append(f"**{day_total:,}**")
            grand_total += day_total
        total_row_data.append(f"**{grand_total:,}**")
        rows.append("| " + " | ".join(total_row_data) + " |")

        md.extend(self._format_markdown_table(headers, rows))
        return "\n".join(md)
