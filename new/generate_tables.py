#!/usr/bin/env python3
"""
Main entry point for summary table generation

Usage:
    python generate_tables.py [data_dir] [output_file]

Example:
    python generate_tables.py passing_log/ output.md
"""

import sys
from scripts.generate_summary_tables_modular import main

if __name__ == '__main__':
    data_dir = sys.argv[1] if len(sys.argv) > 1 else 'passing_log'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'queue_analysis_summary_tables.md'
    main(data_dir, output_file)
