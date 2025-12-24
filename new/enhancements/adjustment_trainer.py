#!/usr/bin/env python3
"""Train all enhancement modules on historical data"""

import json
from .time_of_day_enhancer import TimeOfDayEnhancer
from .queue_growth_detector import QueueGrowthDetector


def train_all_enhancements(train_records, output_dir='models'):
    """
    Train all enhancement modules

    Args:
        train_records: Training data records
        output_dir: Directory to save trained models

    Returns:
        dict: Training statistics
    """
    print("\n=== Training Time-of-Day Adjustment Factors ===")
    tod_enhancer = TimeOfDayEnhancer()
    tod_stats = tod_enhancer.fit(train_records)
    tod_enhancer.save(f'{output_dir}/time_of_day_factors.json')

    print(f"  Training complete: {tod_stats['total_records']:,} records")
    print(f"  Hours with data: {tod_stats['hours_with_data']} / 24")

    print("\n=== Training Queue Growth Rate Detection ===")
    qg_detector = QueueGrowthDetector(window_minutes=5)
    qg_stats = qg_detector.fit(sorted(train_records, key=lambda r: r['timestamp']))
    qg_detector.save(f'{output_dir}/queue_growth_factors.json')

    print(f"  Training complete: {qg_stats['total_windows']:,} time windows")
    print(f"  Window size: {qg_stats['window_minutes']} minutes")

    return {
        'time_of_day': tod_stats,
        'queue_growth': qg_stats
    }


def apply_all_enhancements(records, model_dir='models', conservative_bias=1.60):
    """
    Apply all trained enhancements with conservative bias

    Args:
        records: Data records to enhance
        model_dir: Directory containing trained models
        conservative_bias: Multiplier to maintain 90% over-prediction rate (default: 1.60)

    Returns:
        list: Enhanced records with combined adjustments
    """
    # Load trained models
    tod_enhancer = TimeOfDayEnhancer()
    tod_enhancer.load(f'{model_dir}/time_of_day_factors.json')

    qg_detector = QueueGrowthDetector()
    qg_detector.load(f'{model_dir}/queue_growth_factors.json')

    # Apply time-of-day adjustments
    tod_adjusted = tod_enhancer.transform(records)

    # Apply queue growth adjustments
    qg_adjusted = qg_detector.transform(sorted(tod_adjusted, key=lambda r: r['timestamp']))

    # Combine both adjustments (multiplicative) with conservative bias
    algorithms = ['lidarEstTime', 'throughputEstTime', 'finalEstTime']
    enhanced_records = []

    for record in qg_adjusted:
        enhanced = {**record}

        for alg in algorithms:
            # Get both adjustment factors
            tod_factor = record[f'{alg}_tod_adjusted'] / record[alg] if record[alg] > 0 else 1.0
            qg_factor = record[f'{alg}_qg_adjusted'] / record[alg] if record[alg] > 0 else 1.0

            # Combined adjustment WITH conservative bias to maintain 90% over-prediction
            combined_factor = tod_factor * qg_factor * conservative_bias
            enhanced[f'{alg}_enhanced'] = round(record[alg] * combined_factor)

        enhanced_records.append(enhanced)

    return enhanced_records
