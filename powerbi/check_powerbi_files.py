"""
ASG Airlines — Power BI Setup Helper
=====================================
Run this script ONCE to verify that all required CSV files exist
for loading into Power BI Desktop.
"""

import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

FILES = {
    "Cleaned Datasets": [
        BASE / "data/cleaned/cleaned_flights.csv",
        BASE / "data/cleaned/cleaned_bookings_masked.csv",
        BASE / "data/cleaned/cleaned_passengers_masked.csv",
        BASE / "data/cleaned/cleaned_payments.csv",
        BASE / "data/cleaned/master_dataset.csv",
    ],
    "KPI Aggregations": [
        BASE / "data/aggregated/kpi_route_traffic.csv",
        BASE / "data/aggregated/kpi_avg_duration_by_airline.csv",
        BASE / "data/aggregated/kpi_avg_duration_by_route.csv",
        BASE / "data/aggregated/kpi_airline_distribution.csv",
        BASE / "data/aggregated/kpi_delay_summary.csv",
        BASE / "data/aggregated/kpi_revenue_by_airline.csv",
        BASE / "data/aggregated/kpi_departure_slots.csv",
        BASE / "data/aggregated/kpi_booking_status.csv",
        BASE / "data/aggregated/kpi_payment_methods.csv",
    ],
}

print("=" * 55)
print("   ASG Airlines — Power BI File Readiness Check")
print("=" * 55)

all_ok = True
for section, paths in FILES.items():
    print(f"\n  {section}:")
    for p in paths:
        exists = p.exists()
        size   = f"{p.stat().st_size // 1024} KB" if exists else "MISSING"
        status = "[OK]    " if exists else "[MISSING]"
        all_ok = all_ok and exists
        print(f"    {status} {p.name:<45} {size}")

print("\n" + "=" * 55)
if all_ok:
    print("  [OK] All files ready! Open Power BI Desktop and")
    print("       import files from the paths above.")
else:
    print("  [MISSING FILES] Some files are missing. Please re-run the")
    print("                  Jupyter notebook first.")
print("=" * 55)
