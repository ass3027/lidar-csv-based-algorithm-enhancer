"""
Queue Analysis Package - Modular analysis system for airport queue prediction algorithms

This package provides a comprehensive, modular solution for analyzing queue prediction
performance with aggressive use of Python language features.

Package Structure:
    core/       - Core analysis and data loading functionality
    utils/      - Statistical and outlier detection utilities
    tables/     - Table generation and formatting
    scripts/    - Executable analysis scripts

Main Components:
    - Analysis Engine: Core log analysis with error metrics
    - Data Loader: CSV file loading and parsing
    - Outlier Detection: IQR-based anomaly detection
    - Table Generators: Markdown summary table creation

Example:
    from queue_analysis.core import analyze_logs
    from queue_analysis.utils import detect_outliers_iqr

    data = load_all_logs('csv/')
    filtered_data, stats = filter_outliers(data)
    results = analyze_logs(filtered_data)
"""

__version__ = '2.0.0'
__author__ = 'Gimpo Airport Analytics Team'

from .core.analysis_engine import analyze_logs
from .core.data_loader import load_all_logs, filter_outliers
from .utils.outlier_detection import detect_outliers_iqr
from .utils.statistics_utils import calculate_statistics, calculate_quartiles

__all__ = [
    'analyze_logs',
    'load_all_logs',
    'filter_outliers',
    'detect_outliers_iqr',
    'calculate_statistics',
    'calculate_quartiles',
]
