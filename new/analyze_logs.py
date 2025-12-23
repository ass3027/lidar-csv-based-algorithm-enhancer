#!/usr/bin/env python3
"""
Main entry point for queue log analysis

Usage:
    python analyze_logs.py [log_dir]

Example:
    python analyze_logs.py passing_log/
"""

import sys
from scripts.analyze_queue_logs_modular import main

if __name__ == '__main__':
    log_dir = sys.argv[1] if len(sys.argv) > 1 else 'passing_log'
    main(log_dir)
