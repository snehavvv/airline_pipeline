# Pipeline script for the ASG Airlines data engineering project.
# Reads the source Excel workbook, cleans each sheet, masks PII,
# builds a unified master dataset, computes KPI aggregations, and
# generates a few charts. Run directly: python run_pipeline.py

import hashlib
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger('ASG-Pipeline')


class PipelineDataError(Exception):
    """Raised when a required sheet or column is missing from the workbook."""
    pass


BASE_DIR    = Path(__file__).resolve().parent
RAW_DIR     = BASE_DIR / 'data' / 'raw'
CLEANED_DIR = BASE_DIR / 'data' / 'cleaned'
AGG_DIR     = BASE_DIR / 'data' / 'aggregated'

CLEANED_DIR.mkdir(parents=True, exist_ok=True)
AGG_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


def resolve_raw_file() -> Path:
    """Look for the source workbook in a few likely locations."""
    candidates = [
        RAW_DIR / 'UseCase - Airlines.xlsx',
        BASE_DIR.parent / 'UseCase - Airlines.xlsx',
        RAW_DIR / 'sample_usecase_airlines.xlsx',
        BASE_DIR / 'sample_usecase_airlines.xlsx'
    ]
    for candidate in candidates:
        if candidate.exists():
            log.info("Found input file at: %s", candidate)
            return candidate

    log.error("Could not find 'UseCase - Airlines.xlsx'. Place it in '%s' or use the sample file.", RAW_DIR)
    raise FileNotFoundError(f"Source file missing. Expected at {RAW_DIR / 'UseCase - Airlines.xlsx'}")


def run():
    log.info("Starting ASG Airlines pipeline...")

    # 1. Load workbook
    try:
        raw_path = resolve_raw_file()
        excel_file = pd.ExcelFile(raw_path)
        required_sheets = ['flights', 'bookings', 'passengers', 'payments']

        missing_sheets = [s for s in required_sheets if s not in excel_file.sheet_names]
        if missing_sheets:
            raise PipelineDataError(f"Workbook is missing sheet(s): {missing_sheets}")

        raw = {}
        for sheet in required_sheets:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            df = df[[c for c in df.columns if not str(c).startswith('Unnamed')]]
            if df.empty:
                log.warning("Sheet [%s] loaded but is empty.", sheet)
            raw[sheet] = df
            log.info("Loaded [%s]: %d rows, %d cols", sheet, len(df), len(df.columns))

    except Exception as e:
        log.error("Failed to load workbook: %s", e, exc_info=True)
        sys.exit(1)

    # 2. Clean flights
    try:
        log.info("Cleaning flights table...")
        flights = raw['flights'].copy()

        # check expected columns are present
        req_flights_cols = {'flight_id', 'airline', 'source', 'destination', 'departure_time', 'arrival_time'}
        if not req_flights_cols.issubset(set(flights.columns)):
            missing = req_flights_cols - set(flights.columns)
            log.warning("Flights table missing columns: %s — trying positional rename.", missing)

        drop_cols = [c for c in flights.columns if str(c).startswith('Unnamed') or c == 'duration']
        flights.drop(columns=drop_cols, errors='ignore', inplace=True)
        flights.columns = ['flight_id', 'airline', 'source', 'destination', 'departure_time', 'arrival_time']

        for col in ['flight_id', 'airline', 'source', 'destination']:
            flights[col] = flights[col].astype(str).str.strip().str.upper()

        flights['departure_time'] = pd.to_datetime(flights['departure_time'], errors='coerce')
        flights['arrival_time']   = pd.to_datetime(flights['arrival_time'],   errors='coerce')

        before = len(flights)
        flights.dropna(subset=['flight_id', 'source', 'destination', 'departure_time', 'arrival_time'], inplace=True)
        log.info("Dropped %d rows with null key fields", before - len(flights))

        before = len(flights)
        flights.drop_duplicates(inplace=True)
        log.info("Dropped %d fully duplicate rows", before - len(flights))

        before = len(flights)
        flights.drop_duplicates(subset=['flight_id'], keep='first', inplace=True)
        log.info("Dropped %d duplicate flight_ids", before - len(flights))

        flights = flights[flights['arrival_time'] > flights['departure_time']]

        # fill in airline name from the flight_id prefix where it's blank/unknown
        AIRLINE_MAP = {'AI': 'Air India', 'SJ': 'SpiceJet', '6F': 'IndiGo', 'UK': 'Vistara', 'G8': 'Go First'}
        def impute_airline(row):
            if row['airline'] == 'UNKNOWN':
                return AIRLINE_MAP.get(str(row['flight_id'])[:2], 'UNKNOWN')
            return row['airline']

        flights['airline'] = flights.apply(impute_airline, axis=1)

        before = len(flights)
        flights = flights[~flights['airline'].isin(['NAN', '', 'NONE'])]
        flights.dropna(subset=['airline'], inplace=True)
        log.info("Dropped %d rows where airline could not be resolved", before - len(flights))

        flights['duration_mins'] = (
            (flights['arrival_time'] - flights['departure_time']).dt.total_seconds() / 60
        ).round(2)
        flights['is_overnight'] = (
            flights['arrival_time'].dt.date > flights['departure_time'].dt.date
        ).astype(int)
        flights = flights[(flights['duration_mins'] > 0) & (flights['duration_mins'] <= 1440)]
        flights['duration_hhmm'] = flights['duration_mins'].apply(lambda m: f"{int(m)//60}h {int(m)%60}m")
        flights['route']         = flights['source'] + ' to ' + flights['destination']

        # flag flights significantly longer than the average for their route
        route_avg = flights.groupby('route')['duration_mins'].transform('mean')
        flights['is_delayed'] = (flights['duration_mins'] > route_avg * 1.30).astype(int)

        def get_time_slot(dt):
            if pd.isna(dt): return 'Unknown'
            h = dt.hour
            if 5 <= h < 9:   return 'Early Morning (05-09)'
            if 9 <= h < 12:  return 'Morning (09-12)'
            if 12 <= h < 17: return 'Afternoon (12-17)'
            if 17 <= h < 21: return 'Evening (17-21)'
            return 'Night (21-05)'

        flights['departure_slot'] = flights['departure_time'].apply(get_time_slot)
        log.info("Flights cleaned: %d rows remaining.", len(flights))

    except Exception as e:
        log.error("Error cleaning flights: %s", e, exc_info=True)
        sys.exit(1)

    # 3. Clean bookings + mask PII
    try:
        log.info("Cleaning bookings table...")
        bookings = raw['bookings'].copy()
        bookings.drop(columns=[c for c in bookings.columns if str(c).startswith('Unnamed')], errors='ignore', inplace=True)
        bookings.columns = ['booking_id', 'passenger_id', 'flight_id', 'booking_date',
                            'status', 'passport_number', 'seat_number',
                            'emergency_contact_name', 'emergency_contact_phone']

        for col in ['booking_id', 'passenger_id', 'flight_id', 'status', 'seat_number']:
            bookings[col] = bookings[col].astype(str).str.strip().str.upper()

        bookings['booking_date'] = pd.to_datetime(bookings['booking_date'], errors='coerce')
        bookings.drop_duplicates(subset=['booking_id'], keep='first', inplace=True)

        SALT = 'ASGAirlines2026'
        def sha256_hash(val):
            if pd.isna(val) or str(val).strip().upper() in ('', 'NAN', 'NONE'):
                return 'HASH_MISSING'
            return hashlib.sha256((str(val).strip() + SALT).encode('utf-8')).hexdigest()

        def mask_name(val):
            s = str(val).strip()
            return f"{s[0]}***" if len(s) > 0 else 'N***'

        bookings_masked = bookings.copy()
        bookings_masked['passport_number']         = bookings_masked['passport_number'].apply(sha256_hash)
        bookings_masked['emergency_contact_phone'] = bookings_masked['emergency_contact_phone'].apply(sha256_hash)
        bookings_masked['emergency_contact_name']  = bookings_masked['emergency_contact_name'].apply(mask_name)
        log.info("Bookings cleaned: %d rows.", len(bookings_masked))

    except Exception as e:
        log.error("Error cleaning bookings: %s", e, exc_info=True)
        sys.exit(1)

    # 4. Clean passengers + mask PII
    try:
        log.info("Cleaning passengers table...")
        passengers = raw['passengers'].copy()
        passengers.drop(columns=[c for c in passengers.columns if str(c).startswith('Unnamed')], errors='ignore', inplace=True)
        passengers.columns = ['passenger_id', 'first_name', 'last_name', 'age',
                              'gender', 'email', 'phone', 'aadhaar_id', 'date_of_birth']

        for col in ['passenger_id', 'gender']:
            passengers[col] = passengers[col].astype(str).str.strip().str.upper()

        passengers['gender'] = passengers['gender'].apply(lambda g: 'F' if g == 'F' else 'M')
        passengers['age']    = pd.to_numeric(passengers['age'], errors='coerce')
        passengers['date_of_birth'] = pd.to_datetime(passengers['date_of_birth'], errors='coerce')
        passengers['birth_year']    = passengers['date_of_birth'].dt.year.fillna(0).astype(int)

        def assign_age_group(age):
            if pd.isna(age):  return 'Unknown'
            if age < 18:      return 'Under 18'
            if age <= 30:     return '18-30'
            if age <= 45:     return '31-45'
            if age <= 60:     return '46-60'
            return '60+'

        passengers['age_group'] = passengers['age'].apply(assign_age_group)

        passengers_masked = passengers.copy()
        passengers_masked['first_name']  = passengers_masked['first_name'].apply(mask_name)
        passengers_masked['last_name']   = passengers_masked['last_name'].apply(mask_name)
        passengers_masked['email']       = passengers_masked['email'].apply(sha256_hash)
        passengers_masked['phone']       = passengers_masked['phone'].apply(sha256_hash)
        passengers_masked['aadhaar_id']  = passengers_masked['aadhaar_id'].apply(sha256_hash)
        passengers_masked.drop(columns=['date_of_birth'], errors='ignore', inplace=True)
        passengers_masked.drop_duplicates(subset=['passenger_id'], keep='first', inplace=True)
        log.info("Passengers cleaned: %d rows.", len(passengers_masked))

    except Exception as e:
        log.error("Error cleaning passengers: %s", e, exc_info=True)
        sys.exit(1)

    # 5. Clean payments
    try:
        log.info("Cleaning payments table...")
        payments = raw['payments'].copy()
        payments.drop(columns=[c for c in payments.columns if str(c).startswith('Unnamed')], errors='ignore', inplace=True)
        payments.columns = ['payment_id', 'booking_id', 'amount', 'payment_method']

        for col in ['payment_id', 'booking_id', 'payment_method']:
            payments[col] = payments[col].astype(str).str.strip().str.upper()

        payments['amount'] = pd.to_numeric(payments['amount'], errors='coerce')
        payments.dropna(subset=['amount'], inplace=True)
        payments.drop_duplicates(subset=['payment_id'], keep='first', inplace=True)
        log.info("Payments cleaned: %d rows.", len(payments))

    except Exception as e:
        log.error("Error cleaning payments: %s", e, exc_info=True)
        sys.exit(1)

    # 6. Join all four tables into master dataset
    try:
        log.info("Building master dataset (bookings + flights + payments + passengers)...")
        pax_cols = [c for c in ['passenger_id', 'age', 'age_group', 'gender', 'first_name', 'last_name'] if c in passengers_masked.columns]
        master = (
            bookings_masked
            .merge(flights, on='flight_id', how='left')
            .merge(payments, on='booking_id', how='left')
            .merge(passengers_masked[pax_cols], on='passenger_id', how='left', suffixes=('', '_pax'))
        )
        master.to_csv(CLEANED_DIR / 'master_dataset.csv', index=False)
        flights.to_csv(CLEANED_DIR / 'cleaned_flights.csv', index=False)
        bookings_masked.to_csv(CLEANED_DIR / 'cleaned_bookings_masked.csv', index=False)
        passengers_masked.to_csv(CLEANED_DIR / 'cleaned_passengers_masked.csv', index=False)
        payments.to_csv(CLEANED_DIR / 'cleaned_payments.csv', index=False)
        log.info("Saved cleaned datasets to '%s' (master has %d rows).", CLEANED_DIR, len(master))

    except Exception as e:
        log.error("Error building master dataset: %s", e, exc_info=True)
        sys.exit(1)

    # 7. KPI aggregations
    try:
        log.info("Computing KPI aggregations...")

        # Route traffic
        kpi_route = (
            flights.groupby('route')
            .agg(flight_count=('flight_id', 'count'),
                 avg_duration_mins=('duration_mins', 'mean'),
                 delay_rate_pct=('is_delayed', lambda x: round(x.mean() * 100, 2)))
            .reset_index()
            .sort_values(by='flight_count', ascending=False)
        )
        kpi_route.to_csv(AGG_DIR / 'kpi_route_traffic.csv', index=False)

        # Average duration by airline
        kpi_airline_dur = (
            flights.groupby('airline')
            .agg(avg_duration_mins=('duration_mins', 'mean'),
                 min_duration_mins=('duration_mins', 'min'),
                 max_duration_mins=('duration_mins', 'max'))
            .reset_index()
        )
        kpi_airline_dur.to_csv(AGG_DIR / 'kpi_avg_duration_by_airline.csv', index=False)

        # Average duration by route
        kpi_route_dur = flights.groupby('route')['duration_mins'].mean().reset_index()
        kpi_route_dur.columns = ['route', 'avg_duration_mins']
        kpi_route_dur.to_csv(AGG_DIR / 'kpi_avg_duration_by_route.csv', index=False)

        # Airline distribution
        kpi_airline_dist = flights['airline'].value_counts().reset_index()
        kpi_airline_dist.columns = ['airline', 'flight_count']
        kpi_airline_dist['market_share_pct'] = (kpi_airline_dist['flight_count'] / len(flights) * 100).round(2)
        kpi_airline_dist.to_csv(AGG_DIR / 'kpi_airline_distribution.csv', index=False)

        # Delay summary
        kpi_delay = (
            flights.groupby('airline')
            .agg(total_flights=('flight_id', 'count'),
                 delayed_flights=('is_delayed', 'sum'),
                 overnight_flights=('is_overnight', 'sum'))
            .reset_index()
        )
        kpi_delay['delay_rate_pct'] = (kpi_delay['delayed_flights'] / kpi_delay['total_flights'] * 100).round(2)
        kpi_delay.to_csv(AGG_DIR / 'kpi_delay_summary.csv', index=False)

        # Revenue by airline
        booking_pay = bookings.merge(payments, on='booking_id', how='inner')
        flight_rev = booking_pay.merge(flights[['flight_id', 'airline']], on='flight_id', how='left')
        kpi_rev = (
            flight_rev.groupby('airline')
            .agg(total_revenue=('amount', 'sum'),
                 total_bookings=('booking_id', 'count'),
                 avg_ticket_value=('amount', 'mean'))
            .reset_index()
            .sort_values(by='total_revenue', ascending=False)
        )
        kpi_rev.to_csv(AGG_DIR / 'kpi_revenue_by_airline.csv', index=False)

        # Departure time slots
        kpi_slots = (
            flights.groupby('departure_slot')
            .agg(flight_count=('flight_id', 'count'),
                 delayed_flights=('is_delayed', 'sum'))
            .reset_index()
        )
        kpi_slots['delay_rate_pct'] = (kpi_slots['delayed_flights'] / kpi_slots['flight_count'] * 100).round(2)
        kpi_slots.to_csv(AGG_DIR / 'kpi_departure_slots.csv', index=False)

        # Booking status distribution
        kpi_status = bookings['status'].value_counts().reset_index()
        kpi_status.columns = ['status', 'booking_count']
        kpi_status['percentage'] = (kpi_status['booking_count'] / len(bookings) * 100).round(2)
        kpi_status.to_csv(AGG_DIR / 'kpi_booking_status.csv', index=False)

        # Payment methods
        kpi_pm = (
            payments.groupby('payment_method')
            .agg(transaction_count=('payment_id', 'count'),
                 total_amount=('amount', 'sum'),
                 avg_amount=('amount', 'mean'))
            .reset_index()
        )
        kpi_pm.to_csv(AGG_DIR / 'kpi_payment_methods.csv', index=False)

        # Passenger demographics
        pax_revenue = (
            passengers_masked
            .merge(bookings_masked[['passenger_id', 'booking_id']], on='passenger_id', how='left')
            .merge(payments[['booking_id', 'amount']], on='booking_id', how='left')
        )
        kpi_pax_demo = (
            pax_revenue.groupby(['gender', 'age_group'])
            .agg(passenger_count=('passenger_id', 'nunique'),
                 total_bookings=('booking_id', 'count'),
                 total_spend=('amount', 'sum'))
            .reset_index()
        )
        kpi_pax_demo.to_csv(AGG_DIR / 'kpi_passenger_demographics.csv', index=False)

        # Frequent flyers / loyalty
        kpi_frequent = (
            pax_revenue.groupby(['passenger_id', 'first_name', 'last_name', 'age_group'])
            .agg(total_bookings=('booking_id', 'count'),
                 total_spend=('amount', 'sum'))
            .reset_index()
            .sort_values(by=['total_bookings', 'total_spend'], ascending=False)
            .head(20)
        )
        kpi_frequent.to_csv(AGG_DIR / 'kpi_frequent_flyers.csv', index=False)

        # Airline x passenger demographics breakdown
        airline_pax = (
            master.groupby(['airline', 'gender', 'age_group'])
            .agg(passenger_count=('passenger_id', 'nunique'),
                 revenue=('amount', 'sum'))
            .reset_index()
        )
        airline_pax.to_csv(AGG_DIR / 'kpi_airline_passenger_demographics.csv', index=False)

        log.info("KPI aggregations saved to '%s'.", AGG_DIR)

    except Exception as e:
        log.error("Error during KPI calculation: %s", e, exc_info=True)
        sys.exit(1)

    # 8. Charts
    try:
        log.info("Generating charts...")
        sns.set_theme(style="whitegrid", palette="muted")
        palette = sns.color_palette("Set2")

        fig, ax = plt.subplots(figsize=(8, 4.5))
        sns.barplot(data=kpi_airline_dist, x='airline', y='flight_count', palette=palette, ax=ax)
        ax.set_title('ASG Airlines — Flight Count by Airline', fontsize=12, fontweight='bold')
        ax.set_xlabel('Airline')
        ax.set_ylabel('Flight Count')
        for p in ax.patches:
            ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='bottom', fontsize=10, xytext=(0, 3), textcoords='offset points')
        plt.tight_layout()
        plt.savefig(CLEANED_DIR / 'viz_flight_count_by_airline.png', dpi=150)
        plt.close()

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        gender_counts = passengers_masked['gender'].value_counts()
        axes[0].pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', colors=['#38bdf8', '#ec4899'], startangle=140)
        axes[0].set_title('Passenger Gender Split', fontweight='bold')

        age_counts = passengers_masked['age_group'].value_counts().reindex(['Under 18', '18-30', '31-45', '46-60', '60+'])
        sns.barplot(x=age_counts.index, y=age_counts.values, ax=axes[1], palette='crest')
        axes[1].set_title('Passenger Age Groups', fontweight='bold')
        plt.tight_layout()
        plt.savefig(CLEANED_DIR / 'viz_passenger_demographics.png', dpi=150)
        plt.close()

        log.info("Charts saved to '%s'.", CLEANED_DIR)

    except Exception as e:
        log.warning("Could not generate charts (non-fatal): %s", e)

    log.info("Pipeline complete.")


if __name__ == '__main__':
    run()
