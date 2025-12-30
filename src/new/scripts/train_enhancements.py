#!/usr/bin/env python3
"""
Enhancement Model Training Script
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
from src.new.core.data_loader import load_all_logs, filter_outliers
from src.new.enhancements.adjustment_trainer import train_all_enhancements


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


def main(log_dir, output_dir):
    """
    Main training pipeline

    Args:
        log_dir: Directory containing CSV files
        output_dir: Directory to save trained models
    """
    print("=== Enhancement Model Training Pipeline ===\n")

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Load data
    all_data = load_all_logs(log_dir)

    if not all_data:
        print("\nError: Could not load data.")
        return

    # Filter outliers
    filtered_data, outlier_stats = filter_outliers(all_data)

    # Split data
    print(f"\nSplitting data...")
    train_data, val_data, test_data = split_train_val_test(filtered_data)

    print(f"  Training data: {len(train_data):,} records (70%)")
    print(f"  Validation data: {len(val_data):,} records (15%)")
    print(f"  Test data: {len(test_data):,} records (15%)")

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

    print(f"\nTraining complete! Models saved in '{output_dir}/' directory.")
    print(f"  - time_of_day_factors.json")
    print(f"  - queue_growth_factors.json")
    print(f"  - training_info.json")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent.parent
    
    # Use command-line arguments if provided, otherwise use defaults relative to project root
    log_dir_arg = sys.argv[1] if len(sys.argv) > 1 else "csv"
    output_dir_arg = sys.argv[2] if len(sys.argv) > 2 else "models"

    # Resolve paths
    log_dir = project_root / log_dir_arg
    output_dir = project_root / output_dir_arg
    
    main(log_dir, output_dir)
