#!/usr/bin/env python3
"""Base class for table generators"""


class BaseTableGenerator:
    """Base class for table generators with common functionality"""

    def __init__(self, data):
        self.data = data
        self.days = ['월', '화', '수', '목', '금', '토', '일']
        self.day_mapping = {
            'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목',
            'Fri': '금', 'Sat': '토', 'Sun': '일'
        }
        self.zone_name_dict = {
            1: '유인신분확인',
            2: '우선신분확인',
            3: '바이오신분확인',
            4: '보안검색14',
            5: '보안검색13',
            6: '보안검색12',
            7: '보안검색11',
            8: '보안검색10',
            9: '보안검색9',
            10: '보안검색8',
            11: '보안검색7',
            12: '보안검색6',
            13: '보안검색5',
            14: '보안검색4',
            15: '보안검색3',
            16: '보안검색2',
            17: '보안검색1',
        }

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
