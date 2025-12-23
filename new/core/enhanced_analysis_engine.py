#!/usr/bin/env python3
"""향상된 분석 엔진 - Enhanced analysis engine with time-of-day and queue growth adjustments"""

from .analysis_engine import analyze_logs
from ..enhancements.adjustment_trainer import apply_all_enhancements


def analyze_with_enhancements(data, model_dir='models'):
    """
    Analyze logs with enhanced predictions

    Args:
        data: List of data records
        model_dir: Directory containing trained enhancement models

    Returns:
        dict: Analysis results comparing original vs enhanced predictions
    """
    print("\n=== 원본 알고리즘 분석 ===")
    original_results = analyze_logs(data)

    print("\n=== 향상된 알고리즘 적용 ===")
    enhanced_data = apply_all_enhancements(data, model_dir)

    # Temporarily replace prediction fields with enhanced versions
    enhanced_for_analysis = []
    for record in enhanced_data:
        modified = {**record}
        # Use enhanced predictions for error calculation
        modified['lidarEstTime'] = record['lidarEstTime_enhanced']
        modified['throughputEstTime'] = record['throughputEstTime_enhanced']
        modified['finalEstTime'] = record['finalEstTime_enhanced']
        enhanced_for_analysis.append(modified)

    print("\n=== 향상된 알고리즘 분석 ===")
    enhanced_results = analyze_logs(enhanced_for_analysis)

    # Calculate improvement metrics
    improvements = {}
    for alg in ['lidarEstTime', 'throughputEstTime', 'finalEstTime']:
        original_mae = original_results['accuracy'][alg]['mae']
        enhanced_mae = enhanced_results['accuracy'][alg]['mae']
        improvement_pct = ((original_mae - enhanced_mae) / original_mae) * 100

        improvements[alg] = {
            'original_mae': original_mae,
            'enhanced_mae': enhanced_mae,
            'improvement_pct': improvement_pct
        }

    return {
        'original': original_results,
        'enhanced': enhanced_results,
        'improvements': improvements
    }
