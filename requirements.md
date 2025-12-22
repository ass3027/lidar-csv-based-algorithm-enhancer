# Airport Wait Time Prediction Algorithm Enhancement

## Project Overview

This project aims to optimize the hybrid wait time prediction algorithm for airport departure processing zones (identity verification and security checkpoints) at Gimpo Airport.

## Current Algorithm

### Location
`D:\project\gimpo-airport\source_code\LiDAR-Web\src\main\java\lidar\app\lidar_data\HybridWaitTimeCalculator.java`

### Algorithm Description

The current implementation uses a **hybrid weighted approach** combining two estimation methods:

```
hybridWaitTime = reliability × lidarEstimate + (1 - reliability) × throughputEstimate
```

#### Input Variables

| Variable | Description | Unit | Source |
|----------|-------------|------|--------|
| `zoneId` | Zone identifier (1-14) | integer | Zone configuration |
| `objectCount` | Number of waiting people | count | LiDAR detection |
| `lidarEstTime` | Average wait time from LiDAR tracking | seconds | LiDAR system (5-min avg) |
| `throughputEstTime` | Wait time based on throughput | seconds | Calculated: `waitCount / throughputPerMin × 60` |
| `actualPassTime` | Ground truth wait time | seconds | LiDAR sensor measurement (target variable) |

#### LiDAR Estimate Calculation

- Raw LiDAR estimate is scaled per zone using `ESTIMATE_SCALE_OVERRIDES`
- Formula: `scaledEstimate = ceil((rawEstimate / 60) × scale) × 60`
- Current scale factors range: 0.35 - 0.80 (zone-dependent)

#### Throughput Estimate Calculation

- Based on recent processing throughput (5-minute window)
- Formula: `throughputEstTime = ceil((waitCount / throughputPerMin) × 60)`
- Falls back to lidarEstimate if throughput is unavailable

#### Reliability Calculation

The reliability factor determines how much to trust the LiDAR estimate vs throughput estimate:

```
reliability = min(0.95, max(0.1, (baseReliability × 0.6) + (stability × 0.4)))
```

Where:
- `baseReliability`: Zone-specific constant (0.25 - 0.70)
- `stability`: `min(1.0, throughputPerMin / averageWaitCount)`

### Current Zone-Specific Parameters

#### Base Reliability Values

| Zone Type | Zone IDs | Base Reliability | Logic |
|-----------|----------|------------------|-------|
| Identity (Manned) | 1 | 0.25 | Lower trust in LiDAR |
| Identity (Priority) | 2 | 0.60 | Higher trust in LiDAR |
| Identity (Bio) | 3 | 0.40 | Medium trust in LiDAR |
| Security Checkpoints | 4-14 | 0.55 | Standard security zones |

#### Estimate Scale Values

| Zone Type | Zone IDs | Scale Factor | Effect |
|-----------|----------|--------------|--------|
| Identity (Manned) | 1 | 0.45 | Reduce LiDAR estimate to 45% |
| Identity (Priority) | 2 | 0.70 | Reduce LiDAR estimate to 70% |
| Identity (Bio) | 3 | 0.35 | Reduce LiDAR estimate to 35% |
| Security Checkpoints | 4-14 | 0.80 | Reduce LiDAR estimate to 80% |

#### Reliability Combination Weights

- Base reliability contribution: **60%**
- Stability factor contribution: **40%**
- Final reliability clamped: **0.1 - 0.95**

## Dataset

### Data Source
CSV files in `./csv/` directory containing historical predictions and actual wait times.

### Data Schema

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | datetime | Record timestamp |
| `zone_id` | integer | Zone identifier (1-14) |
| `objectCount` | integer | Number of waiting people |
| `lidarEstTime` | integer | LiDAR-based estimate (seconds) |
| `throughputEstTime` | float | Throughput-based estimate (seconds) |
| `finalEstTime` | integer | Current hybrid algorithm output (seconds) |
| `actualPassTime` | integer | Actual measured wait time from LiDAR sensor (seconds) |

### Dataset Statistics
- Total records: ~57,887
- Date range: 2025-11-28 to 2025-12-01
- Files: 4 daily CSV files

### Data Characteristics
- `throughputEstTime` is often 0.00 when throughput data is unavailable
- Multiple zones with different operational characteristics
- Temporal patterns across different times of day
- `actualPassTime` is measured by LiDAR sensor and may contain anomalies

### Data Quality & Cleaning Rules

**IMPORTANT: Anomaly Detection and Filtering**

Since `actualPassTime` is measured by LiDAR sensors, anomalous readings can occur due to:
- Sensor errors or occlusions
- Misidentified objects
- Edge cases in tracking algorithms

**Filtering Rule**:
- **Skip records where `actualPassTime` deviates more than ±70% from the 5-minute rolling average**
- Calculate 5-minute rolling average per zone separately
- Formula: Keep record only if `|actualPassTime - rollingAvg5min| ≤ 0.7 × rollingAvg5min`
- Apply this filter before splitting data into train/validation/test sets

This ensures the optimization is based on reliable ground truth data.

## Optimization Objectives

### Primary Goal
**Optimize existing algorithm parameters to improve prediction accuracy while maintaining conservative estimates.**

### Success Criteria

1. **Conservative Prediction Target**:
   - **90% of predictions should be ≥ actual wait time**
   - Better to over-estimate than under-estimate (passenger safety margin)

2. **Accuracy Metrics** (to be minimized):
   - Mean Absolute Error (MAE)
   - Root Mean Squared Error (RMSE)
   - Mean Absolute Percentage Error (MAPE)

3. **Per-Zone Performance**:
   - Each zone should meet the 90% threshold
   - Zone-specific parameters should be optimized individually

### Constraints

- Maintain interpretability of existing algorithm structure
- No computation time constraints (for now)
- Future consideration: temporal patterns, ML approaches

## Optimization Scope

### Initial Phase: Zone 1 Only
**First run optimization on zoneId=1 (IDENTITY_MANNED) to validate approach**

### Parameters to Optimize

1. **ESTIMATE_SCALE_OVERRIDES** (per zone)
   - Current range: 0.35 - 0.80
   - Optimizable range: 0.1 - 2.0

2. **BASE_RELIABILITY_OVERRIDES** (per zone)
   - Current range: 0.25 - 0.70
   - Optimizable range: 0.0 - 1.0

3. **Reliability Combination Weights**
   - Current: `(baseReliability × 0.6) + (stability × 0.4)`
   - Optimizable: `(baseReliability × w1) + (stability × w2)` where `w1 + w2 = 1`

4. **Reliability Bounds**
   - Current: min=0.1, max=0.95
   - Optimizable: explore different bounds

### Out of Scope (Phase 1)

- Machine learning approaches
- Temporal feature engineering
- Non-linear weighting functions
- Real-time adaptive algorithms

## Deliverables

### 1. Requirements Documentation
- **File**: `requirements.md` (this file)
- Clean, comprehensive project requirements

### 2. Python Optimization Script
- **File**: `algorithm_enhancement.py`
- Functions:
  - Data loading and preprocessing with 5-minute rolling average anomaly filtering
  - Current algorithm performance evaluation
  - Parameter optimization using scipy.optimize or similar
  - Cross-validation and performance metrics
  - Visualization of results

### 3. Results Report
- **File**: `results.md`
- Contents:
  - Data quality analysis (records filtered)
  - Current vs optimized performance comparison for Zone 1
  - Recommended parameters for Zone 1
  - Performance metrics breakdown
  - Visualizations (error distributions, scatter plots)
  - Implementation guidelines for Java integration

### 4. Optimized Parameters
- **File**: `optimized_parameters.json`
- Production-ready parameter values for Java implementation (Zone 1)

## Implementation Notes

### Special Cases in Current Algorithm

1. **Zone 14 Special Handling**:
   ```java
   if (zoneId == 14 && waitCount > 0 && scaledEstimateSeconds == 0) {
       scaledEstimateSeconds = 60;
   }
   ```
   - Assigns 60-second minimum when LiDAR estimate is zero but people are waiting

2. **Throughput Fallback**:
   - When throughput is unavailable (≤0), uses scaled LiDAR estimate

3. **Final Rounding**:
   - Result is ceiling-rounded to nearest integer second
   - Minimum value: 0 seconds

### Optimization Approach

1. **Data Preprocessing**:
   - Load all CSV files
   - Filter to Zone 1 only
   - Calculate 5-minute rolling average of actualPassTime
   - Filter anomalies (±70% from rolling average)
   - Report filtering statistics

2. **Data Split**:
   - Training: 70%
   - Validation: 15%
   - Test: 15%

3. **Optimization Method**:
   - Grid search or Bayesian optimization
   - Objective function: Weighted combination of:
     - Minimize MAE/RMSE
     - Constraint: ≥90% predictions above actual
     - Penalty for over-conservative predictions (efficiency vs safety balance)

4. **Validation**:
   - Performance analysis for Zone 1
   - Temporal validation (different time periods)
   - Sensitivity analysis of parameters

## Zone Types Reference

| Zone ID | Type | Description |
|---------|------|-------------|
| 1 | IDENTITY_MANNED | Manual identity verification |
| 2 | IDENTITY_PRIORITY | Priority passenger identity check |
| 3 | IDENTITY_BIO | Biometric identity verification |
| 4-14 | SECURITY | Security checkpoint zones |

## Next Steps

1. Load and explore dataset (Zone 1 only)
2. Apply 5-minute rolling average anomaly filtering (±70% rule)
3. Evaluate current algorithm performance
4. Implement parameter optimization
5. Generate results and recommendations
6. Extend to other zones after validating approach
