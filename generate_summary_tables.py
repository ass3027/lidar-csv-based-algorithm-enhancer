#!/usr/bin/env python3
"""
Generate summary tables from queue prediction analysis data
Creates multiple views: by zone, by day, by queue size
"""

import csv
import glob
from datetime import datetime
from collections import defaultdict
import statistics

def load_and_process_data():
    """Load all CSV files and process data"""
    files = glob.glob('passing_log/*.csv')
    data = []
    
    for file in files:
        with open(file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    data.append({
                        'timestamp': datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'),
                        'zone_id': int(row['zone_id']),
                        'objectCount': int(row['objectCount']),
                        'finalEstTime': float(row['finalEstTime']),
                        'actualPassTime': float(row['actualPassTime'])
                    })
                except (ValueError, KeyError):
                    continue
    
    # Remove outliers (same logic as main script)
    errors = [abs(row['finalEstTime'] - row['actualPassTime']) for row in data]
    sorted_errors = sorted(errors)
    n = len(sorted_errors)
    q1 = sorted_errors[n // 4]
    q3 = sorted_errors[3 * n // 4]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    clean_data = []
    for i, row in enumerate(data):
        error = abs(row['finalEstTime'] - row['actualPassTime'])
        if error < lower_bound or error > upper_bound or \
                row['actualPassTime'] > 7200 or row['finalEstTime'] > 7200:
            continue
        clean_data.append(row)

    return clean_data

def get_day_of_week(timestamp):
    """Get Korean day of week name"""
    days_kr = ['월', '화', '수', '목', '금', '토', '일']
    return days_kr[timestamp.weekday()]

def categorize_queue_size(count):
    """Categorize object count into 50-person buckets"""
    if count <= 0:
        return "0"
    bucket = ((count - 1) // 50 + 1) * 50
    return f"{bucket-49}-{bucket}"

def calculate_stats(errors):
    """Calculate statistics for a list of errors"""
    if not errors:
        return None
    return {
        'count': len(errors),
        'mean': statistics.mean(errors),
        'median': statistics.median(errors),
        'std': statistics.stdev(errors) if len(errors) > 1 else 0,
        'early_count': len([e for e in errors if e < 0]),
        'late_count': len([e for e in errors if e > 0]),
    }

def generate_zone_by_day_table(data):
    """Generate Zone x Day of Week summary table"""
    # Aggregate by zone and day
    zone_day_errors = defaultdict(lambda: defaultdict(list))
    
    for row in data:
        zone = row['zone_id']
        day = get_day_of_week(row['timestamp'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        zone_day_errors[zone][day].append(error_minutes)
    
    # Generate markdown table
    md = ["# 존(Zone) x 요일별 평균 오차 테이블\n"]
    md.append("## 평균 오차 (분) - +: 늦게 예상, -: 빠르게 예상\n")
    
    days = ['월', '화', '수', '목', '금', '토', '일']
    zones = sorted(zone_day_errors.keys())
    
    # Header
    md.append("| Zone | " + " | ".join(days) + " | 평균 |")
    md.append("|" + "---|" * (len(days) + 2))
    
    # Rows
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
        
        # Add zone average
        if zone_all_errors:
            zone_avg = statistics.mean(zone_all_errors)
            row.append(f"**{zone_avg:+.2f}**")
        else:
            row.append("-")
        
        md.append("| " + " | ".join(row) + " |")
    
    return "\n".join(md)

def generate_zone_by_queue_table(data):
    """Generate Zone x Queue Size summary table"""
    zone_queue_errors = defaultdict(lambda: defaultdict(list))
    
    for row in data:
        zone = row['zone_id']
        queue_cat = categorize_queue_size(row['objectCount'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        zone_queue_errors[zone][queue_cat].append(error_minutes)
    
    # Get all queue categories
    all_queues = set()
    for zone_data in zone_queue_errors.values():
        all_queues.update(zone_data.keys())
    
    queue_cats = sorted(all_queues, key=lambda x: int(x.split('-')[0]))
    zones = sorted(zone_queue_errors.keys())
    
    md = ["\n\n# 존(Zone) x 대기인원별 평균 오차 테이블\n"]
    md.append("## 평균 오차 (분) - +: 늦게 예상, -: 빠르게 예상\n")
    
    # Header
    md.append("| Zone | " + " | ".join(queue_cats) + " | 평균 |")
    md.append("|" + "---|" * (len(queue_cats) + 2))
    
    # Rows
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
        
        # Add zone average
        if zone_all_errors:
            zone_avg = statistics.mean(zone_all_errors)
            row.append(f"**{zone_avg:+.2f}**")
        else:
            row.append("-")
        
        md.append("| " + " | ".join(row) + " |")
    
    return "\n".join(md)

def generate_queue_by_day_table(data):
    """Generate Queue Size x Day of Week summary table"""
    queue_day_errors = defaultdict(lambda: defaultdict(list))
    
    for row in data:
        queue_cat = categorize_queue_size(row['objectCount'])
        day = get_day_of_week(row['timestamp'])
        error_minutes = (row['finalEstTime'] - row['actualPassTime']) / 60.0
        queue_day_errors[queue_cat][day].append(error_minutes)
    
    days = ['월', '화', '수', '목', '금', '토', '일']
    queue_cats = sorted(queue_day_errors.keys(), key=lambda x: int(x.split('-')[0]))
    
    md = ["\n\n# 대기인원 x 요일별 평균 오차 테이블\n"]
    md.append("## 평균 오차 (분) - +: 늦게 예상, -: 빠르게 예상\n")
    
    # Header
    md.append("| 대기인원 | " + " | ".join(days) + " | 평균 |")
    md.append("|" + "---|" * (len(days) + 2))
    
    # Rows
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
        
        # Add queue average
        if queue_all_errors:
            queue_avg = statistics.mean(queue_all_errors)
            row.append(f"**{queue_avg:+.2f}**")
        else:
            row.append("-")
        
        md.append("| " + " | ".join(row) + " |")
    
    return "\n".join(md)

def generate_sample_count_table(data):
    """Generate sample count table for Zone x Day"""
    zone_day_counts = defaultdict(lambda: defaultdict(int))
    
    for row in data:
        zone = row['zone_id']
        day = get_day_of_week(row['timestamp'])
        zone_day_counts[zone][day] += 1
    
    days = ['월', '화', '수', '목', '금', '토', '일']
    zones = sorted(zone_day_counts.keys())
    
    md = ["\n\n# 존(Zone) x 요일별 샘플 수\n"]
    
    # Header
    md.append("| Zone | " + " | ".join(days) + " | 합계 |")
    md.append("|" + "---|" * (len(days) + 2))
    
    # Rows
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
    
    # Total row
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
    """Generate overall summary statistics by different dimensions"""
    md = ["\n\n# 차원별 요약 통계\n"]
    
    # By Zone
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
    
    # By Day
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
    
    # By Queue Size
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

def main():
    print("데이터 로딩 및 처리 중...")
    data = load_and_process_data()
    print(f"총 {len(data):,}건의 데이터 처리 완료\n")
    
    print("테이블 생성 중...")
    
    # Generate all tables
    tables = []
    tables.append("# 대기 예측시간 분석 - 요약 테이블\n")
    tables.append("> 이 문서는 대기 예측시간 분석 데이터를 다양한 관점에서 요약한 테이블입니다.\n")
    tables.append("> - **+(+)**: 실제보다 늦게 예상")
    tables.append("> - **-(-)**: 실제보다 빠르게 예상\n")
    
    print("  - 존 x 요일 테이블 생성...")
    tables.append(generate_zone_by_day_table(data))
    
    print("  - 존 x 대기인원 테이블 생성...")
    tables.append(generate_zone_by_queue_table(data))
    
    print("  - 대기인원 x 요일 테이블 생성...")
    tables.append(generate_queue_by_day_table(data))
    
    print("  - 샘플 수 테이블 생성...")
    tables.append(generate_sample_count_table(data))
    
    print("  - 요약 통계 테이블 생성...")
    tables.append(generate_summary_statistics_table(data))
    
    # Write to file
    output_file = 'queue_analysis_summary_tables_20251223.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tables))
    
    print(f"\n✅ 요약 테이블 생성 완료: {output_file}")

if __name__ == "__main__":
    main()
