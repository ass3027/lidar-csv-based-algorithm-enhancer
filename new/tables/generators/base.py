#!/usr/bin/env python3
"""Base class for table generators"""


class BaseTableGenerator:
    """Base class for table generators with common functionality"""

    def __init__(self, data):
        self.data = data
        self.days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    def _calculate_error_minutes(self, row):
        """Calculate error in minutes from a data row"""
        return (row['finalEstTime'] - row['actualPassTime']) / 60.0

    def _format_markdown_table(self, headers, rows, separator_count=None):
        """Format data as markdown table"""
        if separator_count is None:
            separator_count = len(headers)

        md = [f"| {' | '.join(headers)} |"]
        md.append(f"|{'---|' * separator_count}")
        md.extend(rows)
        return md
