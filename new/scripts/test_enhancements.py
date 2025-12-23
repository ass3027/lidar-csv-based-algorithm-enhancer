#!/usr/bin/env python3
"""향상 모델 테스트 - Test enhancement performance on held-out test set"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
new_dir = Path(__file__).parent.parent
sys.path.insert(0, str(new_dir.parent))

# Import from new package
from new.core.data_loader import load_all_logs, filter_outliers
from new.core.analysis_engine import analyze_logs
from new.core.enhanced_analysis_engine import analyze_with_enhancements
from new.enhancements.adjustment_trainer import apply_all_enhancements


def load_test_data(model_dir='models'):
    """Load test set indices from training_info.json"""
    with open(f'{model_dir}/training_info.json', 'r') as f:
        info = json.load(f)

    return info


def calculate_over_prediction_rate(records, prediction_field='finalEstTime'):
    """
    Calculate percentage of predictions >= actual

    Args:
        records: Data records
        prediction_field: Which prediction to evaluate

    Returns:
        float: Percentage (0-100)
    """
    over_predictions = sum(
        1 for r in records
        if r[prediction_field] >= r['actualPassTime']
    )

    return (over_predictions / len(records)) * 100 if records else 0


def main(log_dir='csv', model_dir='models'):
    """Test enhancements on held-out test set"""

    print("=== 향상 모델 성능 테스트 ===\n")

    # Load all data
    all_data = load_all_logs(log_dir)
    filtered_data, _ = filter_outliers(all_data)

    # Load training info to get split ratios
    training_info = load_test_data(model_dir)

    # Recreate test split
    train_end = training_info['train_count']
    val_end = train_end + training_info['val_count']
    test_data = filtered_data[val_end:]

    print(f"테스트 데이터: {len(test_data):,} 건\n")

    # Test original algorithm
    print("원본 알고리즘 테스트...")
    original_results = analyze_logs(test_data)

    # Test enhanced algorithm
    print("향상 알고리즘 테스트...")
    enhanced_test = apply_all_enhancements(test_data, model_dir)

    # Create modified records for enhanced analysis
    enhanced_for_analysis = [{
        **r,
        'lidarEstTime': r['lidarEstTime_enhanced'],
        'throughputEstTime': r['throughputEstTime_enhanced'],
        'finalEstTime': r['finalEstTime_enhanced']
    } for r in enhanced_test]

    enhanced_results = analyze_logs(enhanced_for_analysis)

    # Calculate over-prediction rates
    original_over_pct = calculate_over_prediction_rate(test_data, 'finalEstTime')
    enhanced_over_pct = calculate_over_prediction_rate(enhanced_for_analysis, 'finalEstTime')

    # Calculate improvement
    original_mae = original_results['accuracy']['finalEstTime']['mae']
    enhanced_mae = enhanced_results['accuracy']['finalEstTime']['mae']
    improvement_pct = ((original_mae - enhanced_mae) / original_mae) * 100

    # Print results
    print("\n=== 테스트 결과 ===\n")
    print(f"원본 알고리즘:")
    print(f"  MAE: {original_mae:.2f} 초")
    print(f"  RMSE: {original_results['accuracy']['finalEstTime']['rmse']:.2f} 초")
    print(f"  Over-prediction Rate: {original_over_pct:.1f}%")

    print(f"\n향상 알고리즘:")
    print(f"  MAE: {enhanced_mae:.2f} 초")
    print(f"  RMSE: {enhanced_results['accuracy']['finalEstTime']['rmse']:.2f} 초")
    print(f"  Over-prediction Rate: {enhanced_over_pct:.1f}%")

    print(f"\n개선율: {improvement_pct:.1f}%")

    # Constraint check
    if enhanced_over_pct < 90:
        print(f"\n경고: Over-prediction rate가 90% 미만입니다! ({enhanced_over_pct:.1f}%)")
        print("  -> 보수성 제약 조건을 위반했습니다.")
    else:
        print(f"\n성공: Over-prediction rate 90% 이상 달성 ({enhanced_over_pct:.1f}%)")


if __name__ == '__main__':
    log_dir = sys.argv[1] if len(sys.argv) > 1 else 'csv'
    model_dir = sys.argv[2] if len(sys.argv) > 2 else 'models'
    main(log_dir, model_dir)
