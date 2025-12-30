#!/usr/bin/env python3
"""Zone by queue size table generator"""

import statistics
from itertools import chain
from collections import defaultdict
from .base import BaseTableGenerator
from ..table_utils import categorize_queue_size


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

        md = ["\n\n# 구역별 대기인원별 평균 오차\n"]
        md.append("## 평균 오차 (분) | +: 과대추정, -: 과소추정\n")

        headers = ['구역'] + queue_cats + ['평균']
        rows = []

        for zone in super().ALL_ZONES:
            zone_name = super().ZONE_NAME_DICT.get(zone, f'구역 {zone}')
            row_data = [f"**{zone_name}**"]
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
