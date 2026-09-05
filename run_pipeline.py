"""
ASG Airlines — Data Pipeline Runner
Run this script directly to produce all cleaned CSVs and KPI aggregations.
"""

import hashlib
import logging
from pathlib import Path

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
RAW_DIR     = BASE_DIR / 'data' / 'raw'
CLEANED_DIR = BASE_DIR / 'data' / 'cleaned'
AGG_DIR     = BASE_DIR / 'data' / 'aggregated'
RAW_FILE    = RAW_DIR / 'UseCase - Airlines.xlsx'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger('ASG-Pipeline')

# ── 1. Load ────────────────────────────────────────────────────────────────────
log.info('Loading raw data from: %s', RAW_FILE)
raw = {}
for sheet in ['flights', 'bookings', 'passengers', 'payments']:
    df = pd.read_excel(RAW_FILE, sheet_name=sheet)
    df = df[[c for c in df.columns if not str(c).startswith('Unnamed')]]
    raw[sheet] = df
    log.info('Loaded [%s]: %d rows', sheet, len(df))

# ── 2. Clean Flights ───────────────────────────────────────────────────────────
flights = raw['flights'].copy()
drop_cols = [c for c in flights.columns if str(c).startswith('Unnamed') or c == 'duration']
flights.drop(columns=drop_cols, errors='ignore', inplace=True)
flights.columns = ['flight_id', 'airline', 'source', 'destination', 'departure_time', 'arrival_time']

for col in ['flight_id', 'airline', 'source', 'destination']:
    flights[col] = flights[col].astype(str).str.strip().str.upper()

flights['departure_time'] = pd.to_datetime(flights['departure_time'], errors='coerce')
flights['arrival_time']   = pd.to_datetime(flights['arrival_time'],   errors='coerce')

before = len(flights)
flights.dropna(subset=['flight_id', 'source', 'destination', 'departure_time', 'arrival_time'], inplace=True)
log.info('Dropped %d rows with null critical fields', before - len(flights))

before = len(flights)
flights.drop_duplicates(inplace=True)
log.info('Dropped %d fully duplicate rows', before - len(flights))

before = len(flights)
flights.drop_duplicates(subset=['flight_id'], keep='first', inplace=True)
log.info('Dropped %d duplicate flight_id rows', before - len(flights))

flights = flights[flights['arrival_time'] > flights['departure_time']]

AIRLINE_MAP = {'AI': 'Air India', 'SJ': 'SpiceJet', '6F': 'IndiGo', 'UK': 'Vistara', 'G8': 'Go First'}

def impute_airline(row):
    if row['airline'] == 'UNKNOWN':
        return AIRLINE_MAP.get(str(row['flight_id'])[:2], 'UNKNOWN')
    return row['airline']

flights['airline'] = flights.apply(impute_airline, axis=1)

# Drop remaining rows where airline is NaN or the literal string 'NAN'
before = len(flights)
flights = flights[~flights['airline'].isin(['NAN', '', 'NONE'])]
flights.dropna(subset=['airline'], inplace=True)
log.info('Dropped %d rows with unresolvable airline', before - len(flights))

flights['duration_mins'] = (
    (flights['arrival_time'] - flights['departure_time']).dt.total_seconds() / 60
).round(2)
flights['is_overnight'] = (
    flights['arrival_time'].dt.date > flights['departure_time'].dt.date
).astype(int)
flights = flights[(flights['duration_mins'] > 0) & (flights['duration_mins'] <= 1440)]
flights['duration_hhmm'] = flights['duration_mins'].apply(lambda m: f'{int(m)//60}h {int(m)%60}m')
flights['route']         = flights['source'] + ' to ' + flights['destination']


def time_bucket(dt):
    h = dt.hour
    if 5 <= h < 9:   return 'Early Morning'
    if 9 <= h < 12:  return 'Morning'
    if 12 <= h < 17: return 'Afternoon'
    if 17 <= h < 21: return 'Evening'
    return 'Night'


flights['departure_slot'] = flights['departure_time'].apply(time_bucket)
route_avg = flights.groupby('route')['duration_mins'].transform('mean')
flights['is_delayed']     = (flights['duration_mins'] > route_avg * 1.30).astype(int)
flights['departure_date'] = flights['departure_time'].dt.date
flights['arrival_date']   = flights['arrival_time'].dt.date
flights['departure_hour'] = flights['departure_time'].dt.hour
log.info('Flights after cleaning: %d', len(flights))

# ── 3. Clean Passengers ────────────────────────────────────────────────────────
passengers = raw['passengers'].copy()
passengers['passenger_id'] = passengers['passenger_id'].astype(str).str.strip()
passengers['gender']       = passengers['gender'].astype(str).str.upper().str.strip()
passengers['email']        = passengers['email'].astype(str).str.lower().str.strip()
passengers['date_of_birth']= pd.to_datetime(passengers['date_of_birth'], errors='coerce')
passengers.drop_duplicates(inplace=True)

# ── 4. Clean Bookings ──────────────────────────────────────────────────────────
bookings = raw['bookings'].copy()
bookings = bookings[[
    'booking_id', 'passenger_id', 'flight_id', 'booking_date', 'status',
    'passport_number', 'seat_number', 'emergency_contact_name', 'emergency_contact_phone'
]]
for col in ['booking_id', 'passenger_id']:
    bookings[col] = bookings[col].astype(str).str.strip()
bookings['flight_id']    = bookings['flight_id'].astype(str).str.strip().str.upper()
bookings['status']       = bookings['status'].astype(str).str.upper().str.strip()
bookings['booking_date'] = pd.to_datetime(bookings['booking_date'], errors='coerce')
bookings.drop_duplicates(inplace=True)

# ── 5. Clean Payments ──────────────────────────────────────────────────────────
payments = raw['payments'].copy()
payments['payment_method'] = payments['payment_method'].astype(str).str.upper().str.strip()
payments['amount']         = pd.to_numeric(payments['amount'], errors='coerce')
payments.drop_duplicates(inplace=True)
payments.dropna(subset=['amount'], inplace=True)

# ── 6. PII Masking ─────────────────────────────────────────────────────────────
SALT = 'ASG_AIRLINES_2026_SECURE_SALT'


def sha256_hash(value):
    if pd.isna(value) or str(value).strip() in ('', 'nan', 'None'):
        return None
    return hashlib.sha256(f'{SALT}:{value}'.encode()).hexdigest()


def pseudo_name(value):
    if pd.isna(value) or len(str(value)) == 0:
        return '***'
    return str(value)[0] + '***'


pax_masked = passengers.copy()
pax_masked['aadhaar_id_hash']   = pax_masked['aadhaar_id'].astype(str).apply(sha256_hash)
pax_masked['email_hash']        = pax_masked['email'].astype(str).apply(sha256_hash)
pax_masked['phone_hash']        = pax_masked['phone'].astype(str).apply(sha256_hash)
pax_masked['first_name_masked'] = pax_masked['first_name'].apply(pseudo_name)
pax_masked['last_name_masked']  = pax_masked['last_name'].apply(pseudo_name)
pax_masked['birth_year']        = pax_masked['date_of_birth'].dt.year
pax_masked.drop(columns=['aadhaar_id', 'email', 'phone', 'first_name', 'last_name', 'date_of_birth'], inplace=True)

bk_masked = bookings.copy()
bk_masked['passport_hash']   = bk_masked['passport_number'].astype(str).apply(sha256_hash)
bk_masked['emg_phone_hash']  = bk_masked['emergency_contact_phone'].astype(str).apply(sha256_hash)
bk_masked['emg_name_masked'] = bk_masked['emergency_contact_name'].apply(pseudo_name)
bk_masked.drop(columns=['passport_number', 'emergency_contact_phone', 'emergency_contact_name'], inplace=True)

# ── 7. KPI Aggregations ────────────────────────────────────────────────────────
avg_by_airline = (
    flights.groupby('airline')['duration_mins']
    .agg(['mean', 'min', 'max', 'count']).round(2)
    .rename(columns={'mean': 'avg_duration_mins', 'min': 'min_duration_mins',
                     'max': 'max_duration_mins', 'count': 'flight_count'})
    .reset_index().sort_values('avg_duration_mins', ascending=False)
)

avg_by_route = (
    flights.groupby('route')['duration_mins']
    .agg(['mean', 'count']).round(2)
    .rename(columns={'mean': 'avg_duration_mins', 'count': 'flight_count'})
    .reset_index().sort_values('avg_duration_mins', ascending=False)
)

route_traffic = (
    flights.groupby('route')
    .agg(flight_count=('flight_id', 'count'), avg_duration=('duration_mins', 'mean'),
         delayed_flights=('is_delayed', 'sum'), overnight_flights=('is_overnight', 'sum'))
    .round(2).reset_index().sort_values('flight_count', ascending=False)
)
route_traffic['delay_rate_%'] = (
    route_traffic['delayed_flights'] / route_traffic['flight_count'] * 100
).round(2)

delay_summary = (
    flights.groupby('airline')
    .agg(total_flights=('flight_id', 'count'), delayed_flights=('is_delayed', 'sum'),
         overnight_count=('is_overnight', 'sum'))
    .reset_index()
)
delay_summary['delay_rate_%'] = (
    delay_summary['delayed_flights'] / delay_summary['total_flights'] * 100
).round(2)

airline_dist = (
    flights.groupby('airline')
    .agg(flight_count=('flight_id', 'count'), avg_duration_mins=('duration_mins', 'mean'),
         min_duration_mins=('duration_mins', 'min'), max_duration_mins=('duration_mins', 'max'))
    .round(2).reset_index().sort_values('flight_count', ascending=False)
)
airline_dist['market_share_%'] = (
    airline_dist['flight_count'] / airline_dist['flight_count'].sum() * 100
).round(2)

booking_rev = bk_masked.merge(payments, on='booking_id', how='left')
booking_rev = booking_rev.merge(flights[['flight_id', 'airline', 'route']], on='flight_id', how='left')
revenue_by_airline = (
    booking_rev.groupby('airline')['amount']
    .agg(['sum', 'mean', 'count'])
    .rename(columns={'sum': 'total_revenue', 'mean': 'avg_ticket_price', 'count': 'bookings_with_payment'})
    .round(2).reset_index().sort_values('total_revenue', ascending=False)
)

slot_traffic        = flights.groupby('departure_slot')['flight_id'].count().reset_index().rename(columns={'flight_id': 'flight_count'})
booking_status      = bk_masked.groupby('status')['booking_id'].count().reset_index().rename(columns={'booking_id': 'count'})
payment_method_dist = payments.groupby('payment_method')['amount'].agg(['count', 'sum']).round(2).reset_index()

# ── 8. Export ──────────────────────────────────────────────────────────────────
flights_export = flights[[
    'flight_id', 'airline', 'source', 'destination', 'route',
    'departure_time', 'arrival_time', 'duration_mins', 'duration_hhmm',
    'is_overnight', 'departure_slot', 'is_delayed',
    'departure_date', 'arrival_date', 'departure_hour'
]]

flights_export.to_csv(CLEANED_DIR / 'cleaned_flights.csv', index=False)
pax_masked.to_csv(CLEANED_DIR / 'cleaned_passengers_masked.csv', index=False)
bk_masked.to_csv(CLEANED_DIR / 'cleaned_bookings_masked.csv', index=False)
payments.to_csv(CLEANED_DIR / 'cleaned_payments.csv', index=False)

master = (
    bk_masked
    .merge(flights_export, on='flight_id', how='left')
    .merge(payments[['booking_id', 'amount', 'payment_method']], on='booking_id', how='left')
)
master.to_csv(CLEANED_DIR / 'master_dataset.csv', index=False)

route_traffic.to_csv(AGG_DIR / 'kpi_route_traffic.csv', index=False)
avg_by_airline.to_csv(AGG_DIR / 'kpi_avg_duration_by_airline.csv', index=False)
avg_by_route.to_csv(AGG_DIR / 'kpi_avg_duration_by_route.csv', index=False)
airline_dist.to_csv(AGG_DIR / 'kpi_airline_distribution.csv', index=False)
delay_summary.to_csv(AGG_DIR / 'kpi_delay_summary.csv', index=False)
revenue_by_airline.to_csv(AGG_DIR / 'kpi_revenue_by_airline.csv', index=False)
slot_traffic.to_csv(AGG_DIR / 'kpi_departure_slots.csv', index=False)
booking_status.to_csv(AGG_DIR / 'kpi_booking_status.csv', index=False)
payment_method_dist.to_csv(AGG_DIR / 'kpi_payment_methods.csv', index=False)

# ── 9. Summary ─────────────────────────────────────────────────────────────────
print('=' * 60)
print('     ASG AIRLINES - PIPELINE EXECUTION SUMMARY')
print('=' * 60)
print(f'  Raw flights          : {len(raw["flights"])} rows')
print(f'  Clean flights        : {len(flights)} rows')
print(f'  Overnight flights    : {flights["is_overnight"].sum()}')
print(f'  Delayed flights      : {flights["is_delayed"].sum()}')
print(f'  Delay rate           : {flights["is_delayed"].mean()*100:.1f}%')
print(f'  Avg duration         : {flights["duration_mins"].mean():.1f} mins')
print(f'  Unique routes        : {flights["route"].nunique()}')
print(f'  Master dataset       : {master.shape[0]} rows x {master.shape[1]} cols')
print()
print('  CLEANED FILES:')
for f in sorted(CLEANED_DIR.iterdir()):
    size_kb = f.stat().st_size // 1024
    print(f'    {f.name:<45} {size_kb} KB')
print()
print('  KPI FILES:')
for f in sorted(AGG_DIR.iterdir()):
    size_kb = f.stat().st_size // 1024
    print(f'    {f.name:<45} {size_kb} KB')
print('=' * 60)
print('  Pipeline completed successfully!')
print('=' * 60)
