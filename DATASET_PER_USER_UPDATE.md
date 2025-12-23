# Dataset-Per-User Support - Implementation Summary

## Overview

Implemented "dataset-per-user" (Option A) support by adding `--dataset` argument to all CLI scripts. Each dataset is self-contained with its own `sources/`, `books.csv`, and `reports/` directories.

## Changes Made

### 1. Updated All CLI Scripts

All scripts now accept `--dataset` argument (default: `datasets/default`):

#### `scripts/ingest_goodreads.py`
- Added `--dataset` argument (default: `datasets/default`)
- Paths now resolve relative to dataset root:
  - Input: `{dataset}/sources/goodreads_export.csv`
  - Output: `{dataset}/sources/goodreads_canonical.csv`
- Creates `sources/` directory if missing

#### `scripts/merge_and_dedupe.py`
- Added `--dataset` argument (default: `datasets/default`)
- Paths now resolve relative to dataset root:
  - Input: `{dataset}/sources/goodreads_canonical.csv`
  - Output: `{dataset}/books.csv`
  - Reports: `{dataset}/reports/possible_duplicates.csv`
- Creates `dataset/`, `sources/`, and `reports/` directories if missing
- Handles case where `books.csv` doesn't exist yet (creates new)

#### `scripts/validate_books_csv.py`
- Added `--dataset` argument (default: `datasets/default`)
- Added `--csv` argument (overrides `--dataset` for backward compatibility)
- Paths resolve to `{dataset}/books.csv` unless `--csv` is specified

#### `scripts/find_duplicates.py`
- Added `--dataset` argument (default: `datasets/default`)
- Added `--csv` argument (overrides `--dataset` for backward compatibility)
- Paths resolve to `{dataset}/books.csv` unless `--csv` is specified

#### `scripts/recommend.py`
- Added `--dataset` argument (default: `datasets/default`)
- Added `--csv` argument (overrides `--dataset` for backward compatibility)
- Paths resolve to `{dataset}/books.csv` unless `--csv` is specified

### 2. Updated Documentation

#### `README.md`
- Added "Dataset-Per-User Architecture" section explaining dataset layout
- Updated Quick Start to use `--dataset` arguments
- Updated Directory Structure to show `datasets/` hierarchy
- Updated Scripts section with example commands using `--dataset`
- Added "Example: Working with Multiple Datasets" section

#### `DESIGN.md`
- Added "Dataset-Per-User Architecture" section at the top
- Documented dataset structure and layout
- Explained path resolution rules
- Documented data isolation guarantees

### 3. Fixed Minor Issues

- Fixed missing `tags` field in `CANONICAL_FIELDS` in `ingest_goodreads.py`

## Dataset Structure

Each dataset directory contains:
```
datasets/
└── {dataset_name}/
    ├── sources/
    │   ├── goodreads_export.csv          # Input
    │   └── goodreads_canonical.csv       # Intermediate output
    ├── books.csv                         # Canonical output (single source of truth)
    └── reports/
        └── possible_duplicates.csv       # Duplicate detection reports
```

## Example Usage

### Default Dataset
```bash
# Ingest Goodreads
python scripts/ingest_goodreads.py

# Merge and deduplicate
python scripts/merge_and_dedupe.py

# Validate
python scripts/validate_books_csv.py

# Find duplicates
python scripts/find_duplicates.py

# Generate recommendations
python scripts/recommend.py --query "fantasy" --limit 5
```

### Custom Dataset
```bash
# Create dataset directory
mkdir -p datasets/lindsay/sources

# Ingest Goodreads
python scripts/ingest_goodreads.py --dataset datasets/lindsay

# Merge and deduplicate
python scripts/merge_and_dedupe.py --dataset datasets/lindsay

# Validate
python scripts/validate_books_csv.py --dataset datasets/lindsay

# Find duplicates
python scripts/find_duplicates.py --dataset datasets/lindsay

# Generate recommendations
python scripts/recommend.py --dataset datasets/lindsay --query "mystery" --limit 5
```

## Backward Compatibility

- Default dataset path is `datasets/default`, so existing workflows continue to work
- Scripts that had `--csv` argument retain it (overrides `--dataset`)
- All core logic unchanged (deterministic, preserves protected fields)

## Data Safety

- **No global assumptions**: All paths are relative to dataset root
- **Isolated datasets**: Each dataset is completely independent
- **Protected fields preserved**: Manual fields still protected per dataset
- **Deterministic**: Same inputs produce same outputs per dataset

## Migration Notes

For existing projects:
1. Create `datasets/default/` directory
2. Move existing `sources/` to `datasets/default/sources/`
3. Move existing `books.csv` to `datasets/default/books.csv`
4. Create `datasets/default/reports/` directory
5. Run scripts with `--dataset datasets/default` (or rely on default)

Or continue using `--csv` argument for backward compatibility.

