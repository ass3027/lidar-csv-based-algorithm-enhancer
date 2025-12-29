#!/usr/bin/env python3
"""Zone by congestion level table generator"""

import statistics
from itertools import chain
from collections import defaultdict
from .base import BaseTableGenerator
from ...utils.congestion_utils import get_congestion_level, get_congestion_bins, get_congestion_ranges_for_all_groups


class ZoneByCongestionTableGenerator(BaseTableGenerator):
    """Generate average error by zone and congestion level table"""

    def generate(self):
        zone_congestion_errors = defaultdict(lambda: defaultdict(list))
        zone_congestion_counts = defaultdict(lambda: defaultdict(int))
        zone_congestion_predicted = defaultdict(lambda: defaultdict(list))
        zone_congestion_actual = defaultdict(lambda: defaultdict(list))

        for row in self.data:
            zone = row['zone_id']
            congestion = get_congestion_level(row)
            error_minutes = self._calculate_error_minutes(row)

            zone_congestion_errors[zone][congestion].append(error_minutes)
            zone_congestion_counts[zone][congestion] += 1
            zone_congestion_predicted[zone][congestion].append(row['finalEstTime'])
            zone_congestion_actual[zone][congestion].append(row['actualPassTime'])

        md = ["# 구역별 혼잡도별 분석\n"]
        md.append("## 혼잡도 정의\n")

        congestion_levels = get_congestion_bins()
        congestion_kr = {'Low': '낮음', 'Medium': '보통', 'High': '높음', 'Very High': '매우높음'}
        ranges = get_congestion_ranges_for_all_groups()

        md.append("### 신분확인 구역 (1-3)\n")
        for level in congestion_levels:
            md.append(f"- **{congestion_kr[level]}**: {ranges['identity'][level]}")

        md.append("\n### 보안검색 구역 (4-17)\n")
        for level in congestion_levels:
            md.append(f"- **{congestion_kr[level]}**: {ranges['security'][level]}")

        md.append("\n## 1. 구역별 혼잡도별 평균 오차\n")
        md.append("**평균 오차 (분)** - 양수: 과대추정, 음수: 과소추정\n")

        headers = ['구역'] + [congestion_kr[level] for level in congestion_levels] + ['평균']
        rows = []

        for zone in self.all_zones:
            zone_name = self.zone_name_dict.get(zone, f'구역 {zone}')
            row_data = [f"**{zone_name}**"]
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
        overall_row = ["**전체**"]

        for level in congestion_levels:
            all_errors = list(chain(*(zone_congestion_errors[z][level] for z in self.all_zones)))
            if all_errors:
                avg = statistics.mean(all_errors)
                total_count = sum(zone_congestion_counts[z][level] for z in self.all_zones)
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

        # Add wait time comparison table
        md.append("\n\n## 2. 평균 대기시간 비교\n")
        md.append("**형식:** 예측값 / 실제값 (초) - finalEstTime vs actualPassTime\n")

        wait_time_rows = []
        for zone in self.all_zones:
            zone_name = self.zone_name_dict.get(zone, f'구역 {zone}')
            row_data = [f"**{zone_name}**"]

            for level in congestion_levels:
                predicted = zone_congestion_predicted[zone][level]
                actual = zone_congestion_actual[zone][level]

                if predicted and actual:
                    avg_pred = statistics.mean(predicted)
                    avg_actual = statistics.mean(actual)
                    row_data.append(f"{avg_pred:.0f} / {avg_actual:.0f}")
                else:
                    row_data.append("-")

            # Overall average for the zone
            zone_all_predicted = list(chain(*zone_congestion_predicted[zone].values()))
            zone_all_actual = list(chain(*zone_congestion_actual[zone].values()))
            if zone_all_predicted and zone_all_actual:
                avg_pred = statistics.mean(zone_all_predicted)
                avg_actual = statistics.mean(zone_all_actual)
                row_data.append(f"**{avg_pred:.0f} / {avg_actual:.0f}**")
            else:
                row_data.append("-")

            wait_time_rows.append("| " + " | ".join(row_data) + " |")

        # Add overall averages row
        wait_time_rows.append("|---|" + "---|" * (len(congestion_levels) + 1))
        overall_row = ["**전체**"]

        for level in congestion_levels:
            all_predicted = list(chain(*(zone_congestion_predicted[z][level] for z in self.all_zones)))
            all_actual = list(chain(*(zone_congestion_actual[z][level] for z in self.all_zones)))
            if all_predicted and all_actual:
                avg_pred = statistics.mean(all_predicted)
                avg_actual = statistics.mean(all_actual)
                overall_row.append(f"**{avg_pred:.0f} / {avg_actual:.0f}**")
            else:
                overall_row.append("-")

        # Grand overall
        grand_predicted = list(chain(*(chain(*d.values()) for d in zone_congestion_predicted.values())))
        grand_actual = list(chain(*(chain(*d.values()) for d in zone_congestion_actual.values())))
        if grand_predicted and grand_actual:
            avg_pred = statistics.mean(grand_predicted)
            avg_actual = statistics.mean(grand_actual)
            overall_row.append(f"**{avg_pred:.0f} / {avg_actual:.0f}**")
        else:
            overall_row.append("-")

        wait_time_rows.append("| " + " | ".join(overall_row) + " |")

        md.extend(self._format_markdown_table(headers, wait_time_rows[:-2]))
        md.extend(wait_time_rows[-2:])

        return "\n".join(md)
