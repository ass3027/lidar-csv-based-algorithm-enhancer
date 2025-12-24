#!/usr/bin/env python3
"""Queue size by day of week table generator"""

import statistics
from collections import defaultdict
from .base import BaseTableGenerator
from ..table_utils import get_day_of_week, categorize_queue_size


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
