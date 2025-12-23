#!/usr/bin/env python3
"""
향상 모델 훈련 스크립트
Train time-of-day and queue growth enhancement models

Usage:
    python train_enhancements.py [log_dir] [output_dir]

Example:
    python train_enhancements.py csv models
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
new_dir = Path(__file__).parent.parent
sys.path.insert(0, str(new_dir.parent))

# Import from new package
from new.core.data_loader import load_all_logs, filter_outliers
from new.enhancements.adjustment_trainer import train_all_enhancements


def split_train_val_test(data, train_ratio=0.70, val_ratio=0.15):
    """
    Split data into train/validation/test sets

    Args:
        data: List of records
        train_ratio: Training set proportion
        val_ratio: Validation set proportion

    Returns:
        tuple: (train_data, val_data, test_data)
    """
    total = len(data)
    train_end = int(total * train_ratio)
    val_end = int(total * (train_ratio + val_ratio))

    return data[:train_end], data[train_end:val_end], data[val_end:]


def main(log_dir='csv', output_dir='models'):
    """
    Main training pipeline

    Args:
        log_dir: Directory containing CSV files
        output_dir: Directory to save trained models
    """
    print("=== 향상 모델 훈련 파이프라인 ===\n")

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Load data
    all_data = load_all_logs(log_dir)

    if not all_data:
        print("\n오류: 데이터를 로드할 수 없습니다.")
        return

    # Filter outliers
    filtered_data, outlier_stats = filter_outliers(all_data)

    # Split data
    print(f"\n데이터 분할 중...")
    train_data, val_data, test_data = split_train_val_test(filtered_data)

    print(f"  학습 데이터: {len(train_data):,} 건 (70%)")
    print(f"  검증 데이터: {len(val_data):,} 건 (15%)")
    print(f"  테스트 데이터: {len(test_data):,} 건 (15%)")

    # Train enhancements
    training_stats = train_all_enhancements(train_data, output_dir)

    # Save split indices for reproducibility
    split_info = {
        'total_records': len(filtered_data),
        'train_count': len(train_data),
        'val_count': len(val_data),
        'test_count': len(test_data),
        'outlier_removal': outlier_stats,
        'training_stats': training_stats
    }

    with open(f'{output_dir}/training_info.json', 'w', encoding='utf-8') as f:
        json.dump(split_info, f, indent=2, ensure_ascii=False)

    print(f"\n훈련 완료! 모델이 '{output_dir}/' 디렉토리에 저장되었습니다.")
    print(f"  - time_of_day_factors.json")
    print(f"  - queue_growth_factors.json")
    print(f"  - training_info.json")


if __name__ == '__main__':
    log_dir = sys.argv[1] if len(sys.argv) > 1 else 'csv'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'models'
    main(log_dir, output_dir)
