#!/usr/bin/env python3
"""Summary statistics table generator"""

from collections import defaultdict
from .base import BaseTableGenerator
from ..table_utils import get_day_of_week, categorize_queue_size, calculate_stats


class SummaryStatisticsTableGenerator(BaseTableGenerator):
    """Generate comprehensive summary statistics by multiple dimensions"""

    def generate(self):
        md = ["\n\n# 차원별 요약 통계\n"]

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

        md = ["\n## 구역별 통계\n"]
        md.append("| 구역 | 샘플 수 | 평균 오차 | 중간값 | 표준편차 | 조기 추정 | 지연 추정 |")
        md.append("|---|---|---|---|---|---|---|")

        for zone in sorted(zone_stats.keys()):
            errors = zone_stats[zone]
            stats = calculate_stats(errors)
            zone_name = self.zone_name_dict.get(zone, f'구역 {zone}')
            md.append(f"| {zone_name} | {stats['count']:,} | {stats['mean']:+.2f}분 | "
                     f"{stats['median']:+.2f}분 | {stats['std']:.2f}분 | "
                     f"{stats['early_count']:,} | {stats['late_count']:,} |")

        return md

    def _generate_day_statistics(self):
        day_stats = defaultdict(list)
        for row in self.data:
            error_minutes = self._calculate_error_minutes(row)
            day_eng = get_day_of_week(row['timestamp'])
            day = self.day_mapping.get(day_eng, day_eng)
            day_stats[day].append(error_minutes)

        md = ["\n## 요일별 통계\n"]
        md.append("| 요일 | 샘플 수 | 평균 오차 | 중간값 | 표준편차 | 조기 추정 | 지연 추정 |")
        md.append("|---|---|---|---|---|---|---|")

        for day in self.days:
            if day in day_stats:
                errors = day_stats[day]
                stats = calculate_stats(errors)
                md.append(f"| {day} | {stats['count']:,} | {stats['mean']:+.2f}분 | "
                         f"{stats['median']:+.2f}분 | {stats['std']:.2f}분 | "
                         f"{stats['early_count']:,} | {stats['late_count']:,} |")

        return md

    def _generate_queue_statistics(self):
        queue_stats = defaultdict(list)
        for row in self.data:
            error_minutes = self._calculate_error_minutes(row)
            queue_cat = categorize_queue_size(row['objectCount'])
            queue_stats[queue_cat].append(error_minutes)

        md = ["\n## 대기인원별 통계\n"]
        md.append("| 대기인원 | 샘플 수 | 평균 오차 | 중간값 | 표준편차 | 조기 추정 | 지연 추정 |")
        md.append("|---|---|---|---|---|---|---|")

        queue_cats = sorted(queue_stats.keys(), key=lambda x: int(x.split('-')[0]))
        for queue in queue_cats:
            errors = queue_stats[queue]
            stats = calculate_stats(errors)
            md.append(f"| {queue}명 | {stats['count']:,} | {stats['mean']:+.2f}분 | "
                     f"{stats['median']:+.2f}분 | {stats['std']:.2f}분 | "
                     f"{stats['early_count']:,} | {stats['late_count']:,} |")

        return md
