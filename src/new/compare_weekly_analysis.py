#!/usr/bin/env python3
"""
Weekly CSV Analysis Comparison Generator

Analyzes CSV data for 3 weekly periods and generates trend comparison

Usage:
    python compare_weekly_analysis.py

Output:
    result/주간_비교분석_3주_트렌드.md
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from new.tables.table_data_loader import load_and_process_data
from new.utils.congestion_utils import get_congestion_level, get_congestion_bins
from tables.generators.base import BaseTableGenerator
from tables.generators.zone_by_congestion import ZoneByCongestionTableGenerator

# Zone name mapping (Korean)
ZONE_NAMES = BaseTableGenerator.ZONE_NAME_DICT
CONGESTION_KR = ZoneByCongestionTableGenerator.CONGESTION_KR_DICT


# ===== DATA LOADING =====

def load_weekly_data(from_date, to_date):
    """Load and process data for a specific week"""
    data, outliers = load_and_process_data(
        data_dir='csv',
        from_date=from_date,
        to_date=to_date
    )
    return data, outliers


# ===== METRICS CALCULATION =====

def calculate_week_metrics(data):
    """Calculate comprehensive metrics for a week"""
    zone_errors = defaultdict(list)
    zone_congestion_errors = defaultdict(lambda: defaultdict(list))
    zone_congestion_predicted = defaultdict(lambda: defaultdict(list))
    zone_congestion_actual = defaultdict(lambda: defaultdict(list))
    congestion_errors = defaultdict(list)

    for record in data:
        zone = record['zone_id']
        error_minutes = (record['finalEstTime'] - record['actualPassTime']) / 60
        congestion = get_congestion_level(record)

        # Aggregate data
        zone_errors[zone].append(error_minutes)
        zone_congestion_errors[zone][congestion].append(error_minutes)
        zone_congestion_predicted[zone][congestion].append(record['finalEstTime'] / 60)
        zone_congestion_actual[zone][congestion].append(record['actualPassTime'] / 60)
        congestion_errors[congestion].append(error_minutes)

    # Calculate summary statistics
    return {
        'zone_avg_errors': {z: statistics.mean(errors) for z, errors in zone_errors.items()},
        'zone_congestion_errors': {
            z: {c: statistics.mean(errors) if errors else 0
                for c, errors in cong.items()}
            for z, cong in zone_congestion_errors.items()
        },
        'congestion_avg_errors': {c: statistics.mean(errors) for c, errors in congestion_errors.items()},
        'zone_wait_times': {
            z: {
                'predicted': statistics.mean([r['finalEstTime'] / 60 for r in data if r['zone_id'] == z]),
                'actual': statistics.mean([r['actualPassTime'] / 60 for r in data if r['zone_id'] == z])
            } for z in zone_errors.keys()
        },
        'total_samples': len(data),
        'zone_sample_counts': {z: len(errors) for z, errors in zone_errors.items()}
    }


def calculate_trend(week1, week2, week3, lower_is_better=True):
    """Calculate week-over-week trends with delta and percentage"""
    w1_to_w2_delta = week2 - week1
    w2_to_w3_delta = week3 - week2
    overall_delta = week3 - week1

    return {
        'values': [week1, week2, week3],
        'w1_to_w2': {
            'delta': w1_to_w2_delta,
            'pct': round((w1_to_w2_delta / week1 * 100), 1) if week1 else 0
        },
        'w2_to_w3': {
            'delta': w2_to_w3_delta,
            'pct': round((w2_to_w3_delta / week2 * 100), 1) if week2 else 0
        },
        'overall': {
            'delta': overall_delta,
            'pct': round((overall_delta / week1 * 100), 1) if week1 else 0
        },
        'trend': assess_trend(overall_delta, lower_is_better)
    }


def assess_trend(overall_delta, lower_is_better):
    """Assess if trend is improving/degrading/stable"""
    threshold = 0.1  # 0.1 minute threshold for errors

    if abs(overall_delta) < threshold:
        return {'status': 'stable', 'icon': '→', 'arrow': '→'}

    is_improving = (overall_delta < 0) if lower_is_better else (overall_delta > 0)
    return {
        'status': 'improving' if is_improving else 'degrading',
        'icon': '✓' if is_improving else '⚠️',
        'arrow': '↓' if overall_delta < 0 else '↑'
    }


def calculate_all_trends(week1_metrics, week2_metrics, week3_metrics):
    """Calculate all trends across 3 weeks"""
    # Zone performance trends
    all_zones = set(week1_metrics['zone_avg_errors'].keys()) | \
                set(week2_metrics['zone_avg_errors'].keys()) | \
                set(week3_metrics['zone_avg_errors'].keys())

    zone_trends = {}
    for zone in all_zones:
        w1 = week1_metrics['zone_avg_errors'].get(zone, 0)
        w2 = week2_metrics['zone_avg_errors'].get(zone, 0)
        w3 = week3_metrics['zone_avg_errors'].get(zone, 0)
        if w1 or w2 or w3:  # At least one week has data
            zone_trends[zone] = calculate_trend(w1, w2, w3, lower_is_better=True)

    # Congestion level trends
    congestion_trends = {}
    for cong in get_congestion_bins():
        w1 = week1_metrics['congestion_avg_errors'].get(cong, 0)
        w2 = week2_metrics['congestion_avg_errors'].get(cong, 0)
        w3 = week3_metrics['congestion_avg_errors'].get(cong, 0)
        congestion_trends[cong] = calculate_trend(w1, w2, w3, lower_is_better=True)

    return {
        'zone_trends': zone_trends,
        'congestion_trends': congestion_trends
    }


def identify_top_changes(zone_trends, n=3):
    """Identify top N improving/degrading zones"""
    deltas = [(zone, trend['overall']['delta']) for zone, trend in zone_trends.items()]

    # Sort by delta (lower is better for errors)
    improving = sorted(deltas, key=lambda x: x[1])[:n]
    degrading = sorted(deltas, key=lambda x: x[1], reverse=True)[:n]

    return {'improving': improving, 'degrading': degrading}


# ===== MARKDOWN FORMATTING =====

def format_number(n):
    """Format number with thousand separators"""
    return f"{n:,}"


def generate_comparison_report(week1_metrics, week2_metrics, week3_metrics, outlier_stats, trends):
    """Generate comprehensive comparison markdown report"""
    sections = []

    # Header
    sections.append("# 주간 예측 성능 비교 분석 (3주 트렌드)\n")
    sections.append("**비교 기간:**")
    sections.append("- Week 1: 2025-12-07 ~ 2025-12-13")
    sections.append("- Week 2: 2025-12-14 ~ 2025-12-20")
    sections.append("- Week 3: 2025-12-21 ~ 2025-12-27\n")
    sections.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    sections.append("---\n")

    # Section 1: Data Quality Trends
    sections.append(generate_data_quality_section(outlier_stats, week1_metrics, week2_metrics, week3_metrics))

    # Section 2: Zone Performance Trends
    sections.append(generate_zone_performance_section(trends, week1_metrics, week2_metrics, week3_metrics))

    # Section 3: Congestion Analysis
    sections.append(generate_congestion_section(trends))

    # Section 4: Summary and Recommendations
    sections.append(generate_summary_section(trends, outlier_stats))

    return '\n'.join(sections)


def generate_data_quality_section(outlier_stats, week1_metrics, week2_metrics, week3_metrics):
    """Generate data quality comparison section"""
    md = ["## 1. 데이터 품질 트렌드\n", "### 1.1 전체 레코드 추이\n"]

    w1_total = outlier_stats['week1']['total_records']
    w2_total = outlier_stats['week2']['total_records']
    w3_total = outlier_stats['week3']['total_records']

    w1_removed = outlier_stats['week1']['removed_records']
    w2_removed = outlier_stats['week2']['removed_records']
    w3_removed = outlier_stats['week3']['removed_records']

    w1_rate = outlier_stats['week1']['removal_rate_pct']
    w2_rate = outlier_stats['week2']['removal_rate_pct']
    w3_rate = outlier_stats['week3']['removal_rate_pct']

    total_trend = calculate_trend(w1_total, w2_total, w3_total, lower_is_better=False)
    rate_trend = calculate_trend(w1_rate, w2_rate, w3_rate, lower_is_better=True)

    md.append("| 지표 | Week 1 | Week 2 | Week 3 | W1→W2 | W2→W3 | 전체 변화 (W1→W3) | 트렌드 |")
    md.append("|------|--------|--------|--------|-------|-------|-----------------|--------|")

    # Total records
    md.append(f"| 전체 레코드 | {format_number(w1_total)} | {format_number(w2_total)} | {format_number(w3_total)} | "
              f"{total_trend['w1_to_w2']['delta']:+,} ({total_trend['w1_to_w2']['pct']:+.1f}%) | "
              f"{total_trend['w2_to_w3']['delta']:+,} ({total_trend['w2_to_w3']['pct']:+.1f}%) | "
              f"{total_trend['overall']['delta']:+,} ({total_trend['overall']['pct']:+.1f}%) | "
              f"{total_trend['trend']['arrow']} |")

    # Outlier rate
    md.append(f"| 이상치 제거율 | {w1_rate:.1f}% | {w2_rate:.1f}% | {w3_rate:.1f}% | "
              f"{rate_trend['w1_to_w2']['delta']:+.1f}pp | "
              f"{rate_trend['w2_to_w3']['delta']:+.1f}pp | "
              f"{rate_trend['overall']['delta']:+.1f}pp | "
              f"{rate_trend['trend']['icon']} {rate_trend['trend']['arrow']} |")

    # Analysis records
    w1_filtered = outlier_stats['week1']['filtered_records']
    w2_filtered = outlier_stats['week2']['filtered_records']
    w3_filtered = outlier_stats['week3']['filtered_records']
    filtered_trend = calculate_trend(w1_filtered, w2_filtered, w3_filtered, lower_is_better=False)

    md.append(f"| 분석 대상 | {format_number(w1_filtered)} | {format_number(w2_filtered)} | {format_number(w3_filtered)} | "
              f"{filtered_trend['w1_to_w2']['delta']:+,} ({filtered_trend['w1_to_w2']['pct']:+.1f}%) | "
              f"{filtered_trend['w2_to_w3']['delta']:+,} ({filtered_trend['w2_to_w3']['pct']:+.1f}%) | "
              f"{filtered_trend['overall']['delta']:+,} ({filtered_trend['overall']['pct']:+.1f}%) | "
              f"{filtered_trend['trend']['arrow']} |\n")

    # Insights
    md.append("**인사이트:**")
    md.append(f"- 📈 데이터 볼륨: Week 1 대비 Week 3에서 {filtered_trend['overall']['pct']:.0f}% 증가 ({format_number(w1_filtered)} → {format_number(w3_filtered)})")
    md.append(f"- {'⚠️' if rate_trend['trend']['status'] == 'degrading' else '✓'} 이상치 비율: {w1_rate:.1f}% → {w2_rate:.1f}% → {w3_rate:.1f}%")

    if w2_rate > w1_rate:
        md.append(f"  - Week 2에서 이상치 비율 {'급증' if w2_rate - w1_rate > 5 else '증가'} ({w1_rate:.1f}% → {w2_rate:.1f}%)")
    if w3_rate < w2_rate:
        md.append(f"  - Week 3에서 {'개선' if w2_rate - w3_rate > 2 else '소폭 개선'} ({w2_rate:.1f}% → {w3_rate:.1f}%)\n")

    # Outlier breakdown
    md.append("### 1.2 이상치 유형별 추이\n")
    md.append("| 이상치 유형 | Week 1 | Week 2 | Week 3 | 전체 변화 |")
    md.append("|------------|--------|--------|--------|-----------|")

    for outlier_type, kr_name in [
        ('actual_time', '실제 대기시간'),
        ('lidar_error', 'LiDAR 예측 오차'),
        ('throughput_error', '처리량 기반 오차'),
        ('final_error', '최종 예측 오차')
    ]:
        w1 = outlier_stats['week1']['outliers_by_type'][outlier_type]
        w2 = outlier_stats['week2']['outliers_by_type'][outlier_type]
        w3 = outlier_stats['week3']['outliers_by_type'][outlier_type]
        delta = w3 - w1
        pct = (delta / w1 * 100) if w1 else 0

        md.append(f"| {kr_name} | {format_number(w1)} | {format_number(w2)} | {format_number(w3)} | "
                  f"{delta:+,} ({pct:+.1f}%) |")

    md.append("\n---\n")
    return '\n'.join(md)


def generate_zone_performance_section(trends, week1_metrics, week2_metrics, week3_metrics):
    """Generate zone performance comparison section"""
    md = ["## 2. 구역별 예측 성능 트렌드\n", "### 2.1 전체 평균 오차 비교\n"]

    md.append("| 구역 | Week 1 | Week 2 | Week 3 | W1→W2 | W2→W3 | 전체 변화 | 트렌드 |")
    md.append("|------|--------|--------|--------|-------|-------|-----------|--------|")

    zone_trends = trends['zone_trends']
    for zone in sorted(zone_trends.keys()):
        zone_name = ZONE_NAMES.get(zone, f'구역 {zone}')
        trend = zone_trends[zone]

        w1 = trend['values'][0]
        w2 = trend['values'][1]
        w3 = trend['values'][2]

        # Skip if all zeros
        if w1 == 0 and w2 == 0 and w3 == 0:
            continue

        md.append(f"| {zone_name} | "
                  f"{w1:+.2f}분 | {w2:+.2f}분 | {w3:+.2f}분 | "
                  f"{trend['w1_to_w2']['delta']:+.2f} | "
                  f"{trend['w2_to_w3']['delta']:+.2f} | "
                  f"{trend['overall']['delta']:+.2f} | "
                  f"{trend['trend']['icon']} {trend['trend']['arrow']} |")

    md.append("\n**주요 발견:**\n")

    # Identify top changes
    top_changes = identify_top_changes(zone_trends, n=3)

    if top_changes['degrading'] and top_changes['degrading'][0][1] > 0.3:
        md.append("🔴 **가장 악화된 구역 (Week 1 → Week 3):**")
        for i, (zone, delta) in enumerate(top_changes['degrading'], 1):
            if delta > 0.3:  # Only show significant degradations
                zone_name = ZONE_NAMES.get(zone, f'구역 {zone}')
                w1 = zone_trends[zone]['values'][0]
                w3 = zone_trends[zone]['values'][2]
                md.append(f"{i}. {zone_name}: {delta:+.2f}분 악화 ({w1:+.2f} → {w3:+.2f})")

    if top_changes['improving'] and top_changes['improving'][0][1] < -0.1:
        md.append("\n🟢 **개선된 구역:**")
        for zone, delta in top_changes['improving']:
            if delta < -0.1:  # Only show meaningful improvements
                zone_name = ZONE_NAMES.get(zone, f'구역 {zone}')
                w1 = zone_trends[zone]['values'][0]
                w3 = zone_trends[zone]['values'][2]
                md.append(f"- {zone_name}: {abs(delta):.2f}분 개선 ({w1:+.2f} → {w3:+.2f})")

    md.append("\n---\n")
    return '\n'.join(md)


def generate_congestion_section(trends):
    """Generate congestion level performance section"""
    md = ["## 3. 혼잡도별 성능 트렌드\n"]

    md.append("| 혼잡도 | Week 1 | Week 2 | Week 3 | 트렌드 |")
    md.append("|--------|--------|--------|--------|--------|")

    congestion_trends = trends['congestion_trends']
    for cong in get_congestion_bins():
        trend = congestion_trends[cong]
        cong_kr = CONGESTION_KR[cong]

        w1, w2, w3 = trend['values']

        md.append(f"| {cong_kr} | {w1:+.2f}분 | {w2:+.2f}분 | {w3:+.2f}분 | "
                  f"{trend['trend']['icon']} {trend['trend']['arrow']} |")

    md.append("\n**인사이트:**")
    for cong in get_congestion_bins():
        trend = congestion_trends[cong]
        if trend['trend']['status'] == 'improving':
            md.append(f"- ✓ {CONGESTION_KR[cong]}: 개선 추세 ({trend['values'][0]:+.2f} → {trend['values'][2]:+.2f}분)")
        elif trend['trend']['status'] == 'degrading' and abs(trend['overall']['delta']) > 0.3:
            md.append(f"- ⚠️ {CONGESTION_KR[cong]}: 악화 추세 ({trend['values'][0]:+.2f} → {trend['values'][2]:+.2f}분, {trend['overall']['delta']:+.2f}분)")

    md.append("\n---\n")
    return '\n'.join(md)


def generate_summary_section(trends, outlier_stats):
    """Generate summary and recommendations section"""
    md = ["## 4. 종합 요약 및 권장사항\n", "### 4.1 핵심 발견사항\n"]

    # Data quality summary
    w1_rate = outlier_stats['week1']['removal_rate_pct']
    w3_rate = outlier_stats['week3']['removal_rate_pct']
    rate_change = w3_rate - w1_rate

    md.append("1. **데이터 품질**")
    md.append(f"   - 📈 레코드 수: {outlier_stats['week1']['total_records']:,} → {outlier_stats['week3']['total_records']:,} (약 {(outlier_stats['week3']['total_records'] / outlier_stats['week1']['total_records']):.1f}배)")
    md.append(f"   - {'⚠️' if rate_change > 0 else '✓'} 이상치 비율: {w1_rate:.1f}% → {w3_rate:.1f}% ({rate_change:+.1f}pp)\n")

    # Zone performance summary
    top_changes = identify_top_changes(trends['zone_trends'], n=3)
    md.append("2. **예측 정확도**")

    if top_changes['degrading'] and top_changes['degrading'][0][1] > 0.5:
        worst_zone, worst_delta = top_changes['degrading'][0]
        md.append(f"   - 🔴 최대 악화: {ZONE_NAMES.get(worst_zone, f'구역 {worst_zone}')} ({worst_delta:+.2f}분)")

    if top_changes['improving'] and top_changes['improving'][0][1] < -0.1:
        best_zone, best_delta = top_changes['improving'][0]
        md.append(f"   - ✓ 최대 개선: {ZONE_NAMES.get(best_zone, f'구역 {best_zone}')} ({best_delta:+.2f}분)\n")
    else:
        md.append("")

    # Congestion summary
    md.append("3. **혼잡도별 성능**")
    for cong in get_congestion_bins():
        trend = trends['congestion_trends'][cong]
        if abs(trend['overall']['delta']) > 0.3:
            status = '개선' if trend['trend']['status'] == 'improving' else '악화'
            md.append(f"   - {CONGESTION_KR[cong]}: {status} ({trend['overall']['delta']:+.2f}분)")

    md.append("\n### 4.2 권장사항\n")

    # Generate recommendations based on findings
    if top_changes['degrading']:
        md.append("1. **성능 악화 구역 집중 분석**")
        for i, (zone, delta) in enumerate(top_changes['degrading'][:2], 1):
            if delta > 0.5:
                zone_name = ZONE_NAMES.get(zone, f'구역 {zone}')
                md.append(f"   - {zone_name}: 급격한 성능 악화 ({delta:+.2f}분) - 원인 조사 필요")

    md.append("\n2. **알고리즘 파라미터 재조정**")
    degrading_congestions = [cong for cong in get_congestion_bins()
                             if trends['congestion_trends'][cong]['trend']['status'] == 'degrading']
    if degrading_congestions:
        md.append(f"   - {', '.join([CONGESTION_KR[c] for c in degrading_congestions])} 레벨에서 과대추정 증가")
        md.append("   - 혼잡도별 스케일 팩터 재조정 검토")

    if rate_change > 5:
        md.append("\n3. **데이터 품질 관리**")
        md.append(f"   - 이상치 비율 {rate_change:+.1f}pp 증가 - 센서 상태 점검 권장")

    md.append("\n---\n")
    md.append(f"생성 스크립트: compare_weekly_analysis.py")

    return '\n'.join(md)


# ===== MAIN PIPELINE =====

def main():
    print("=== 3-Week Comparison Analysis ===\n")

    # Load data for 3 weeks
    print("Loading Week 1 data (2025-12-07 ~ 2025-12-13)...")
    week1_data, week1_outliers = load_weekly_data('20251207', '20251213')

    print("Loading Week 2 data (2025-12-14 ~ 2025-12-20)...")
    week2_data, week2_outliers = load_weekly_data('20251214', '20251220')

    print("Loading Week 3 data (2025-12-21 ~ 2025-12-27)...")
    week3_data, week3_outliers = load_weekly_data('20251221', '20251227')

    # Calculate metrics for each week
    print("\nCalculating metrics...")
    week1_metrics = calculate_week_metrics(week1_data)
    week2_metrics = calculate_week_metrics(week2_data)
    week3_metrics = calculate_week_metrics(week3_data)

    # Package outlier stats
    outlier_stats = {
        'week1': week1_outliers,
        'week2': week2_outliers,
        'week3': week3_outliers
    }

    # Calculate trends
    print("Analyzing trends...")
    trends = calculate_all_trends(week1_metrics, week2_metrics, week3_metrics)

    # Generate comparison report
    print("Generating comparison report...")
    report = generate_comparison_report(week1_metrics, week2_metrics, week3_metrics, outlier_stats, trends)

    # Write output
    result_dir = project_root / 'result'
    result_dir.mkdir(exist_ok=True)
    output_path = result_dir / '주간_비교분석_3주_트렌드.md'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nComparison report generated: {output_path}")


if __name__ == '__main__':
    main()
