#!/usr/bin/env python3
"""
대기열 예상시간 알고리즘 로그 분석 스크립트 (모듈화 버전)
Analyzes queue estimation algorithm logs with outlier filtering

Refactored version with separated modules:
- data_loader: CSV file loading
- outlier_detection: IQR-based outlier filtering
- analysis_engine: Performance analysis
- statistics_utils: Statistical calculations
"""

import json
from data_loader import load_all_logs
from outlier_detection import filter_outliers
from analysis_engine import analyze_logs


def print_comparison_summary(results_original, results_filtered):
    """
    Print comparison summary between original and filtered data

    Args:
        results_original: Analysis results from original data
        results_filtered: Analysis results from filtered data
    """
    print("=== 이상치 제거 전후 비교 ===\n")
    print("원본 데이터:")
    print(f"  - LiDAR MAE: {results_original['accuracy']['lidarEstTime']['mae']:.2f} 초")
    print(f"  - Throughput MAE: {results_original['accuracy']['throughputEstTime']['mae']:.2f} 초")
    print(f"  - 최종 MAE: {results_original['accuracy']['finalEstTime']['mae']:.2f} 초")
    print(f"  - LiDAR RMSE: {results_original['accuracy']['lidarEstTime']['rmse']:.2f} 초")

    print("\n필터링 후:")
    print(f"  - LiDAR MAE: {results_filtered['accuracy']['lidarEstTime']['mae']:.2f} 초")
    print(f"  - Throughput MAE: {results_filtered['accuracy']['throughputEstTime']['mae']:.2f} 초")
    print(f"  - 최종 MAE: {results_filtered['accuracy']['finalEstTime']['mae']:.2f} 초")
    print(f"  - LiDAR RMSE: {results_filtered['accuracy']['lidarEstTime']['rmse']:.2f} 초")

    lidar_mae_improvement = ((results_original['accuracy']['lidarEstTime']['mae'] -
                              results_filtered['accuracy']['lidarEstTime']['mae']) /
                             results_original['accuracy']['lidarEstTime']['mae'] * 100)

    print(f"\n개선율:")
    print(f"  - LiDAR MAE: {lidar_mae_improvement:.1f}% 개선")


def main(log_dir="passing_log", output_file="queue_analysis_results_filtered.json"):
    """
    Main execution pipeline

    Args:
        log_dir: Directory containing CSV files (default: "passing_log")
        output_file: Output JSON file path (default: "queue_analysis_results_filtered.json")

    Returns:
        Dictionary with combined analysis results
    """
    print("=== 대기열 예상시간 알고리즘 로그 분석 (이상치 필터링) ===\n")

    all_data = load_all_logs(log_dir)

    if not all_data:
        print("\n오류: 데이터를 로드할 수 없습니다.")
        return None

    print("\n--- 원본 데이터 분석 ---")
    results_original = analyze_logs(all_data)

    filtered_data, outlier_stats = filter_outliers(all_data)

    print("\n--- 필터링된 데이터 분석 ---")
    results_filtered = analyze_logs(filtered_data)

    combined_results = {
        'outlier_removal': outlier_stats,
        'original': results_original,
        'filtered': results_filtered
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, indent=2, ensure_ascii=False)

    print(f"\n분석 결과가 {output_file} 에 저장되었습니다.\n")

    print_comparison_summary(results_original, results_filtered)

    return combined_results


if __name__ == "__main__":
    results = main(log_dir="passing_log", output_file="queue_analysis_results_filtered.json")
