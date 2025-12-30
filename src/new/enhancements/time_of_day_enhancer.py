#!/usr/bin/env python3
"""시간대별 보정 - Time-of-day prediction adjustment using hourly multipliers"""

import json
from collections import defaultdict
from ..utils.time_utils import extract_hour_from_time


class TimeOfDayEnhancer:
    """
    Calculates hourly correction factors based on historical error patterns

    Training Process:
    1. Group records by hour (0-23)
    2. Calculate mean error ratio per hour: actualPassTime / prediction
    3. Smooth factors to avoid overfitting
    4. Store as multipliers for each hour

    Inference Process:
    1. Extract hour from timestamp
    2. Multiply prediction by hour-specific factor
    3. Round result
    """

    def __init__(self):
        self.hourly_factors = {}  # {algorithm: {hour: factor}}
        self.hourly_stats = {}    # {hour: {record_count, avg_error, ...}}
        self.algorithms = ['lidarEstTime', 'throughputEstTime', 'finalEstTime']
        self.is_trained = False

    def fit(self, records, min_samples_per_hour=10, smoothing_factor=0.3):
        """
        Train time-of-day adjustment factors

        Args:
            records: List of data records with predictions and actuals
            min_samples_per_hour: Minimum records needed per hour (default: 10)
            smoothing_factor: Blend with global average (0=full smoothing, 1=no smoothing)

        Returns:
            dict: Training statistics
        """
        # Group records by hour
        hourly_data = defaultdict(lambda: {alg: [] for alg in self.algorithms})
        hourly_actuals = defaultdict(list)

        for record in records:
            # Extract hour from inTime (entry time is most relevant)
            hour = extract_hour_from_time(record.get('inTime', record['timestamp'].split()[1]))

            hourly_actuals[hour].append(record['actualPassTime'])

            for alg in self.algorithms:
                if record[alg] > 0:  # Avoid division by zero
                    error_ratio = record['actualPassTime'] / record[alg]
                    hourly_data[hour][alg].append(error_ratio)

        # Calculate global average ratio as baseline
        global_ratios = {
            alg: (sum(sum(hourly_data[h][alg]) for h in range(24)) /
                  sum(len(hourly_data[h][alg]) for h in range(24)))
            for alg in self.algorithms
        }

        # Calculate hourly factors
        for alg in self.algorithms:
            self.hourly_factors[alg] = {}

            for hour in range(24):
                ratios = hourly_data[hour][alg]

                if len(ratios) >= min_samples_per_hour:
                    mean_ratio = sum(ratios) / len(ratios)
                    # Smooth with global average to avoid overfitting
                    adjusted_factor = (smoothing_factor * mean_ratio +
                                      (1 - smoothing_factor) * global_ratios[alg])
                else:
                    # Not enough data - use global average
                    adjusted_factor = global_ratios[alg]

                self.hourly_factors[alg][hour] = adjusted_factor

        # Calculate statistics
        self.hourly_stats = {
            hour: {
                'record_count': len(hourly_actuals[hour]),
                'avg_actual_time': (sum(hourly_actuals[hour]) / len(hourly_actuals[hour])
                                   if hourly_actuals[hour] else 0),
                'factors': {alg: self.hourly_factors[alg].get(hour, 1.0)
                           for alg in self.algorithms}
            }
            for hour in range(24)
        }

        self.is_trained = True

        return {
            'total_records': len(records),
            'hours_with_data': len([h for h in range(24) if hourly_actuals[h]]),
            'global_ratios': global_ratios,
            'hourly_stats': self.hourly_stats
        }

    def transform(self, records):
        """
        Apply time-of-day adjustments to predictions

        Args:
            records: List of data records with predictions

        Returns:
            list: Records with added fields: lidar_tod_adjusted, throughput_tod_adjusted, final_tod_adjusted
        """
        if not self.is_trained:
            raise ValueError("Enhancer must be trained before transform. Call fit() first.")

        adjusted_records = []

        for record in records:
            hour = extract_hour_from_time(record.get('inTime', record['timestamp'].split()[1]))

            adjusted = {**record}  # Copy all existing fields

            for alg in self.algorithms:
                factor = self.hourly_factors[alg].get(hour, 1.0)
                adjusted_key = f"{alg}_tod_adjusted"
                adjusted[adjusted_key] = round(record[alg] * factor)

            adjusted_records.append(adjusted)

        return adjusted_records

    def save(self, filepath):
        """Save trained factors to JSON"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained enhancer")

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'hourly_factors': self.hourly_factors,
                'hourly_stats': self.hourly_stats
            }, f, indent=2, ensure_ascii=False)

    def load(self, filepath):
        """Load trained factors from JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.hourly_factors = data['hourly_factors']
        self.hourly_stats = data['hourly_stats']
        self.is_trained = True
