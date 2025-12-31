#!/bin/bash
python src/new/generate_tables.py --from 20251207 --to 20251213
python src/new/generate_tables.py --from 20251214 --to 20251220
python src/new/generate_tables.py --from 20251221 --to 20251227
python src/new/compare_weekly_analysis.py