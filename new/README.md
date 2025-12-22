# Modular Queue Log Analysis & Table Generation

This directory contains the refactored, modular versions of:
- `analyze_queue_logs_filtered.py` → Log analysis with outlier filtering
- `generate_summary_tables.py` → Summary table generation

## File Structure

```
new/
├── statistics_utils.py                 # Statistical calculation utilities
├── outlier_detection.py                # IQR-based outlier detection
├── data_loader.py                      # CSV file loading (for log analysis)
├── analysis_engine.py                  # Performance analysis engine
├── analyze_queue_logs_modular.py       # Main script: Log analysis
├── table_data_loader.py                # CSV loading with outlier filtering (for tables)
├── table_utils.py                      # Utility functions for table generation
├── table_generators.py                 # Five table generator functions
├── generate_summary_tables_modular.py  # Main script: Summary table generation
└── README.md                           # This file
```

## Module Descriptions

### 1. `statistics_utils.py`
**Purpose**: Provides statistical calculation functions

**Key Functions**:
- `calculate_quartiles(values)` - Calculates Q1, Q2 (median), Q3
- `calculate_statistics(values)` - Returns min, max, mean, median, std

**Dependencies**: None (uses only Python stdlib)

---

### 2. `outlier_detection.py`
**Purpose**: IQR-based outlier detection and filtering

**Key Functions**:
- `detect_outliers_iqr(values, multiplier=1.5)` - Detects outlier indices using IQR method
- `filter_outliers(data)` - Filters outliers from dataset across multiple metrics

**Dependencies**:
- `statistics_utils` (for quartile calculations)

**Metrics Used for Outlier Detection**:
- Actual pass times
- LiDAR estimation errors
- Throughput estimation errors
- Final estimation errors

---

### 3. `data_loader.py`
**Purpose**: CSV file loading and parsing

**Key Functions**:
- `load_all_logs(log_dir="passing_log")` - Loads all CSV files from directory

**Features**:
- Automatically finds `passingObject_*.csv` files
- Handles encoding (UTF-8)
- Type conversion for numeric fields
- Error handling for malformed rows

**Expected CSV Schema**:
```
timestamp, zone_id, objectCount, lidarEstTime, throughputEstTime, finalEstTime, actualPassTime
```

---

### 4. `analysis_engine.py`
**Purpose**: Core analysis logic for queue prediction performance

**Key Functions**:
- `analyze_logs(data)` - Main analysis function

**Analysis Outputs**:
- **Summary**: Date range, zone coverage, basic statistics
- **Accuracy**: MAE, RMSE, median error, percentage errors for all estimators
- **By Zone**: Performance metrics grouped by zone_id
- **By Date**: Performance metrics grouped by date
- **Issues**: Counters for high errors, under/overestimation, extreme times
- **Correlation**: Performance by object count bins

**Dependencies**:
- `statistics_utils` (for statistical calculations)

---

### 5. `analyze_queue_logs_modular.py`
**Purpose**: Main orchestration script

**Key Functions**:
- `main(log_dir, output_file)` - Full pipeline execution
- `print_comparison_summary(original, filtered)` - Prints comparison report

**Pipeline Steps**:
1. Load data from CSV files
2. Analyze original data
3. Filter outliers
4. Analyze filtered data
5. Combine and save results to JSON
6. Print comparison summary

**Dependencies**:
- `data_loader`
- `outlier_detection`
- `analysis_engine`

---

### 6. `table_data_loader.py`
**Purpose**: CSV loading with built-in outlier filtering for table generation

**Key Functions**:
- `load_and_process_data(data_dir="passing_log")` - Loads CSV files and filters outliers

**Features**:
- IQR-based outlier filtering on prediction errors
- Filters extreme values (> 2 hours)
- Returns cleaned data ready for table generation

**Expected CSV Schema**:
```
timestamp, zone_id, objectCount, finalEstTime, actualPassTime
```

---

### 7. `table_utils.py`
**Purpose**: Utility functions for table generation

**Key Functions**:
- `get_day_of_week(timestamp)` - Returns Korean day name (월, 화, 수, etc.)
- `categorize_queue_size(count)` - Categorizes queue size into 50-person buckets
- `calculate_stats(errors)` - Returns count, mean, median, std, early/late counts

**Dependencies**: None (uses only Python stdlib)

---

### 8. `table_generators.py`
**Purpose**: Markdown table generators for different analysis views

**Key Functions**:
- `generate_zone_by_day_table(data)` - Zone × Day of Week table
- `generate_zone_by_queue_table(data)` - Zone × Queue Size table
- `generate_queue_by_day_table(data)` - Queue Size × Day of Week table
- `generate_sample_count_table(data)` - Sample count distribution table
- `generate_summary_statistics_table(data)` - Comprehensive statistics table

**Dependencies**:
- `table_utils` (for helper functions)

**Output Format**: Markdown tables with Korean labels

---

### 9. `generate_summary_tables_modular.py`
**Purpose**: Main orchestration script for table generation

**Key Functions**:
- `main(data_dir, output_file)` - Full pipeline execution

**Pipeline Steps**:
1. Load and process data (with outlier filtering)
2. Generate 5 different table views
3. Combine into single markdown document
4. Save to file

**Dependencies**:
- `table_data_loader`
- `table_generators`

---

## Usage

### Log Analysis

#### Basic Usage
```bash
python analyze_queue_logs_modular.py
```

#### Custom Parameters
```python
from analyze_queue_logs_modular import main

# Custom log directory and output file
results = main(
    log_dir="../csv",
    output_file="my_analysis_results.json"
)
```

#### Using Individual Modules
```python
from data_loader import load_all_logs
from outlier_detection import filter_outliers
from analysis_engine import analyze_logs

# Load data
data = load_all_logs("../csv")

# Filter outliers
clean_data, stats = filter_outliers(data)

# Analyze
results = analyze_logs(clean_data)
```

---

### Summary Table Generation

#### Basic Usage
```bash
python generate_summary_tables_modular.py
```

#### Custom Parameters
```python
from generate_summary_tables_modular import main

# Custom data directory and output file
main(
    data_dir="../csv",
    output_file="my_summary_tables.md"
)
```

#### Using Individual Table Generators
```python
from table_data_loader import load_and_process_data
from table_generators import (
    generate_zone_by_day_table,
    generate_zone_by_queue_table
)

# Load data (already filtered)
data = load_and_process_data("../csv")

# Generate specific tables
zone_day_table = generate_zone_by_day_table(data)
zone_queue_table = generate_zone_by_queue_table(data)

# Save to file
with open("custom_tables.md", "w", encoding="utf-8") as f:
    f.write(zone_day_table + "\n\n" + zone_queue_table)
```

---

## Output Formats

### Log Analysis Output (JSON)

The log analysis script produces a JSON file with the following structure:

```json
{
  "outlier_removal": {
    "total_records": 57887,
    "removed_records": 5234,
    "filtered_records": 52653,
    "removal_rate_pct": 9.04,
    "outliers_by_type": {...}
  },
  "original": {
    "summary": {...},
    "accuracy": {...},
    "by_zone": {...},
    "by_date": {...},
    "issues": {...},
    "correlation": {...}
  },
  "filtered": {
    "summary": {...},
    "accuracy": {...},
    "by_zone": {...},
    "by_date": {...},
    "issues": {...},
    "correlation": {...}
  }
}
```

### Summary Table Output (Markdown)

The table generation script produces a markdown file with:

1. **Zone × Day of Week** - Average errors by zone and day
2. **Zone × Queue Size** - Average errors by zone and queue size (50-person buckets)
3. **Queue Size × Day of Week** - Average errors by queue size and day
4. **Sample Counts** - Data distribution across zones and days
5. **Summary Statistics** - Comprehensive statistics by zone, day, and queue size

All values are in minutes with sign notation:
- **Positive (+)**: Over-estimation (predicted later than actual)
- **Negative (-)**: Under-estimation (predicted earlier than actual)

---

## Benefits of Modular Design

1. **Reusability**: Each module can be imported independently
2. **Testability**: Functions can be unit tested in isolation
3. **Maintainability**: Changes to one feature don't affect others
4. **Readability**: Smaller, focused files are easier to understand
5. **Extensibility**: Easy to add new analysis features or outlier detection methods

## Comparison with Original

### Log Analysis Script

| Feature | Original | Modular |
|---------|----------|---------|
| Lines per file | 445 | ~50-250 per module |
| Modules | 1 monolithic | 5 focused modules |
| Testability | Low | High |
| Import flexibility | None | High |
| Code reuse | Difficult | Easy |

### Table Generation Script

| Feature | Original | Modular |
|---------|----------|---------|
| Lines per file | 366 | ~60-200 per module |
| Modules | 1 monolithic | 4 focused modules |
| Testability | Low | High |
| Import flexibility | None | High |
| Table generator reuse | Difficult | Easy (import individual generators) |

---

## Module Dependencies

```
Log Analysis Pipeline:
└── analyze_queue_logs_modular.py
    ├── data_loader.py
    ├── outlier_detection.py
    │   └── statistics_utils.py
    └── analysis_engine.py
        └── statistics_utils.py

Table Generation Pipeline:
└── generate_summary_tables_modular.py
    ├── table_data_loader.py
    └── table_generators.py
        └── table_utils.py
```

**Shared Module**: `statistics_utils.py` is reused by both pipelines for statistical calculations.
