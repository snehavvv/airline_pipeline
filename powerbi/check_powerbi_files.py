# Checks that all expected output files from run_pipeline.py and
# generate_dashboard_and_screenshots.py are present.
# Run directly: python powerbi/check_powerbi_files.py

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CLEANED = BASE / 'data' / 'cleaned'
AGG = BASE / 'data' / 'aggregated'
POWERBI = BASE / 'powerbi'
PREVIEWS = POWERBI / 'previews'

REQUIRED_CLEANED = [
    'master_dataset.csv',
    'cleaned_flights.csv',
    'cleaned_bookings_masked.csv',
    'cleaned_passengers_masked.csv',
    'cleaned_payments.csv'
]

REQUIRED_KPIS = [
    'kpi_route_traffic.csv',
    'kpi_avg_duration_by_airline.csv',
    'kpi_avg_duration_by_route.csv',
    'kpi_airline_distribution.csv',
    'kpi_delay_summary.csv',
    'kpi_revenue_by_airline.csv',
    'kpi_departure_slots.csv',
    'kpi_booking_status.csv',
    'kpi_payment_methods.csv',
    'kpi_passenger_demographics.csv',
    'kpi_frequent_flyers.csv',
    'kpi_airline_passenger_demographics.csv'
]

REQUIRED_PBI = [
    'ASG_Airlines_Dashboard.pbix',
    'dashboard_preview.png'
]

REQUIRED_PREVIEWS = [
    '01_operations_overview.png',
    '02_route_delay_performance.png',
    '03_commercial_financial_trends.png',
    '04_passenger_demographics_loyalty.png',
    'asg_airlines_dashboard_preview.png'
]

def check():
    print("=" * 60)
    print("  ASG Airlines - Power BI Artifacts Check")
    print("=" * 60)
    
    all_ok = True
    
    print("\n[1] Checking Cleaned Core Data Files (data/cleaned/):")
    for f in REQUIRED_CLEANED:
        p = CLEANED / f
        exists = p.exists()
        size_kb = (p.stat().st_size // 1024) if exists else 0
        print(f"  [{'OK' if exists else 'MISSING'}] {f} ({size_kb} KB)")
        if not exists: all_ok = False

    print("\n[2] Checking 12 KPI Summary Datasets (data/aggregated/):")
    for f in REQUIRED_KPIS:
        p = AGG / f
        exists = p.exists()
        print(f"  [{'OK' if exists else 'MISSING'}] {f}")
        if not exists: all_ok = False

    print("\n[3] Checking Power BI Report & Deliverables (powerbi/):")
    for f in REQUIRED_PBI:
        p = POWERBI / f
        exists = p.exists()
        size_kb = (p.stat().st_size // 1024) if exists else 0
        print(f"  [{'OK' if exists else 'MISSING'}] {f} ({size_kb} KB)")
        if not exists: all_ok = False

    print("\n[4] Checking Analytical Preview Images (powerbi/previews/):")
    for f in REQUIRED_PREVIEWS:
        p = PREVIEWS / f
        exists = p.exists()
        print(f"  [{'OK' if exists else 'MISSING'}] {f}")
        if not exists: all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("[OK] All artifacts present.")
    else:
        print("[ERROR] Some artifacts are missing. Run run_pipeline.py and generate_dashboard_and_screenshots.py.")
    print("=" * 60)

if __name__ == '__main__':
    check()
