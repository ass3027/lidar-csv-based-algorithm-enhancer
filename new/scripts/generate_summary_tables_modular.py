#!/usr/bin/env python3
"""
대기 예측시간 분석 요약 테이블 생성 (모듈화 버전)
Generate summary tables from queue prediction analysis data

Refactored version with separated modules:
- table_data_loader: CSV loading with outlier filtering
- table_utils: Utility functions (day of week, queue categorization, stats)
- table_generators: Five different table generator functions
"""

from ..tables.table_data_loader import load_and_process_data
from ..tables.table_generators import (
    generate_zone_by_day_table,
    generate_zone_by_queue_table,
    generate_queue_by_day_table,
    generate_sample_count_table,
    generate_summary_statistics_table
)


def main(data_dir="passing_log", output_file="queue_analysis_summary_tables.md"):
    """
    Main execution pipeline for generating summary tables

    Args:
        data_dir: Directory containing CSV files (default: "passing_log")
        output_file: Output markdown file path (default: "queue_analysis_summary_tables.md")
    """
    print("데이터 로딩 및 처리 중...")
    data = load_and_process_data(data_dir)

    if not data:
        print("\n오류: 데이터를 로드할 수 없습니다.")
        return

    print(f"총 {len(data):,}건의 데이터 처리 완료\n")

    print("테이블 생성 중...")

    tables = []
    tables.append("# 대기열 예상시간 분석 요약 테이블\n")
    tables.append("> 이 문서는 대기 예측시간 분석 데이터를 다양한 관점에서 요약한 테이블입니다.\n")
    tables.append("> - **양수(+)**: 실제보다 늦게 예상\n")
    tables.append("> - **음수(-)**: 실제보다 빠르게 예상\n")

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

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tables))

    print(f"\n✅ 요약 테이블 생성 완료: {output_file}")


if __name__ == "__main__":
    main(data_dir="passing_log", output_file="queue_analysis_summary_tables.md")
