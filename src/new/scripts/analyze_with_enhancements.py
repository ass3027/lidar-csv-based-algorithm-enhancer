#!/usr/bin/env python3
"""
Enhanced Algorithm Analysis Script
Analyze queue logs with time-of-day and queue growth enhancements

Usage:
    python analyze_with_enhancements.py [log_dir] [model_dir] [output_file]

Example:
    python analyze_with_enhancements.py csv models enhanced_results.json
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
new_dir = Path(__file__).parent.parent
sys.path.insert(0, str(new_dir.parent))

# Import from new package
from new.core.data_loader import load_all_logs, filter_outliers
from new.core.enhanced_analysis_engine import analyze_with_enhancements


def print_improvement_summary(improvements):
    """Print improvement statistics"""
    print("\n=== Improvement Effect ===\n")

    algorithm_display = {
        'lidarEstTime': 'LiDAR',
        'throughputEstTime': 'Throughput',
        'finalEstTime': 'Final'
    }

    for alg_name, stats in improvements.items():
        print(f"{algorithm_display[alg_name]}:")
        print(f"  Original MAE: {stats['original_mae']:.2f} seconds")
        print(f"  Enhanced MAE: {stats['enhanced_mae']:.2f} seconds")
        print(f"  Improvement Rate: {stats['improvement_pct']:.1f}%\n")


def main(log_dir, model_dir, output_file):
    """
    Main analysis pipeline with enhancements

    Args:
        log_dir: Directory containing CSV files
        model_dir: Directory containing trained models
        output_file: Output JSON file path
    """
    print("=== Enhanced Algorithm Analysis Pipeline ===\n")

    # Load data
    all_data = load_all_logs(log_dir)

    if not all_data:
        print("\nError: Could not load data.")
        return

    # Filter outliers
    filtered_data, outlier_stats = filter_outliers(all_data)

    # Analyze with enhancements
    results = analyze_with_enhancements(filtered_data, model_dir)

    # Add outlier stats
    results['outlier_removal'] = outlier_stats

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nAnalysis results have been saved to {output_file}.")

    # Print summary
    print_improvement_summary(results['improvements'])


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent.parent

    log_dir_arg = sys.argv[1] if len(sys.argv) > 1 else "csv"
    model_dir_arg = sys.argv[2] if len(sys.argv) > 2 else "models"
    output_file_arg = sys.argv[3] if len(sys.argv) > 3 else "enhanced_analysis_results.json"

    log_dir = project_root / log_dir_arg
    model_dir = project_root / model_dir_arg
    output_file = project_root / output_file_arg

    main(log_dir, model_dir, output_file)
