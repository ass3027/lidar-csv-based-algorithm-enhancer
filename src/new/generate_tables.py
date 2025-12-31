#!/usr/bin/env python3
"""
Main entry point for summary table generation

Usage:
    python new/generate_tables.py [data_dir] [--from YYYYMMDD] [--to YYYYMMDD]

Examples:
    python new/generate_tables.py csv
    python new/generate_tables.py csv --from 20251216 --to 20251221
    python new/generate_tables.py passing_log --from 20251220

Output:
    Saves to result/대기시간_통계분석_YYYYMMDD_YYYYMMDD.md
    Date range is extracted from CSV filenames in the data directory
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))



from src.new.tables.table_data_loader import load_and_process_data

from src.new.tables.table_generators import (
    generate_zone_by_day_table,
    generate_zone_by_queue_table,
    generate_zone_by_congestion_table,
    generate_queue_by_day_table,
    generate_sample_count_table,
    generate_summary_statistics_table,
)



def validate_date_format(date_str):
    """
    Validate date string format (YYYYMMDD)

    Args:
        date_str: Date string to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not date_str:
        return True  # None is valid (no filter)

    if len(date_str) != 8 or not date_str.isdigit():
        return False

    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False


def extract_date_range_from_csv_dir(data_dir):
    """Extract the date range (from-to) from CSV filenames in directory"""
    csv_files = list(Path(data_dir).glob("passingObject_*.csv"))
    if not csv_files:
        today = datetime.now().strftime('%Y%m%d')
        return today, today

    # Extract dates from filenames (format: passingObject_YYYYMMDD.csv)
    dates = []
    for csv_file in csv_files:
        try:
            date_str = csv_file.stem.split('_')[1]  # Get YYYYMMDD part
            dates.append(date_str)
        except (IndexError, ValueError):
            continue

    if not dates:
        today = datetime.now().strftime('%Y%m%d')
        return today, today

    return min(dates), max(dates)


def generate_outlier_detection_header(outlier_stats, from_date, to_date):
    """
    Generate outlier detection summary section for the report header

    Args:
        outlier_stats: Dictionary containing outlier detection statistics
        from_date: Start date (YYYYMMDD format)
        to_date: End date (YYYYMMDD format)

    Returns:
        str: Markdown formatted header section
    """
    if not outlier_stats:
        return ""

    # Format dates
    from_date_formatted = f"{from_date[:4]}-{from_date[4:6]}-{from_date[6:]}"
    to_date_formatted = f"{to_date[:4]}-{to_date[4:6]}-{to_date[6:]}"

    # Get breakdown statistics
    breakdown = outlier_stats.get('removal_breakdown', {})
    stage1_removed = breakdown.get('removed_by_hard_bounds_stage1', 0)
    adaptive_removed = breakdown.get('removed_by_adaptive', 0)
    skipped_groups = breakdown.get('skipped_groups_count', 0)

    # Get configuration
    config = outlier_stats.get('config', {})
    min_threshold = config.get('min_sample_threshold', 10)
    lower_mult = config.get('adaptive_lower_mult', 0.3)
    upper_mult = config.get('adaptive_upper_mult', 1.7)

    # Calculate congestion level breakdown
    from collections import defaultdict
    congestion_stats = defaultdict(lambda: {'kept': 0, 'removed_stage1': 0, 'removed_adaptive': 0})

    group_stats = outlier_stats.get('group_statistics', {})
    for (zone_id, congestion_level), stats in group_stats.items():
        congestion_stats[congestion_level]['kept'] += stats.get('kept', 0)
        congestion_stats[congestion_level]['removed_stage1'] += stats.get('removed_by_hard_bounds_stage1', 0)
        congestion_stats[congestion_level]['removed_adaptive'] += stats.get('removed_adaptive', 0)

    header = [
        "# 대기시간 예측 알고리즘 분석 보고서\n",
        f"**분석 기간:** {from_date_formatted} ~ {to_date_formatted}\n",
        "---\n",
        "## 데이터 품질 및 필터링\n",
        f"- **전체 레코드:** {outlier_stats['total_records']:,}건",
        f"- **제거된 레코드:** {outlier_stats['removed_records']:,}건 ({outlier_stats['removal_rate_pct']:.1f}%)",
        f"- **분석 대상:** {outlier_stats['filtered_records']:,}건\n",
        "### 2단계 필터링 프로세스\n",
        "**Stage 1: 구역-혼잡도 기반 하드 바운드 필터링**\n",
        "- Zone 1-4 (신분확인): Low(0-8분), Medium(4-15분), High(6-30분), Very High(8-40분)",
        "- Zone 5-17 (보안검색): Low(0-8분), Medium(2-15분), High(3-20분), Very High(4-30분)",
        f"- **제거:** {stage1_removed:,}건\n",
        "**Stage 2: 적응형 통계 필터링**\n",
        f"- 그룹 단위: (zone_id, congestion_level) - 최대 68개 그룹",
        f"- 필터링 범위: 그룹 평균의 {int(lower_mult*100)}%-{int(upper_mult*100)}%",
        f"- 최소 샘플 요구: {min_threshold}건 (미달 시 적응형 필터 스킵)",
        f"- **제거:** {adaptive_removed:,}건",
        f"- **소규모 그룹 레코드:** {skipped_groups:,}건 (적응형 필터 미적용)\n",
        "### 필터링 결과 요약\n",
        f"| 단계 | 제거 건수 | 비율 |",
        f"|------|----------|------|",
        f"| Stage 1 - 하드 바운드 | {stage1_removed:,}건 | {(stage1_removed/outlier_stats['total_records']*100):.1f}% |",
        f"| Stage 2 - 적응형 필터 | {adaptive_removed:,}건 | {(adaptive_removed/outlier_stats['total_records']*100):.1f}% |",
        f"| **총 제거** | **{outlier_stats['removed_records']:,}건** | **{outlier_stats['removal_rate_pct']:.1f}%** |",
        f"| **최종 분석 대상** | **{outlier_stats['filtered_records']:,}건** | **{(outlier_stats['filtered_records']/outlier_stats['total_records']*100):.1f}%** |\n",
        "### 혼잡도별 필터링 통계\n",
        f"| 혼잡도 | 유지 건수 | Stage 1 제거 | Stage 2 제거 | 유지율 |",
        f"|------|----------|-------------|-------------|--------|"
    ]

    # Add congestion level rows
    for congestion_level in ['Low', 'Medium', 'High', 'Very High']:
        stats = congestion_stats.get(congestion_level, {'kept': 0, 'removed_stage1': 0, 'removed_adaptive': 0})
        total_cong = stats['kept'] + stats['removed_stage1'] + stats['removed_adaptive']
        if total_cong > 0:
            kept_pct = (stats['kept'] / total_cong * 100)
            header.append(
                f"| {congestion_level} | {stats['kept']:,}건 | {stats['removed_stage1']:,}건 | "
                f"{stats['removed_adaptive']:,}건 | {kept_pct:.1f}% |"
            )

    header.extend([
        "\n> **참고:** 센서 오류나 비정상적인 측정값은 2단계 필터링을 통해 자동으로 제거됩니다.\n",
        "---\n"
    ])

    return "\n".join(header)


def main(data_dir, from_date=None, to_date=None):
    """
    Main pipeline for generating summary tables.

    Args:
        data_dir: Directory containing CSV files
        from_date: Optional start date in YYYYMMDD format
        to_date: Optional end date in YYYYMMDD format
    """
    print("--- Summary Table Generation Pipeline ---")

    # Load and process data
    print(f"Loading data from '{data_dir}'...")
    data, outlier_stats = load_and_process_data(data_dir, from_date=from_date, to_date=to_date)

    if not data:
        print("No data loaded. Exiting.")
        return

    print(f"Loaded and filtered {len(data)} records.")

    # Extract date range for output filename
    # If date filters were provided, use them; otherwise extract from all CSV files
    if from_date or to_date:
        # Use the provided date filters for the filename
        output_from_date = from_date if from_date else extract_date_range_from_csv_dir(data_dir)[0]
        output_to_date = to_date if to_date else extract_date_range_from_csv_dir(data_dir)[1]
    else:
        # No filters provided, extract from all files
        output_from_date, output_to_date = extract_date_range_from_csv_dir(data_dir)

    # Generate header with outlier detection summary
    print("Generating report header...")
    header = generate_outlier_detection_header(outlier_stats, output_from_date, output_to_date)

    # Generate all tables
    print("Generating tables...")
    zone_by_day_table = generate_zone_by_day_table(data)
    zone_by_queue_table = generate_zone_by_queue_table(data)
    zone_by_congestion_table = generate_zone_by_congestion_table(data)
    queue_by_day_table = generate_queue_by_day_table(data)
    sample_count_table = generate_sample_count_table(data)
    summary_stats_table = generate_summary_statistics_table(data)

    # Combine header and tables into a single document
    full_report = (
        f"{header}\n"
        f"{zone_by_congestion_table}\n\n"
        f"{zone_by_queue_table}\n\n"
        f"{zone_by_day_table}\n\n"
        f"{queue_by_day_table}\n\n"
        f"{sample_count_table}\n\n"
        f"{summary_stats_table}"
    )

    # Create result directory if it doesn't exist
    result_dir = project_root / "resource" / "result"
    result_dir.mkdir(exist_ok=True)

    # Generate output filename with date range
    output_filename = f"대기시간_통계분석_{output_from_date}_{output_to_date}.md"
    output_path = result_dir / output_filename

    # Save to output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"Successfully generated summary tables in '{output_path}'")



if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Generate summary tables from queue log data',
        epilog='Example: python new/generate_tables.py csv --from 20251216 --to 20251221'
    )
    parser.add_argument(
        'data_dir',
        nargs='?',
        default='csv',
        help='Directory containing CSV files (default: csv)'
    )
    parser.add_argument(
        '--from', '-f',
        dest='from_date',
        metavar='YYYYMMDD',
        help='Start date filter (inclusive, format: YYYYMMDD)'
    )
    parser.add_argument(
        '--to', '-t',
        dest='to_date',
        metavar='YYYYMMDD',
        help='End date filter (inclusive, format: YYYYMMDD)'
    )

    args = parser.parse_args()

    # Validate date formats
    if not validate_date_format(args.from_date):
        print(f"Error: Invalid --from date format '{args.from_date}'. Expected YYYYMMDD (e.g., 20251216)")
        sys.exit(1)

    if not validate_date_format(args.to_date):
        print(f"Error: Invalid --to date format '{args.to_date}'. Expected YYYYMMDD (e.g., 20251221)")
        sys.exit(1)

    # Validate date range logic
    if args.from_date and args.to_date and args.from_date > args.to_date:
        print(f"Error: --from date ({args.from_date}) cannot be later than --to date ({args.to_date})")
        sys.exit(1)

    # Resolve paths
    _data_dir = project_root / 'resource' / args.data_dir

    main(_data_dir, from_date=args.from_date, to_date=args.to_date)
