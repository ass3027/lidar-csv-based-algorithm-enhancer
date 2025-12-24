# Gemini Code Assistant Guidance

This file provides guidance to the Gemini Code Assistant when working with code in this repository.

## Project Overview

This is a **Python-based data analysis and algorithm optimization project** for Gimpo Airport's wait time prediction system. The goal is to optimize a hybrid wait time prediction algorithm used in airport departure processing zones. The algorithm itself is implemented in Java, and this project uses Python to analyze historical data and find optimal parameters.

**Source Algorithm Location**: `D:\project\gimpo-airport\source_code\LiDAR-Web\src\main\java\lidar\app\lidar_data\HybridWaitTimeCalculator.java`

## Project Structure

The project is structured into a `legacy` and a `new` version. The `new` version is a refactoring of the original scripts into a more modular and maintainable structure.

```
csv-based-algorithm-enhancer/
├── csv/                            # Historical data (CSV format)
├── legacy/
│   └── algorithm_enhancement.py    # Original optimization implementation
├── new/                            # Refactored, modular version
│   ├── core/                       # Core analysis and data loading logic
│   ├── enhancements/               # Algorithm enhancement modules
│   ├── scripts/                    # Main scripts to run analysis and training
│   ├── tables/                     # Table generation modules
│   └── utils/                      # Utility modules
├── requirements.md                 # Detailed project requirements
└── CLAUDE.md                       # Guidance for the Claude AI model (useful for context)
```

## Running Scripts

### Refactored (`new`) Scripts

The `new` directory contains the most up-to-date and modular scripts.

**Analyze Logs:**
```bash
python new/scripts/analyze_with_enhancements.py
```

**Generate Summary Tables:**
```bash
python new/generate_tables.py
```

### Legacy Scripts

The legacy scripts are still available for reference.

**Algorithm Optimization (Legacy):**
```bash
python legacy/algorithm_enhancement.py
```

## Data Schema

The input data is in CSV files located in the `csv/` directory.

| Column            | Type     | Description                                       |
|-------------------|----------|---------------------------------------------------|
| `timestamp`       | datetime | Record timestamp                                  |
| `zone_id`         | integer  | Zone identifier (1-17)                            |
| `objectCount`     | integer  | Number of waiting people                          |
| `lidarEstTime`    | integer  | LiDAR-based estimate (seconds)                    |
| `throughputEstTime`| float    | Throughput-based estimate (seconds)               |
| `finalEstTime`    | integer  | Current hybrid algorithm output (seconds)         |
| `actualPassTime`  | integer  | **Ground truth** - Actual measured wait time (seconds) |

## Algorithm Architecture

The hybrid wait time calculator combines two estimation methods:

```
hybridWaitTime = reliability × lidarEstimate + (1 - reliability) × throughputEstimate
```

The `reliability` factor is calculated based on zone-specific base reliability and a stability factor. The goal of this project is to optimize the parameters used in this calculation.

## Data Quality and Outlier Detection

A critical part of this project is handling anomalies in the `actualPassTime` data. The `new` scripts use an IQR-based outlier detection method on both the `actualPassTime` and the prediction errors. The `legacy` script uses a rolling average-based filter.

## Optimization Objectives

1.  **Conservative Prediction Target**: At least 90% of predictions must be greater than or equal to the actual wait time.
2.  **Accuracy Metrics**: Minimize MAE, RMSE, and MAPE.

## Coding Standards

As outlined in `CLAUDE.md`, the project prefers a modern, idiomatic Python style. When making changes, please adhere to the following:

*   **Use modern Python features**: Comprehensions, f-strings, tuple unpacking, etc.
*   **Follow the modular structure**: Keep code in the appropriate modules within the `new` directory.
*   **Maintain existing conventions**: Preserve Korean language output and the use of JSON for machine-readable results and Markdown for human-readable reports.
