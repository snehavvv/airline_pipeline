"""
ASG Airlines — Power BI Setup Helper
=====================================
Run this script ONCE to verify that all required CSV files exist
for loading into Power BI Desktop.
"""

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

FILES = {
    "Cleaned Datasets (All 4 Tables + Master)": [
        BASE / "data/cleaned/cleaned_flights.csv",
        BASE / "data/cleaned/cleaned_bookings_masked.csv",
        BASE / "data/cleaned/cleaned_passengers_masked.csv",
        BASE / "data/cleaned/cleaned_payments.csv",
        BASE / "data/cleaned/master_dataset.csv",
    ],
    "KPI Aggregations (Flight, Booking, Payment & Passenger Analytics)": [
        BASE / "data/aggregated/kpi_route_traffic.csv",
        BASE / "data/aggregated/kpi_avg_duration_by_airline.csv",
        BASE / "data/aggregated/kpi_avg_duration_by_route.csv",
        BASE / "data/aggregated/kpi_airline_distribution.csv",
        BASE / "data/aggregated/kpi_delay_summary.csv",
        BASE / "data/aggregated/kpi_revenue_by_airline.csv",
        BASE / "data/aggregated/kpi_departure_slots.csv",
        BASE / "data/aggregated/kpi_booking_status.csv",
        BASE / "data/aggregated/kpi_payment_methods.csv",
        BASE / "data/aggregated/kpi_passenger_demographics.csv",
        BASE / "data/aggregated/kpi_frequent_flyers.csv",
        BASE / "data/aggregated/kpi_airline_passenger_demographics.csv",
    ],
    "Visualizations": [
        BASE / "data/cleaned/viz_airline_distribution.png",
        BASE / "data/cleaned/viz_avg_duration_route.png",
        BASE / "data/cleaned/viz_delay_rate.png",
        BASE / "data/cleaned/viz_departure_slots.png",
        BASE / "data/cleaned/viz_duration_dist.png",
        BASE / "data/cleaned/viz_route_heatmap.png",
        BASE / "data/cleaned/viz_passenger_demographics.png",
        BASE / "data/cleaned/viz_passenger_revenue_by_age.png",
    ],
}

print("=" * 60)
print("   ASG Airlines — Power BI File Readiness Check")
print("=" * 60)

all_ok = True
for section, paths in FILES.items():
    print(f"\n  {section}:")
    for p in paths:
        exists = p.exists()
        size   = f"{p.stat().st_size // 1024} KB" if exists else "MISSING"
        status = "[OK]    " if exists else "[MISSING]"
        all_ok = all_ok and exists
        print(f"    {status} {p.name:<45} {size}")

print("\n" + "=" * 60)
if all_ok:
    print("  [OK] All 4 tables & KPIs ready! Open Power BI Desktop and")
    print("       import master_dataset.csv and KPI tables.")
else:
    print("  [MISSING FILES] Some files are missing. Please re-run")
    print("                  run_pipeline.py first.")
print("=" * 60)
