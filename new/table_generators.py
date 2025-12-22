#!/usr/bin/env python3
"""테이블 생성 모듈 - Markdown table generators for queue analysis"""

import statistics
from itertools import chain
from collections import defaultdict
from table_utils import get_day_of_week, categorize_queue_size, calculate_stats


def generate_zone_by_day_table(data):
    zone_day_errors = defaultdict(lambda: defaultdict(list))

    for row in data:
        zone = row['zone_id']
        day = get_day_of_week(row['timestamp'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        zone_day_errors[zone][day].append(error_minutes)

    md = ["# 존(Zone) x 요일별 평균 오차 테이블\n"]
    md.append("## 평균 오차 (분) - 양수: 늦게 예상, 음수: 빠르게 예상\n")

    days = ['월', '화', '수', '목', '금', '토', '일']
    zones = sorted(zone_day_errors.keys())

    md.append(f"| Zone | {' | '.join(days)} | 평균 |")
    md.append(f"|{'---|' * (len(days) + 2)}")

    for zone in zones:
        row = [f"**Zone {zone}**"]
        zone_all_errors = []

        for day in days:
            errors = zone_day_errors[zone][day]
            if errors:
                avg = statistics.mean(errors)
                row.append(f"{avg:+.2f}")
                zone_all_errors.extend(errors)
            else:
                row.append("-")

        if zone_all_errors:
            zone_avg = statistics.mean(zone_all_errors)
            row.append(f"**{zone_avg:+.2f}**")
        else:
            row.append("-")

        md.append("| " + " | ".join(row) + " |")

    return "\n".join(md)


def generate_zone_by_queue_table(data):
    zone_queue_errors = defaultdict(lambda: defaultdict(list))

    for row in data:
        zone = row['zone_id']
        queue_cat = categorize_queue_size(row['objectCount'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        zone_queue_errors[zone][queue_cat].append(error_minutes)

    queue_cats = sorted(
        set(chain.from_iterable(zone_data.keys() for zone_data in zone_queue_errors.values())),
        key=lambda x: int(x.split('-')[0])
    )
    zones = sorted(zone_queue_errors.keys())

    md = ["\n\n# 존(Zone) x 대기인원별 평균 오차 테이블\n"]
    md.append("## 평균 오차 (분) - 양수: 늦게 예상, 음수: 빠르게 예상\n")

    md.append(f"| Zone | {' | '.join(queue_cats)} | 평균 |")
    md.append(f"|{'---|' * (len(queue_cats) + 2)}")

    for zone in zones:
        row = [f"**Zone {zone}**"]
        zone_all_errors = []

        for queue in queue_cats:
            errors = zone_queue_errors[zone][queue]
            if errors:
                avg = statistics.mean(errors)
                row.append(f"{avg:+.2f}")
                zone_all_errors.extend(errors)
            else:
                row.append("-")

        if zone_all_errors:
            zone_avg = statistics.mean(zone_all_errors)
            row.append(f"**{zone_avg:+.2f}**")
        else:
            row.append("-")

        md.append("| " + " | ".join(row) + " |")

    return "\n".join(md)


def generate_queue_by_day_table(data):
    queue_day_errors = defaultdict(lambda: defaultdict(list))

    for row in data:
        queue_cat = categorize_queue_size(row['objectCount'])
        day = get_day_of_week(row['timestamp'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        queue_day_errors[queue_cat][day].append(error_minutes)

    days = ['월', '화', '수', '목', '금', '토', '일']
    queue_cats = sorted(queue_day_errors.keys(), key=lambda x: int(x.split('-')[0]))

    md = ["\n\n# 대기인원 x 요일별 평균 오차 테이블\n"]
    md.append("## 평균 오차 (분) - 양수: 늦게 예상, 음수: 빠르게 예상\n")

    md.append(f"| 대기인원 | {' | '.join(days)} | 평균 |")
    md.append(f"|{'---|' * (len(days) + 2)}")

    for queue in queue_cats:
        row = [f"**{queue}명**"]
        queue_all_errors = []

        for day in days:
            errors = queue_day_errors[queue][day]
            if errors:
                avg = statistics.mean(errors)
                row.append(f"{avg:+.2f}")
                queue_all_errors.extend(errors)
            else:
                row.append("-")

        if queue_all_errors:
            queue_avg = statistics.mean(queue_all_errors)
            row.append(f"**{queue_avg:+.2f}**")
        else:
            row.append("-")

        md.append("| " + " | ".join(row) + " |")

    return "\n".join(md)


def generate_sample_count_table(data):
    zone_day_counts = defaultdict(lambda: defaultdict(int))

    for row in data:
        zone = row['zone_id']
        day = get_day_of_week(row['timestamp'])
        zone_day_counts[zone][day] += 1

    days = ['월', '화', '수', '목', '금', '토', '일']
    zones = sorted(zone_day_counts.keys())

    md = ["\n\n# 존(Zone) x 요일별 샘플 수\n"]

    md.append(f"| Zone | {' | '.join(days)} | 합계 |")
    md.append(f"|{'---|' * (len(days) + 2)}")

    for zone in zones:
        row = [f"**Zone {zone}**"]
        zone_total = 0

        for day in days:
            count = zone_day_counts[zone][day]
            if count > 0:
                row.append(f"{count:,}")
                zone_total += count
            else:
                row.append("-")

        row.append(f"**{zone_total:,}**")
        md.append("| " + " | ".join(row) + " |")

    total_row = ["**전체**"]
    grand_total = 0
    for day in days:
        day_total = sum(zone_day_counts[zone][day] for zone in zones)
        total_row.append(f"**{day_total:,}**")
        grand_total += day_total
    total_row.append(f"**{grand_total:,}**")
    md.append("| " + " | ".join(total_row) + " |")

    return "\n".join(md)


def generate_summary_statistics_table(data):
    md = ["\n\n# 차원별 요약 통계\n"]

    zone_stats = defaultdict(list)
    for row in data:
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        zone_stats[row['zone_id']].append(error_minutes)

    md.append("\n## 존(Zone)별 통계\n")
    md.append("| Zone | 샘플 수 | 평균 오차 | 중앙값 | 표준편차 | 빠르게 예상 | 늦게 예상 |")
    md.append("|---|---|---|---|---|---|---|")

    for zone in sorted(zone_stats.keys()):
        errors = zone_stats[zone]
        stats = calculate_stats(errors)
        md.append(f"| Zone {zone} | {stats['count']:,} | {stats['mean']:+.2f}분 | "
                 f"{stats['median']:+.2f}분 | {stats['std']:.2f}분 | "
                 f"{stats['early_count']:,}건 | {stats['late_count']:,}건 |")

    day_stats = defaultdict(list)
    for row in data:
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        day = get_day_of_week(row['timestamp'])
        day_stats[day].append(error_minutes)

    md.append("\n## 요일별 통계\n")
    md.append("| 요일 | 샘플 수 | 평균 오차 | 중앙값 | 표준편차 | 빠르게 예상 | 늦게 예상 |")
    md.append("|---|---|---|---|---|---|---|")

    days = ['월', '화', '수', '목', '금', '토', '일']
    for day in days:
        if day in day_stats:
            errors = day_stats[day]
            stats = calculate_stats(errors)
            md.append(f"| {day}요일 | {stats['count']:,} | {stats['mean']:+.2f}분 | "
                     f"{stats['median']:+.2f}분 | {stats['std']:.2f}분 | "
                     f"{stats['early_count']:,}건 | {stats['late_count']:,}건 |")

    queue_stats = defaultdict(list)
    for row in data:
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        queue_cat = categorize_queue_size(row['objectCount'])
        queue_stats[queue_cat].append(error_minutes)

    md.append("\n## 대기인원별 통계\n")
    md.append("| 대기인원 | 샘플 수 | 평균 오차 | 중앙값 | 표준편차 | 빠르게 예상 | 늦게 예상 |")
    md.append("|---|---|---|---|---|---|---|")

    queue_cats = sorted(queue_stats.keys(), key=lambda x: int(x.split('-')[0]))
    for queue in queue_cats:
        errors = queue_stats[queue]
        stats = calculate_stats(errors)
        md.append(f"| {queue}명 | {stats['count']:,} | {stats['mean']:+.2f}분 | "
                 f"{stats['median']:+.2f}분 | {stats['std']:.2f}분 | "
                 f"{stats['early_count']:,}건 | {stats['late_count']:,}건 |")

    return "\n".join(md)
