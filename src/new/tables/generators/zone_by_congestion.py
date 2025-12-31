#!/usr/bin/env python3
"""Zone by congestion level table generator"""

import statistics
from itertools import chain
from collections import defaultdict
from .base import BaseTableGenerator
from ...utils.congestion_utils import get_congestion_level, get_congestion_bins, get_congestion_ranges_for_all_groups


class ZoneByCongestionTableGenerator(BaseTableGenerator):
    """Generate average error by zone and congestion level table"""
    CONGESTION_KR_DICT = {'Low': '원활', 'Medium': '보통', 'High': '혼잡', 'Very High': '매우혼잡'}
    def __init__(self, data):
        super().__init__(data)

    def generate(self):
        """Generate complete zone by congestion analysis"""
        # Aggregate data
        zone_congestion_errors, zone_congestion_counts, zone_congestion_predicted, zone_congestion_actual = self._aggregate_data()

        # Build report sections
        md = ["# 구역별 혼잡도별 분석\n"]
        md.extend(self._generate_congestion_definition_section())
        md.extend(self._generate_error_table(zone_congestion_errors, zone_congestion_counts))
        md.extend(self._generate_wait_time_table(zone_congestion_predicted, zone_congestion_actual))

        return "\n".join(md)

    def _aggregate_data(self):
        """Aggregate data by zone and congestion level"""
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

        return zone_congestion_errors, zone_congestion_counts, zone_congestion_predicted, zone_congestion_actual

    def _generate_congestion_definition_section(self):
        """Generate congestion level definition section"""
        md = []
        md.append("## 혼잡도 정의\n")

        congestion_levels = get_congestion_bins()
        ranges = get_congestion_ranges_for_all_groups()

        md.append("### 신분확인 구역 (1-3)\n")
        for level in congestion_levels:
            md.append(f"- **{self.CONGESTION_KR_DICT[level]}**: {ranges['identity'][level]}")

        md.append("\n### 보안검색 구역 (4-17)\n")
        for level in congestion_levels:
            md.append(f"- **{self.CONGESTION_KR_DICT[level]}**: {ranges['security'][level]}")

        return md

    def _generate_error_table(self, zone_congestion_errors, zone_congestion_counts):
        """Generate zone by congestion error table"""
        md = []
        md.append("\n## 1. 구역별 혼잡도별 평균 오차\n")
        md.append("**평균 오차 (분)** | +: 과대추정, -: 과소추정\n")

        congestion_levels = get_congestion_bins()
        headers = ['구역'] + [self.CONGESTION_KR_DICT[level] for level in congestion_levels] + ['평균']
        rows = []

        for zone in super().ALL_ZONES:
            zone_name = super().ZONE_NAME_DICT.get(zone, f'구역 {zone}')
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
            all_errors = list(chain(*(zone_congestion_errors[z][level] for z in super().ALL_ZONES)))
            if all_errors:
                avg = statistics.mean(all_errors)
                total_count = sum(zone_congestion_counts[z][level] for z in super().ALL_ZONES)
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

        return md

    def _generate_wait_time_table(self, zone_congestion_predicted, zone_congestion_actual):
        """Generate predicted vs actual wait time comparison table"""
        md = []
        md.append("\n\n## 2. 평균 대기시간 비교\n")
        md.append("**형식:** 예측값 / 실제값 (min~max) (분) - finalEstTime vs actualPassTime\n")

        congestion_levels = get_congestion_bins()
        headers = ['구역'] + [self.CONGESTION_KR_DICT[level] for level in congestion_levels] + ['평균']
        wait_time_rows = []

        for zone in super().ALL_ZONES:
            zone_name = super().ZONE_NAME_DICT.get(zone, f'구역 {zone}')
            row_data = [f"**{zone_name}**"]

            for level in congestion_levels:
                predicted = zone_congestion_predicted[zone][level]
                actual = zone_congestion_actual[zone][level]

                if predicted and actual:
                    avg_pred = statistics.mean(predicted) / 60
                    avg_actual = statistics.mean(actual) / 60
                    min_actual = min(actual) / 60
                    max_actual = max(actual) / 60
                    row_data.append(f"{avg_pred:.1f} / {avg_actual:.1f} ({min_actual:.1f}~{max_actual:.1f})")
                else:
                    row_data.append("-")

            # Overall average for the zone
            zone_all_predicted = list(chain(*zone_congestion_predicted[zone].values()))
            zone_all_actual = list(chain(*zone_congestion_actual[zone].values()))
            if zone_all_predicted and zone_all_actual:
                avg_pred = statistics.mean(zone_all_predicted) / 60
                avg_actual = statistics.mean(zone_all_actual) / 60
                min_actual = min(zone_all_actual) / 60
                max_actual = max(zone_all_actual) / 60
                row_data.append(f"**{avg_pred:.1f} / {avg_actual:.1f} ({min_actual:.1f}~{max_actual:.1f})**")
            else:
                row_data.append("-")

            wait_time_rows.append("| " + " | ".join(row_data) + " |")

        # Add overall averages row
        wait_time_rows.append("|---|" + "---|" * (len(congestion_levels) + 1))
        overall_row = ["**전체**"]

        for level in congestion_levels:
            all_predicted = list(chain(*(zone_congestion_predicted[z][level] for z in super().ALL_ZONES)))
            all_actual = list(chain(*(zone_congestion_actual[z][level] for z in super().ALL_ZONES)))
            if all_predicted and all_actual:
                avg_pred = statistics.mean(all_predicted) / 60
                avg_actual = statistics.mean(all_actual) / 60
                min_actual = min(all_actual) / 60
                max_actual = max(all_actual) / 60
                overall_row.append(f"**{avg_pred:.1f} / {avg_actual:.1f} ({min_actual:.1f}~{max_actual:.1f})**")
            else:
                overall_row.append("-")

        # Grand overall
        grand_predicted = list(chain(*(chain(*d.values()) for d in zone_congestion_predicted.values())))
        grand_actual = list(chain(*(chain(*d.values()) for d in zone_congestion_actual.values())))
        if grand_predicted and grand_actual:
            avg_pred = statistics.mean(grand_predicted) / 60
            avg_actual = statistics.mean(grand_actual) / 60
            min_actual = min(grand_actual) / 60
            max_actual = max(grand_actual) / 60
            overall_row.append(f"**{avg_pred:.1f} / {avg_actual:.1f} ({min_actual:.1f}~{max_actual:.1f})**")
        else:
            overall_row.append("-")

        wait_time_rows.append("| " + " | ".join(overall_row) + " |")

        md.extend(self._format_markdown_table(headers, wait_time_rows[:-2]))
        md.extend(wait_time_rows[-2:])

        return md