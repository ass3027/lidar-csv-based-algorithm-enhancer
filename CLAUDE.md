# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Python-based data analysis and algorithm optimization project** for Gimpo Airport's wait time prediction system. The goal is to optimize the hybrid wait time prediction algorithm used in airport departure processing zones (identity verification and security checkpoints).

**Source Algorithm Location**: `D:\project\gimpo-airport\source_code\LiDAR-Web\src\main\java\lidar\app\lidar_data\HybridWaitTimeCalculator.java`

## Project Structure

```
csv-based-algorithm-enhancer/
├── csv/                                  # Historical data (CSV format)
│   └── passingObject_YYYYMMDD.csv       # Daily prediction logs
├── legacy/
│   └── algorithm_enhancement.py         # Original optimization implementation
├── analyze_queue_logs_filtered.py       # Log analysis with outlier filtering
├── generate_summary_tables.py           # Summary table generation
├── queue_analysis_results_filtered.json # Analysis results
├── queue_analysis_summary_tables.md     # Human-readable analysis
└── requirements.md                      # Detailed project requirements
```

## Running Scripts

### Data Analysis
```bash
# Analyze queue logs with IQR-based outlier filtering
python analyze_queue_logs_filtered.py

# Generate summary tables (by zone, day, queue size)
python generate_summary_tables.py
```

### Algorithm Optimization (Legacy)
```bash
# Run parameter optimization for Zone 1
python legacy/algorithm_enhancement.py
```

**Note**: The legacy script expects CSV files in `./csv/` directory and produces:
- `optimized_parameters.json` - Optimized parameter values
- `results_data.json` - Performance metrics
- `*.png` - Visualization plots

## Data Schema

### Input CSV Files (`csv/passingObject_*.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | datetime | Record timestamp |
| `zone_id` | integer | Zone identifier (1-17) |
| `objectCount` | integer | Number of waiting people |
| `lidarEstTime` | integer | LiDAR-based estimate (seconds) |
| `throughputEstTime` | float | Throughput-based estimate (seconds) |
| `finalEstTime` | integer | Current hybrid algorithm output (seconds) |
| `actualPassTime` | integer | **Ground truth** - Actual measured wait time (seconds) |

## Algorithm Architecture

The hybrid wait time calculator combines two estimation methods:

```
hybridWaitTime = reliability × lidarEstimate + (1 - reliability) × throughputEstimate
```

### Key Components

1. **LiDAR Estimate Scaling**
   - Zone-specific scale factors (0.35-0.80)
   - Formula: `scaledEstimate = ceil((rawEstimate / 60) × scale) × 60`

2. **Reliability Calculation**
   - Combines base reliability and stability
   - Formula: `reliability = min(0.95, max(0.1, (baseReliability × 0.6) + (stability × 0.4)))`
   - `stability = min(1.0, throughputPerMin / averageWaitCount)`

3. **Optimizable Parameters** (per zone)
   - `ESTIMATE_SCALE_OVERRIDES`: 0.1 - 2.0
   - `BASE_RELIABILITY_OVERRIDES`: 0.0 - 1.0
   - Reliability combination weights: `w1 + w2 = 1`
   - Reliability bounds: `min`, `max`

## Data Quality Rules

### Critical: Anomaly Filtering

Since `actualPassTime` is measured by LiDAR sensors, it may contain anomalies from sensor errors or tracking issues.

**Filtering Rule** (5-minute rolling average):
```python
# Skip records where actualPassTime deviates more than ±70% from rolling average
keep_record = |actualPassTime - rollingAvg5min| ≤ 0.7 × rollingAvg5min
```

**Implementation**: `analyze_queue_logs_filtered.py` uses IQR-based outlier detection on:
- `actualPassTime` values
- Prediction errors for all three estimators (LiDAR, throughput, final)

## Optimization Objectives

### Success Criteria

1. **Conservative Prediction Target** (Primary)
   - **90% of predictions must be ≥ actual wait time**
   - Over-estimation is preferred (passenger safety margin)

2. **Accuracy Metrics** (Secondary - to minimize)
   - Mean Absolute Error (MAE)
   - Root Mean Squared Error (RMSE)
   - Mean Absolute Percentage Error (MAPE)

3. **Per-Zone Performance**
   - Each zone should meet the 90% threshold independently
   - Zone-specific parameters optimized individually

### Initial Optimization Scope

**Phase 1**: Zone 1 only (IDENTITY_MANNED)
- Validate approach before extending to other zones
- Data split: 70% train, 15% validation, 15% test

## Zone Types Reference

| Zone ID | Type | Current Base Reliability | Current Scale Factor |
|---------|------|-------------------------|---------------------|
| 1 | IDENTITY_MANNED | 0.25 | 0.45 |
| 2 | IDENTITY_PRIORITY | 0.60 | 0.70 |
| 3 | IDENTITY_BIO | 0.40 | 0.35 |
| 4-14 | SECURITY | 0.55 | 0.80 |

## Special Algorithm Cases

### Zone 14 Special Handling
```java
if (zoneId == 14 && waitCount > 0 && scaledEstimateSeconds == 0) {
    scaledEstimateSeconds = 60;  // 60-second minimum
}
```

### Throughput Fallback
When `throughputEstTime ≤ 0`, the algorithm falls back to using the scaled LiDAR estimate.

### Final Rounding
All predictions are ceiling-rounded to nearest integer second, with a minimum value of 0.

## Code Implementation Details

### `analyze_queue_logs_filtered.py`
- Loads all CSV files from `csv/` or specified directory
- Applies IQR-based outlier detection (configurable multiplier, default 1.5)
- Produces comprehensive JSON analysis comparing original vs filtered data
- Korean language console output

### `generate_summary_tables.py`
- Creates markdown tables with multi-dimensional analysis:
  - Zone × Day of Week
  - Zone × Queue Size (50-person buckets)
  - Queue Size × Day of Week
  - Sample count distributions
- Korean language output with statistical summaries

### `legacy/algorithm_enhancement.py`
- Python reimplementation of Java `HybridWaitTimeCalculator`
- Uses `scipy.optimize.differential_evolution` for parameter optimization
- Creates matplotlib visualizations (error distributions, scatter plots, time series)
- Requires: pandas, numpy, scipy, sklearn, matplotlib, seaborn

## Coding Standards

### Python Language Features - Use Aggressively

**CRITICAL RULE**: Always leverage advanced Python language features to write concise, idiomatic code.

**Required Patterns**:

1. **Dictionary Comprehensions**
   ```python
   # Good
   result = {key: process(value) for key, value in data.items()}

   # Avoid
   result = {}
   for key, value in data.items():
       result[key] = process(value)
   ```

2. **Dictionary Unpacking (`**dict`)**
   ```python
   # Good
   combined = {**base_dict, 'extra_key': value}

   # Avoid
   combined = base_dict.copy()
   combined['extra_key'] = value
   ```

3. **List/Set Comprehensions**
   ```python
   # Good
   outliers = {i for i, val in enumerate(values) if val > threshold}

   # Avoid
   outliers = set()
   for i, val in enumerate(values):
       if val > threshold:
           outliers.add(i)
   ```

4. **Tuple Unpacking**
   ```python
   # Good
   for name, value in pairs:
       process(name, value)

   # Avoid
   for pair in pairs:
       process(pair[0], pair[1])
   ```

5. **Generator Expressions**
   ```python
   # Good
   total = sum(record['value'] for record in data)

   # Avoid
   values = [record['value'] for record in data]
   total = sum(values)
   ```

6. **f-strings with Expressions**
   ```python
   # Good
   msg = f"Result: {calculate(x):.2f} ({status.upper()})"

   # Avoid
   result = calculate(x)
   msg = "Result: {:.2f} ({})".format(result, status.upper())
   ```

7. **Walrus Operator (`:=`)**
   ```python
   # Good
   if (match := pattern.search(text)):
       process(match)

   # Avoid
   match = pattern.search(text)
   if match:
       process(match)
   ```

8. **defaultdict, Counter, namedtuple**
   ```python
   # Good
   from collections import defaultdict, Counter
   counts = Counter(data)
   groups = defaultdict(list)

   # Avoid
   counts = {}
   for item in data:
       counts[item] = counts.get(item, 0) + 1
   ```

**See Examples**: The `new/` directory demonstrates aggressive Python feature usage throughout all modules.

## Development Notes

### When Modifying Scripts

1. **CSV Loading**: All scripts expect CSV files in `csv/` subdirectory or `passing_log/` directory
2. **Encoding**: Files use UTF-8 encoding (Korean language support)
3. **Date Format**: Timestamps follow `YYYY-MM-DD HH:MM:SS` format
4. **Zone IDs**: Valid range is 1-17 (not all zones may have data)
5. **Python Style**: Follow aggressive Python feature usage guidelines above

### When Adding New Analysis

- Follow the existing pattern of IQR-based outlier removal
- Maintain the 5-minute rolling average window for temporal filtering
- Preserve Korean language output conventions in console messages
- Save results as both JSON (machine-readable) and Markdown (human-readable)

### When Optimizing Parameters

- Always apply anomaly filtering **before** train/val/test split
- Constraint penalty must enforce the 90% over-prediction requirement
- Consider efficiency penalty to avoid overly conservative predictions
- Test on held-out test set to validate generalization

## Integration with Java Codebase

Optimized parameters from this project will be integrated back into:
```
D:\project\gimpo-airport\source_code\LiDAR-Web\src\main\java\lidar\app\lidar_data\HybridWaitTimeCalculator.java
```

Format: Update the `ESTIMATE_SCALE_OVERRIDES` and `BASE_RELIABILITY_OVERRIDES` maps with optimized values from `optimized_parameters.json`.
