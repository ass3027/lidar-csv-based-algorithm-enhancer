"""
Airport Wait Time Prediction Algorithm Enhancement
Optimizes parameters for the HybridWaitTimeCalculator algorithm
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Tuple, List
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize, differential_evolution
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class HybridWaitTimeCalculator:
    """Python implementation of the Java HybridWaitTimeCalculator"""

    def __init__(self, zone_id: int, base_reliability: float = 0.25,
                 estimate_scale: float = 0.45, reliability_weights: Tuple[float, float] = (0.6, 0.4),
                 reliability_bounds: Tuple[float, float] = (0.1, 0.95)):
        self.zone_id = zone_id
        self.base_reliability = base_reliability
        self.estimate_scale = estimate_scale
        self.reliability_weight_base = reliability_weights[0]
        self.reliability_weight_stability = reliability_weights[1]
        self.reliability_min = reliability_bounds[0]
        self.reliability_max = reliability_bounds[1]

    def apply_estimate_scale(self, raw_estimate_seconds: float) -> float:
        """Apply zone-specific scale to LiDAR estimate"""
        minutes = raw_estimate_seconds / 60.0
        return max(0, np.ceil(minutes * self.estimate_scale) * 60)

    def calculate_reliability(self, throughput_per_minute: float,
                            average_wait_count: float) -> float:
        """Calculate reliability factor combining base reliability and stability"""
        if average_wait_count > 0:
            stability = min(1.0, throughput_per_minute / max(average_wait_count, 0.0001))
        else:
            stability = 0.5

        reliability = (self.base_reliability * self.reliability_weight_base +
                      stability * self.reliability_weight_stability)

        return min(self.reliability_max, max(self.reliability_min, reliability))

    def calculate(self, lidar_est_time: float, throughput_est_time: float,
                 object_count: int, throughput_per_minute: float = 0.0,
                 average_wait_count: float = None) -> float:
        """Calculate hybrid wait time prediction"""
        scaled_estimate = self.apply_estimate_scale(lidar_est_time)

        # Special case for Zone 14 (not applicable for Zone 1, but keeping for completeness)
        if self.zone_id == 14 and object_count > 0 and scaled_estimate == 0:
            scaled_estimate = 60

        # Use throughput estimate if available, otherwise use scaled LiDAR estimate
        if throughput_est_time > 0:
            throughput_seconds = throughput_est_time
        else:
            throughput_seconds = scaled_estimate

        # Calculate reliability
        if average_wait_count is None:
            average_wait_count = object_count

        reliability = self.calculate_reliability(throughput_per_minute, average_wait_count)

        # Hybrid calculation
        hybrid_seconds = (reliability * scaled_estimate +
                         (1 - reliability) * throughput_seconds)

        return max(0, np.ceil(hybrid_seconds))


class DataLoader:
    """Load and preprocess CSV data"""

    def __init__(self, csv_folder: str = "./csv"):
        self.csv_folder = Path(csv_folder)

    def load_all_data(self) -> pd.DataFrame:
        """Load all CSV files and concatenate"""
        csv_files = list(self.csv_folder.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.csv_folder}")

        print(f"Loading {len(csv_files)} CSV files...")
        dfs = []
        for file in csv_files:
            df = pd.read_csv(file)
            dfs.append(df)
            print(f"  - {file.name}: {len(df)} records")

        combined = pd.concat(dfs, ignore_index=True)
        combined['timestamp'] = pd.to_datetime(combined['timestamp'])
        combined = combined.sort_values('timestamp').reset_index(drop=True)

        print(f"\nTotal records loaded: {len(combined)}")
        return combined

    def filter_zone(self, df: pd.DataFrame, zone_id: int) -> pd.DataFrame:
        """Filter data for specific zone"""
        filtered = df[df['zone_id'] == zone_id].copy()
        print(f"Zone {zone_id} records: {len(filtered)}")
        return filtered

    def apply_anomaly_filter(self, df: pd.DataFrame, window_minutes: int = 5,
                            threshold: float = 0.7) -> Tuple[pd.DataFrame, Dict]:
        """
        Filter anomalies based on 5-minute rolling average
        Skip records where actualPassTime is more than ±70% from rolling average
        """
        print(f"\nApplying anomaly filter (±{threshold*100}% from {window_minutes}-min rolling avg)...")

        df = df.copy()
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Calculate rolling average with minimum periods
        rolling_window = f'{window_minutes}T'  # T = minutes
        df['rolling_avg'] = df.set_index('timestamp')['actualPassTime'].rolling(
            rolling_window, min_periods=1).mean().values

        # Calculate deviation
        df['deviation'] = abs(df['actualPassTime'] - df['rolling_avg'])
        df['threshold'] = threshold * df['rolling_avg']

        # Filter: keep records within threshold
        original_count = len(df)
        df_filtered = df[df['deviation'] <= df['threshold']].copy()
        filtered_count = len(df_filtered)
        removed_count = original_count - filtered_count

        # Statistics
        stats = {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'removed_count': removed_count,
            'removed_percentage': (removed_count / original_count) * 100 if original_count > 0 else 0,
            'original_mean': df['actualPassTime'].mean(),
            'filtered_mean': df_filtered['actualPassTime'].mean(),
            'original_std': df['actualPassTime'].std(),
            'filtered_std': df_filtered['actualPassTime'].std()
        }

        print(f"  Original records: {original_count}")
        print(f"  Filtered records: {filtered_count}")
        print(f"  Removed records: {removed_count} ({stats['removed_percentage']:.2f}%)")
        print(f"  Mean actualPassTime: {stats['original_mean']:.1f}s → {stats['filtered_mean']:.1f}s")
        print(f"  Std actualPassTime: {stats['original_std']:.1f}s → {stats['filtered_std']:.1f}s")

        # Drop temporary columns
        df_filtered = df_filtered.drop(['rolling_avg', 'deviation', 'threshold'], axis=1)

        return df_filtered, stats


class AlgorithmEvaluator:
    """Evaluate algorithm performance"""

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """Calculate performance metrics"""
        errors = y_pred - y_true
        abs_errors = np.abs(errors)

        # Basic metrics
        mae = np.mean(abs_errors)
        rmse = np.sqrt(np.mean(errors ** 2))
        mape = np.mean(np.abs(errors / np.maximum(y_true, 1))) * 100  # Avoid division by zero

        # Conservative prediction metrics
        over_predictions = np.sum(y_pred >= y_true)
        over_prediction_rate = (over_predictions / len(y_true)) * 100

        # Error distribution
        median_error = np.median(errors)
        error_std = np.std(errors)

        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'over_prediction_rate': over_prediction_rate,
            'median_error': median_error,
            'error_std': error_std,
            'mean_actual': np.mean(y_true),
            'mean_predicted': np.mean(y_pred)
        }

    @staticmethod
    def evaluate_current_algorithm(df: pd.DataFrame) -> Dict:
        """Evaluate current algorithm (finalEstTime)"""
        y_true = df['actualPassTime'].values
        y_pred = df['finalEstTime'].values

        print("\n=== Current Algorithm Performance ===")
        metrics = AlgorithmEvaluator.calculate_metrics(y_true, y_pred)

        print(f"MAE: {metrics['mae']:.2f} seconds")
        print(f"RMSE: {metrics['rmse']:.2f} seconds")
        print(f"MAPE: {metrics['mape']:.2f}%")
        print(f"Over-prediction rate: {metrics['over_prediction_rate']:.2f}%")
        print(f"Mean actual: {metrics['mean_actual']:.2f}s")
        print(f"Mean predicted: {metrics['mean_predicted']:.2f}s")

        return metrics


class ParameterOptimizer:
    """Optimize algorithm parameters"""

    def __init__(self, zone_id: int, target_over_prediction_rate: float = 90.0):
        self.zone_id = zone_id
        self.target_over_prediction_rate = target_over_prediction_rate

    def objective_function(self, params: np.ndarray, X: np.ndarray,
                          y_true: np.ndarray, return_details: bool = False):
        """
        Objective function to minimize
        params: [base_reliability, estimate_scale, weight_base, reliability_min, reliability_max]
        """
        base_reliability = params[0]
        estimate_scale = params[1]
        weight_base = params[2]
        weight_stability = 1.0 - weight_base
        reliability_min = params[3]
        reliability_max = params[4]

        # Create calculator with these parameters
        calc = HybridWaitTimeCalculator(
            zone_id=self.zone_id,
            base_reliability=base_reliability,
            estimate_scale=estimate_scale,
            reliability_weights=(weight_base, weight_stability),
            reliability_bounds=(reliability_min, reliability_max)
        )

        # Make predictions
        y_pred = np.array([
            calc.calculate(
                lidar_est_time=row[0],
                throughput_est_time=row[1],
                object_count=int(row[2])
            )
            for row in X
        ])

        # Calculate metrics
        mae = np.mean(np.abs(y_pred - y_true))
        rmse = np.sqrt(np.mean((y_pred - y_true) ** 2))

        # Conservative prediction constraint
        over_predictions = np.sum(y_pred >= y_true)
        over_prediction_rate = (over_predictions / len(y_true)) * 100

        # Penalty for not meeting 90% threshold
        if over_prediction_rate < self.target_over_prediction_rate:
            constraint_penalty = (self.target_over_prediction_rate - over_prediction_rate) * 100
        else:
            constraint_penalty = 0

        # Penalty for over-conservative predictions (efficiency)
        over_estimate_mean = np.mean(np.maximum(0, y_pred - y_true))
        efficiency_penalty = over_estimate_mean * 0.1  # Weight for efficiency

        # Combined objective
        objective = mae + constraint_penalty + efficiency_penalty

        if return_details:
            return {
                'objective': objective,
                'mae': mae,
                'rmse': rmse,
                'over_prediction_rate': over_prediction_rate,
                'constraint_penalty': constraint_penalty,
                'efficiency_penalty': efficiency_penalty
            }

        return objective

    def optimize(self, X_train: np.ndarray, y_train: np.ndarray,
                X_val: np.ndarray, y_val: np.ndarray) -> Dict:
        """
        Optimize parameters using differential evolution
        Returns best parameters and performance metrics
        """
        print("\n=== Starting Parameter Optimization ===")
        print(f"Target: {self.target_over_prediction_rate}% over-prediction rate")

        # Parameter bounds
        # [base_reliability, estimate_scale, weight_base, reliability_min, reliability_max]
        bounds = [
            (0.0, 1.0),    # base_reliability
            (0.1, 2.0),    # estimate_scale
            (0.0, 1.0),    # weight_base
            (0.05, 0.5),   # reliability_min
            (0.5, 1.0)     # reliability_max
        ]

        print("Optimizing on training data...")
        result = differential_evolution(
            func=lambda params: self.objective_function(params, X_train, y_train),
            bounds=bounds,
            strategy='best1bin',
            maxiter=100,
            popsize=15,
            tol=0.01,
            mutation=(0.5, 1.0),
            recombination=0.7,
            seed=42,
            workers=1,
            disp=True
        )

        best_params = result.x
        print(f"\nOptimization complete!")
        print(f"Best parameters found:")
        print(f"  base_reliability: {best_params[0]:.4f}")
        print(f"  estimate_scale: {best_params[1]:.4f}")
        print(f"  weight_base: {best_params[2]:.4f} (weight_stability: {1-best_params[2]:.4f})")
        print(f"  reliability_min: {best_params[3]:.4f}")
        print(f"  reliability_max: {best_params[4]:.4f}")

        # Evaluate on training data
        train_details = self.objective_function(best_params, X_train, y_train, return_details=True)
        print(f"\nTraining performance:")
        print(f"  MAE: {train_details['mae']:.2f}s")
        print(f"  RMSE: {train_details['rmse']:.2f}s")
        print(f"  Over-prediction rate: {train_details['over_prediction_rate']:.2f}%")

        # Evaluate on validation data
        val_details = self.objective_function(best_params, X_val, y_val, return_details=True)
        print(f"\nValidation performance:")
        print(f"  MAE: {val_details['mae']:.2f}s")
        print(f"  RMSE: {val_details['rmse']:.2f}s")
        print(f"  Over-prediction rate: {val_details['over_prediction_rate']:.2f}%")

        return {
            'params': {
                'base_reliability': float(best_params[0]),
                'estimate_scale': float(best_params[1]),
                'weight_base': float(best_params[2]),
                'weight_stability': float(1 - best_params[2]),
                'reliability_min': float(best_params[3]),
                'reliability_max': float(best_params[4])
            },
            'train_metrics': train_details,
            'val_metrics': val_details
        }


class Visualizer:
    """Create visualizations for results"""

    @staticmethod
    def plot_error_distribution(y_true: np.ndarray, y_pred_current: np.ndarray,
                               y_pred_optimized: np.ndarray, output_path: str):
        """Plot error distribution comparison"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        errors_current = y_pred_current - y_true
        errors_optimized = y_pred_optimized - y_true

        # Current algorithm
        axes[0].hist(errors_current, bins=50, alpha=0.7, color='blue', edgecolor='black')
        axes[0].axvline(0, color='red', linestyle='--', linewidth=2, label='Perfect prediction')
        axes[0].set_xlabel('Error (Predicted - Actual) [seconds]')
        axes[0].set_ylabel('Frequency')
        axes[0].set_title('Current Algorithm Error Distribution')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Optimized algorithm
        axes[1].hist(errors_optimized, bins=50, alpha=0.7, color='green', edgecolor='black')
        axes[1].axvline(0, color='red', linestyle='--', linewidth=2, label='Perfect prediction')
        axes[1].set_xlabel('Error (Predicted - Actual) [seconds]')
        axes[1].set_ylabel('Frequency')
        axes[1].set_title('Optimized Algorithm Error Distribution')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

    @staticmethod
    def plot_prediction_scatter(y_true: np.ndarray, y_pred_current: np.ndarray,
                               y_pred_optimized: np.ndarray, output_path: str):
        """Plot prediction scatter plots"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        max_val = max(y_true.max(), y_pred_current.max(), y_pred_optimized.max())

        # Current algorithm
        axes[0].scatter(y_true, y_pred_current, alpha=0.3, s=10)
        axes[0].plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect prediction')
        axes[0].set_xlabel('Actual Wait Time [seconds]')
        axes[0].set_ylabel('Predicted Wait Time [seconds]')
        axes[0].set_title('Current Algorithm')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Optimized algorithm
        axes[1].scatter(y_true, y_pred_optimized, alpha=0.3, s=10, color='green')
        axes[1].plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect prediction')
        axes[1].set_xlabel('Actual Wait Time [seconds]')
        axes[1].set_ylabel('Predicted Wait Time [seconds]')
        axes[1].set_title('Optimized Algorithm')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()

    @staticmethod
    def plot_time_series(df: pd.DataFrame, output_path: str, sample_hours: int = 4):
        """Plot time series of predictions vs actual"""
        # Sample a few hours of data
        df_sample = df.iloc[:sample_hours * 60].copy()  # Assuming ~1 record per minute

        plt.figure(figsize=(14, 6))
        plt.plot(df_sample['timestamp'], df_sample['actualPassTime'],
                label='Actual', linewidth=1.5, alpha=0.7)
        plt.plot(df_sample['timestamp'], df_sample['finalEstTime'],
                label='Current Prediction', linewidth=1.5, alpha=0.7)
        plt.xlabel('Time')
        plt.ylabel('Wait Time [seconds]')
        plt.title(f'Wait Time Predictions vs Actual (First {sample_hours} hours)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
        plt.close()


def main():
    """Main execution pipeline"""
    print("="*70)
    print("Airport Wait Time Algorithm Enhancement - Zone 1")
    print("="*70)

    # 1. Load data
    loader = DataLoader(csv_folder="./csv")
    df_all = loader.load_all_data()

    # 2. Filter to Zone 1
    df_zone1 = loader.filter_zone(df_all, zone_id=1)

    # 3. Apply anomaly filtering
    df_clean, filter_stats = loader.apply_anomaly_filter(df_zone1, window_minutes=5, threshold=0.7)

    # 4. Evaluate current algorithm
    evaluator = AlgorithmEvaluator()
    current_metrics = evaluator.evaluate_current_algorithm(df_clean)

    # 5. Prepare data for optimization
    print("\n=== Preparing data for optimization ===")
    X = df_clean[['lidarEstTime', 'throughputEstTime', 'objectCount']].values
    y = df_clean['actualPassTime'].values

    # Split data: 70% train, 15% validation, 15% test
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176, random_state=42)  # 0.176 * 0.85 ≈ 0.15

    print(f"Train set: {len(X_train)} records")
    print(f"Validation set: {len(X_val)} records")
    print(f"Test set: {len(X_test)} records")

    # 6. Optimize parameters
    optimizer = ParameterOptimizer(zone_id=1, target_over_prediction_rate=90.0)
    optimization_results = optimizer.optimize(X_train, y_train, X_val, y_val)

    # 7. Evaluate on test set
    print("\n=== Test Set Evaluation ===")
    best_params = optimization_results['params']
    calc_optimized = HybridWaitTimeCalculator(
        zone_id=1,
        base_reliability=best_params['base_reliability'],
        estimate_scale=best_params['estimate_scale'],
        reliability_weights=(best_params['weight_base'], best_params['weight_stability']),
        reliability_bounds=(best_params['reliability_min'], best_params['reliability_max'])
    )

    y_pred_optimized = np.array([
        calc_optimized.calculate(
            lidar_est_time=row[0],
            throughput_est_time=row[1],
            object_count=int(row[2])
        )
        for row in X_test
    ])

    test_metrics = evaluator.calculate_metrics(y_test, y_pred_optimized)
    print(f"MAE: {test_metrics['mae']:.2f}s")
    print(f"RMSE: {test_metrics['rmse']:.2f}s")
    print(f"MAPE: {test_metrics['mape']:.2f}%")
    print(f"Over-prediction rate: {test_metrics['over_prediction_rate']:.2f}%")

    # 8. Create visualizations
    print("\n=== Generating visualizations ===")
    visualizer = Visualizer()

    # Get current predictions for test set
    y_pred_current_test = df_clean.loc[X_test[:, 0].astype(int), 'finalEstTime'].values

    visualizer.plot_error_distribution(y_test, y_pred_current_test, y_pred_optimized,
                                      'error_distribution.png')
    visualizer.plot_prediction_scatter(y_test, y_pred_current_test, y_pred_optimized,
                                      'prediction_scatter.png')
    visualizer.plot_time_series(df_clean, 'time_series_sample.png', sample_hours=4)

    # 9. Save results
    print("\n=== Saving results ===")

    # Save optimized parameters
    params_output = {
        'zone_id': 1,
        'zone_type': 'IDENTITY_MANNED',
        'parameters': best_params,
        'current_parameters': {
            'base_reliability': 0.25,
            'estimate_scale': 0.45,
            'weight_base': 0.6,
            'weight_stability': 0.4,
            'reliability_min': 0.1,
            'reliability_max': 0.95
        }
    }

    with open('optimized_parameters.json', 'w') as f:
        json.dump(params_output, f, indent=2)
    print("Saved: optimized_parameters.json")

    # Save comprehensive results
    results_data = {
        'data_quality': filter_stats,
        'current_algorithm': current_metrics,
        'optimized_algorithm': {
            'train': optimization_results['train_metrics'],
            'validation': optimization_results['val_metrics'],
            'test': test_metrics
        },
        'parameters': params_output
    }

    with open('results_data.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    print("Saved: results_data.json")

    print("\n" + "="*70)
    print("Optimization Complete!")
    print("="*70)

    return results_data


if __name__ == "__main__":
    main()
