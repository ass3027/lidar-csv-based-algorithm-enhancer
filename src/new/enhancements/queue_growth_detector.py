#!/usr/bin/env python3
"""대기열 변화율 탐지 - Queue growth rate detection and dynamic adjustment"""

import json
from collections import defaultdict
from datetime import datetime
from ..utils.time_utils import parse_timestamp


class QueueGrowthDetector:
    """
    Detects queue growth patterns and applies dynamic adjustments

    Training Process:
    1. Build time-series of queue sizes per zone in time windows (e.g., 5 minutes)
    2. Calculate entry/exit rates
    3. Classify: Growing (entries > exits), Stable, Shrinking (exits > entries)
    4. Calculate error patterns for each state

    Inference Process:
    1. Detect current queue state from recent time window
    2. Apply state-specific adjustment factor
    """

    def __init__(self, window_minutes=5):
        self.window_minutes = window_minutes
        self.window_seconds = window_minutes * 60
        self.growth_factors = {}  # {state: {algorithm: factor}}
        self.growth_stats = {}
        self.algorithms = ['lidarEstTime', 'throughputEstTime', 'finalEstTime']
        self.is_trained = False

    def _classify_queue_state(self, current_count, previous_count):
        """
        Classify queue growth state

        Args:
            current_count: Current queue size
            previous_count: Queue size at previous time window

        Returns:
            str: 'growing', 'stable', 'shrinking'
        """
        threshold = 0.1  # 10% change threshold

        if previous_count == 0:
            return 'stable'

        change_ratio = (current_count - previous_count) / previous_count

        if change_ratio > threshold:
            return 'growing'
        elif change_ratio < -threshold:
            return 'shrinking'
        else:
            return 'stable'

    def fit(self, records):
        """
        Train queue growth adjustment factors

        Args:
            records: List of data records sorted by timestamp

        Returns:
            dict: Training statistics
        """
        # Group records by zone and time window
        zone_windows = defaultdict(list)

        for record in records:
            zone_id = record['zone_id']
            timestamp = parse_timestamp(record['timestamp'])

            # Round down to time window (e.g., 00:00-00:05, 00:05-00:10, ...)
            window_start = timestamp.replace(
                minute=(timestamp.minute // self.window_minutes) * self.window_minutes,
                second=0,
                microsecond=0
            )

            window_key = (zone_id, window_start)
            zone_windows[window_key].append(record)

        # Calculate queue states and corresponding errors
        state_data = defaultdict(lambda: {alg: [] for alg in self.algorithms})

        sorted_windows = sorted(zone_windows.keys())

        for i, window_key in enumerate(sorted_windows):
            zone_id, window_time = window_key
            current_records = zone_windows[window_key]

            if not current_records:
                continue

            # Average queue size in current window
            avg_current_count = sum(r['objectCount'] for r in current_records) / len(current_records)

            # Find previous window for same zone
            previous_count = None
            for j in range(i - 1, -1, -1):
                prev_zone, prev_time = sorted_windows[j]
                if prev_zone == zone_id:
                    prev_records = zone_windows[sorted_windows[j]]
                    previous_count = sum(r['objectCount'] for r in prev_records) / len(prev_records)
                    break

            if previous_count is None:
                state = 'stable'  # First window for zone
            else:
                state = self._classify_queue_state(avg_current_count, previous_count)

            # Record error ratios for this state
            for record in current_records:
                for alg in self.algorithms:
                    if record[alg] > 0:
                        error_ratio = record['actualPassTime'] / record[alg]
                        state_data[state][alg].append(error_ratio)

        # Calculate adjustment factors per state
        for state in ['growing', 'stable', 'shrinking']:
            self.growth_factors[state] = {}

            for alg in self.algorithms:
                ratios = state_data[state][alg]

                if len(ratios) >= 20:  # Minimum samples
                    mean_ratio = sum(ratios) / len(ratios)
                    self.growth_factors[state][alg] = mean_ratio
                else:
                    self.growth_factors[state][alg] = 1.0  # Neutral factor

        # Statistics
        self.growth_stats = {
            state: {
                'record_count': sum(len(state_data[state][alg]) for alg in self.algorithms) // len(self.algorithms),
                'factors': self.growth_factors[state]
            }
            for state in ['growing', 'stable', 'shrinking']
        }

        self.is_trained = True

        return {
            'total_windows': len(zone_windows),
            'window_minutes': self.window_minutes,
            'growth_stats': self.growth_stats
        }

    def transform(self, records):
        """
        Apply queue growth adjustments

        Args:
            records: List of data records (must be sorted by timestamp)

        Returns:
            list: Records with added fields: lidar_qg_adjusted, throughput_qg_adjusted, final_qg_adjusted
        """
        if not self.is_trained:
            raise ValueError("Detector must be trained before transform. Call fit() first.")

        # Build zone windows for state detection
        zone_windows = defaultdict(list)

        for record in records:
            zone_id = record['zone_id']
            timestamp = parse_timestamp(record['timestamp'])

            window_start = timestamp.replace(
                minute=(timestamp.minute // self.window_minutes) * self.window_minutes,
                second=0,
                microsecond=0
            )

            window_key = (zone_id, window_start)
            zone_windows[window_key].append(record)

        # Detect states and apply adjustments
        sorted_windows = sorted(zone_windows.keys())
        adjusted_records = []

        for i, window_key in enumerate(sorted_windows):
            zone_id, window_time = window_key
            current_records = zone_windows[window_key]

            avg_current_count = sum(r['objectCount'] for r in current_records) / len(current_records)

            # Find previous window
            previous_count = None
            for j in range(i - 1, -1, -1):
                prev_zone, prev_time = sorted_windows[j]
                if prev_zone == zone_id:
                    prev_records = zone_windows[sorted_windows[j]]
                    previous_count = sum(r['objectCount'] for r in prev_records) / len(prev_records)
                    break

            state = 'stable' if previous_count is None else self._classify_queue_state(avg_current_count, previous_count)

            # Apply adjustments to all records in this window
            for record in current_records:
                adjusted = {**record, 'queue_state': state}

                for alg in self.algorithms:
                    factor = self.growth_factors[state][alg]
                    adjusted_key = f"{alg}_qg_adjusted"
                    adjusted[adjusted_key] = round(record[alg] * factor)

                adjusted_records.append(adjusted)

        return adjusted_records

    def save(self, filepath):
        """Save trained factors to JSON"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained detector")

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'window_minutes': self.window_minutes,
                'growth_factors': self.growth_factors,
                'growth_stats': self.growth_stats
            }, f, indent=2, ensure_ascii=False)

    def load(self, filepath):
        """Load trained factors from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.window_minutes = data['window_minutes']
        self.window_seconds = self.window_minutes * 60
        self.growth_factors = data['growth_factors']
        self.growth_stats = data['growth_stats']
        self.is_trained = True
