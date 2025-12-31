# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Python-based data analysis and algorithm optimization project** for Gimpo Airport's wait time prediction system. The goal is to optimize the hybrid wait time prediction algorithm used in airport departure processing zones (identity verification and security checkpoints).

**Source Algorithm Location**: `D:\project\gimpo-airport\source_code\LiDAR-Web\src\main\java\lidar\app\lidar_data\HybridWaitTimeCalculator.java`

## Project Structure

```
csv-based-algorithm-enhancer/
├── resource/
│   ├── csv/                             # Historical data (CSV format)
│   │   └── passingObject_YYYYMMDD.csv   # Daily prediction logs
│   └── result/                          # Generated analysis reports
│       └── 대기시간_통계분석_*.md        # Analysis markdown reports
├── src/
│   └── new/                             # Main analysis codebase
│       ├── core/                        # Core data processing
│       │   ├── data_loader.py           # CSV loading & two-stage filtering
│       │   ├── analysis_engine.py       # Base analysis engine
│       │   └── enhanced_analysis_engine.py  # Enhanced analysis with ML
│       ├── utils/                       # Utility modules
│       │   ├── outlier_detection.py     # Two-stage outlier filtering
│       │   ├── congestion_utils.py      # Congestion level calculation
│       │   ├── statistics_utils.py      # Statistical functions
│       │   └── time_utils.py            # Time parsing utilities
│       ├── tables/                      # Table generation system
│       │   ├── generators/              # Individual table generators
│       │   │   ├── zone_by_congestion.py  # Zone × Congestion analysis
│       │   │   ├── zone_by_queue.py     # Zone × Queue size analysis
│       │   │   ├── zone_by_day.py       # Zone × Day of week analysis
│       │   │   └── ...
│       │   ├── table_data_loader.py     # Table-specific data loading
│       │   └── table_generators.py      # Table generator registry
│       ├── enhancements/                # ML enhancement modules
│       │   ├── time_of_day_enhancer.py  # Time-based adjustments
│       │   ├── queue_growth_detector.py # Queue growth prediction
│       │   └── adjustment_trainer.py    # ML model training
│       ├── scripts/                     # Analysis scripts
│       │   ├── analyze_with_enhancements.py  # Enhanced analysis
│       │   ├── train_enhancements.py    # Train ML models
│       │   └── test_enhancements.py     # Test ML models
│       ├── generate_tables.py           # Main table generation script
│       └── compare_weekly_analysis.py   # Weekly comparison analysis
└── legacy/
    └── algorithm_enhancement.py         # Original optimization implementation
```

## Running Scripts

### Main Analysis Scripts

```bash
# Generate comprehensive statistical analysis tables
python src/new/generate_tables.py resource/csv

# Generate tables for specific date range
python src/new/generate_tables.py resource/csv --from 20251216 --to 20251221

# Compare weekly trends (requires 3 weeks of data)
python src/new/compare_weekly_analysis.py resource/csv

# Run enhanced analysis with ML adjustments
python src/new/scripts/analyze_with_enhancements.py
```

### ML Enhancement Scripts

```bash
# Train time-of-day and queue growth models
python src/new/scripts/train_enhancements.py

# Test trained enhancement models
python src/new/scripts/test_enhancements.py
```

### Output Files

**Main table generation** (`generate_tables.py`):
- Output: `resource/result/대기시간_통계분석_YYYYMMDD_YYYYMMDD.md`
- Contains: Zone-congestion analysis, queue size analysis, day-of-week trends, sample counts

**Weekly comparison** (`compare_weekly_analysis.py`):
- Output: `resource/result/주차별_비교분석_Week1-2-3.md`
- Contains: Week-over-week trends, filtering statistics, zone performance changes

**Enhanced analysis** (`analyze_with_enhancements.py`):
- Output: JSON analysis with ML-enhanced predictions
- Includes: Time-of-day adjustments, queue growth predictions

## Data Schema

### Input CSV Files (`resource/csv/passingObject_*.csv`)

The system supports **two CSV formats** and auto-detects which format is present:

#### Format 1: Old Format (with header)
```csv
timestamp,zone_id,objectCount,lidarEstTime,throughputEstTime,finalEstTime,actualPassTime
2025-12-20 09:15:00,1,25,180.0,150.5,165,120
```

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | datetime | Record timestamp (YYYY-MM-DD HH:MM:SS) |
| `zone_id` | integer | Zone identifier (1-17) |
| `objectCount` | integer | Number of waiting people |
| `lidarEstTime` | float | LiDAR-based estimate (seconds) |
| `throughputEstTime` | float | Throughput-based estimate (seconds) |
| `finalEstTime` | float | Current hybrid algorithm output (seconds) |
| `actualPassTime` | integer | **Ground truth** - Actual measured wait time (seconds) |

#### Format 2: New Format (no header, 10 columns)
```csv
2025-12-20 09:15:00,12345,1,25,09:15:00,09:17:00,02:00,180.0,150.5,165
```

| Column Position | Name | Type | Description |
|----------------|------|------|-------------|
| 0 | `timestamp` | datetime | Event timestamp (YYYY-MM-DD HH:MM:SS) |
| 1 | `objectId` | integer | Object/Person identifier |
| 2 | `zoneId` | integer | Zone identifier (1-17) |
| 3 | `zoneObjectCount` | integer | Number of objects in zone |
| 4 | `inTime` | time | Entry time (HH:MM:SS) |
| 5 | `outTime` | time | Exit time (HH:MM:SS) |
| 6 | `actualPassTime` | time | Duration (MM:SS or HH:MM:SS format) |
| 7 | `lidarEstTime` | float | LiDAR estimate (seconds) |
| 8 | `throughputEstTime` | float | Throughput estimate (seconds) |
| 9 | `finalEstTime` | float | Final estimate (seconds) |

**Auto-detection**: The loader checks if the first row starts with "timestamp" to determine format.

**Added fields** (during parsing):
- `congestion_level` - Calculated from `objectCount` using zone-specific thresholds
  - Identity zones (1-4): Low (≤40), Medium (41-80), High (81-140), Very High (>140)
  - Security zones (5-17): Low (≤5), Medium (6-11), High (12-16), Very High (>16)

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

### Two-Stage Outlier Filtering

Since `actualPassTime` is measured by LiDAR sensors, it may contain anomalies from sensor errors or tracking issues.

**Implementation**: `src/new/utils/outlier_detection.py` and `src/new/core/data_loader.py`

#### Stage 1: Zone-Congestion Hard Bounds

Domain knowledge-based filtering with different thresholds per zone group and congestion level:

**Zone 1-4 (Identity zones):**
- Low: 0 < actualPassTime < 8 minutes
- Medium: 4 < actualPassTime < 15 minutes
- High: 6 < actualPassTime < 30 minutes
- Very High: 8 < actualPassTime < 40 minutes

**Zone 5-17 (Security zones):**
- Low: 0 < actualPassTime < 8 minutes
- Medium: 2 < actualPassTime < 15 minutes
- High: 3 < actualPassTime < 20 minutes
- Very High: 4 < actualPassTime < 30 minutes

#### Stage 2: Adaptive Statistical Filtering

Per-(zone_id, congestion_level) group statistical filtering:

- **Grouping**: Up to 68 groups (17 zones × 4 congestion levels)
- **Filtering range**: 30%-170% of group mean actualPassTime
- **Minimum samples**: Groups with < 10 samples skip adaptive filtering
- **Calculation**: For each group, remove values outside `[0.3×mean, 1.7×mean]`

**Key Functions:**
- `filter_outliers()` - Main two-stage filtering pipeline
- `check_hard_bounds()` - Stage 1 validation
- `compute_group_statistics()` - Stage 2 statistics calculation
- `build_outlier_statistics()` - Comprehensive filtering report generation

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

### Core Modules

#### `src/new/core/data_loader.py`
- Loads CSV files supporting both old and new formats
- Implements two-stage outlier filtering (hard bounds + adaptive)
- Auto-detects CSV format (with/without headers)
- Adds `congestion_level` field during parsing
- Supports date range filtering (`--from`, `--to` parameters)

#### `src/new/core/analysis_engine.py`
- Base analysis engine for error calculations
- Computes MAE, RMSE, MAPE metrics
- Zone-level and overall performance statistics
- Korean language output support

#### `src/new/core/enhanced_analysis_engine.py`
- Extends base engine with ML enhancements
- Integrates time-of-day and queue growth adjustments
- Provides enhanced prediction analysis

### Table Generation System

#### `src/new/tables/generators/`
Modular table generators following Single Responsibility Principle:

- **`zone_by_congestion.py`** - Zone × Congestion level analysis with min/max ranges
- **`zone_by_queue.py`** - Zone × Queue size (50-person buckets)
- **`zone_by_day.py`** - Zone × Day of week
- **`queue_by_day.py`** - Queue size × Day of week
- **`sample_count.py`** - Sample count distributions
- **`summary_statistics.py`** - Overall statistical summary

Each generator uses the **Table Unit Pattern**:
- `_aggregate_data()` - Data collection
- `_generate_*_table()` - Table generation
- `_generate_*_insights()` - Insight generation

#### `src/new/generate_tables.py`
- Main entry point for table generation
- Orchestrates all table generators
- Generates comprehensive markdown report with:
  - Two-stage filtering summary
  - Zone-congestion analysis
  - Queue size analysis
  - Day-of-week trends
  - Sample distributions

#### `src/new/compare_weekly_analysis.py`
- Compares 3 weeks of data side-by-side
- Tracks week-over-week changes
- Shows filtering statistics trends
- Identifies performance improvements/regressions

### Utility Modules

#### `src/new/utils/outlier_detection.py`
- **ZONE_CONGESTION_BOUNDS** - Hard-coded thresholds
- `check_hard_bounds()` - Stage 1 validation
- `compute_group_statistics()` - Per-group statistics
- `build_outlier_statistics()` - Filtering report
- `print_filter_summary()` - Console output

#### `src/new/utils/congestion_utils.py`
- `get_congestion_level()` - Calculates congestion from objectCount
- `get_congestion_bins()` - Returns congestion level list
- `get_congestion_ranges_for_all_groups()` - Zone-specific ranges

#### `src/new/utils/time_utils.py`
- Time parsing and extraction utilities
- Supports HH:MM:SS and MM:SS formats
- Hour extraction for time-of-day analysis

### Enhancement Modules (ML)

#### `src/new/enhancements/time_of_day_enhancer.py`
- Learns hourly adjustment patterns per zone-congestion group
- Applies time-based corrections to predictions
- Trained on historical error patterns

#### `src/new/enhancements/queue_growth_detector.py`
- Detects rapid queue growth scenarios
- Applies conservative adjustments when queue is growing
- Uses sliding window analysis

#### `src/new/enhancements/adjustment_trainer.py`
- Trains time-of-day and queue growth models
- Saves/loads trained parameters
- Validates model performance

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

1. **CSV Loading**: Scripts expect CSV files in `resource/csv/` directory
2. **Encoding**: Files use UTF-8 encoding (Korean language support)
3. **Date Format**: Timestamps follow `YYYY-MM-DD HH:MM:SS` format
4. **Zone IDs**: Valid range is 1-17 (zones 1-4: identity, zones 5-17: security)
5. **Congestion Levels**: Low, Medium, High, Very High (auto-calculated from objectCount)
6. **Python Style**: Follow aggressive Python feature usage guidelines above

### When Adding New Analysis

- Use two-stage filtering: `filter_outliers()` from `data_loader.py`
- Preserve Korean language output conventions in console messages
- Save results as Markdown files in `resource/result/`
- Follow the Table Unit Pattern for new table generators:
  - Separate `_aggregate_data()` for data collection
  - Separate `_generate_*_table()` for table generation
  - Separate `_generate_*_insights()` for insights

### When Adding New Table Generators

1. Create new generator in `src/new/tables/generators/`
2. Extend `BaseTableGenerator` class
3. Implement `generate()` method following table unit pattern
4. Register in `src/new/tables/table_generators.py`
5. Import and call in `src/new/generate_tables.py`

### When Modifying Filtering Logic

- **Stage 1 bounds**: Update `ZONE_CONGESTION_BOUNDS` in `outlier_detection.py`
- **Stage 2 parameters**: Adjust `adaptive_lower_mult`, `adaptive_upper_mult`, `min_sample_threshold`
- **Default parameters** in `filter_outliers()`: `adaptive_lower_mult=0.3`, `adaptive_upper_mult=1.7`
- Always test filtering changes on sample data before running on full dataset

## Integration with Java Codebase

Optimized parameters from this project will be integrated back into:
```
D:\project\gimpo-airport\source_code\LiDAR-Web\src\main\java\lidar\app\lidar_data\HybridWaitTimeCalculator.java
```

Format: Update the `ESTIMATE_SCALE_OVERRIDES` and `BASE_RELIABILITY_OVERRIDES` maps with optimized values from `optimized_parameters.json`.
