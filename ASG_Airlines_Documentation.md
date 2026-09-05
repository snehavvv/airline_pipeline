# ASG Airlines — Data Engineering Pipeline: Full Documentation

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture & Data Flow](#2-architecture--data-flow)
3. [Dataset Structure](#3-dataset-structure)
4. [Data Cleaning Logic & Strategy](#4-data-cleaning-logic--strategy)
5. [Transformation Steps](#5-transformation-steps)
6. [PII Masking & Data Governance](#6-pii-masking--data-governance)
7. [KPI Definitions](#7-kpi-definitions)
8. [Data Model](#8-data-model)
9. [Assumptions](#9-assumptions)
10. [Power BI Dashboard Guide](#10-power-bi-dashboard-guide)

---

## 1. Project Overview

**Client:** ASG Airlines  
**Objective:** Build an end-to-end local Python data pipeline to ingest, clean, transform, and export flight operational data for BI reporting.  
**Tools:** Python 3.10, pandas, numpy, matplotlib, seaborn, Jupyter Notebook, Power BI Desktop  
**Approach:** Local pipeline (Python/Jupyter) — no cloud dependencies required.

---

## 2. Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAW DATA LAYER                           │
│   UseCase - Airlines.xlsx                                       │
│   ├── Sheet: flights    (1,020 rows)                            │
│   ├── Sheet: bookings   (1,012 rows)                            │
│   ├── Sheet: passengers (1,039 rows)                            │
│   └── Sheet: payments   (1,000 rows)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │  pandas.read_excel()
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION & VALIDATION                        │
│   • Schema validation (expected columns check)                  │
│   • Data quality report (nulls, dtypes, duplicates, uniques)    │
│   • Drop unnamed / formula-string columns                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLEANING & TRANSFORMATION                     │
│   • Handle null critical fields (drop rows)                     │
│   • Deduplicate (full row + flight_id level)                    │
│   • Standardize strings (upper/lower case, strip)               │
│   • Parse datetime columns                                      │
│   • Impute UNKNOWN airlines via flight_id prefix                │
│   • Calculate duration_mins (overnight-aware)                   │
│   • Flag is_overnight flights                                   │
│   • Derive route, departure_slot, is_delayed                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PII MASKING                               │
│   • SHA-256 hash: aadhaar_id, email, phone, passport            │
│   • Pseudonymise: first_name, last_name                         │
│   • Generalise: date_of_birth → birth_year                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     KPI AGGREGATION                             │
│   • avg_duration by airline & route                             │
│   • route_traffic (flight count + delay rate)                   │
│   • delay_summary by airline                                    │
│   • airline_distribution (market share)                         │
│   • revenue_by_airline                                          │
│   • departure_slots, booking_status, payment_methods            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXPORT LAYER                               │
│   data/cleaned/      → 5 CSV files (masked)                     │
│   data/aggregated/   → 9 KPI CSV files                          │
│   data/cleaned/      → 6 PNG visualisation charts               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    [Power BI Dashboard]
```

---

## 3. Dataset Structure

### 3.1 flights Sheet

| Column | Type | Description | Issues Found |
|--------|------|-------------|--------------|
| `flight_id` | string | Unique flight identifier (e.g. AI155, SJ010) | 16 duplicate IDs |
| `airline` | string | Airline name | 31 UNKNOWN values |
| `source` | string | IATA departure airport code | Minor: some nulls |
| `destination` | string | IATA arrival airport code | Minor: some nulls |
| `departure_time` | datetime | Scheduled departure (full datetime) | None |
| `arrival_time` | datetime | Scheduled arrival (full datetime) | Overnight flights span next day |
| `duration` | formula | Excel formula string `=F2-E2` | **Not usable** — recalculated |

**Additional unnamed columns** (cols 8–11): Empty Excel artifacts — dropped.

### 3.2 bookings Sheet

| Column | Type | Description |
|--------|------|-------------|
| `booking_id` | string | Unique booking identifier |
| `passenger_id` | string | FK → passengers |
| `flight_id` | string | FK → flights |
| `booking_date` | datetime | When the booking was created |
| `status` | string | CONFIRMED / CANCELLED |
| `passport_number` | string | **PII** — hashed |
| `seat_number` | string | Assigned seat |
| `emergency_contact_name` | string | **PII** — pseudonymised |
| `emergency_contact_phone` | string | **PII** — hashed |

### 3.3 passengers Sheet

| Column | Type | Description |
|--------|------|-------------|
| `passenger_id` | string | Unique passenger identifier |
| `first_name` | string | **PII** — pseudonymised |
| `last_name` | string | **PII** — pseudonymised |
| `age` | integer | Passenger age |
| `gender` | string | M / F |
| `email` | string | **PII** — hashed |
| `phone` | string | **PII** — hashed |
| `aadhaar_id` | string | **Highly Sensitive PII** — hashed |
| `date_of_birth` | date | **PII** — year only retained |

### 3.4 payments Sheet

| Column | Type | Description |
|--------|------|-------------|
| `payment_id` | string | Unique payment identifier |
| `booking_id` | string | FK → bookings |
| `amount` | float | Payment amount in INR |
| `payment_method` | string | UPI / NETBANKING / CREDIT_CARD / DEBIT_CARD |

---

## 4. Data Cleaning Logic & Strategy

### 4.1 Flights Cleaning Steps

| Step | Action | Reason |
|------|--------|--------|
| 1 | Drop `duration` column and unnamed cols | Duration is Excel formula string; unnamed cols are empty |
| 2 | Standardize column names | Ensure consistent naming |
| 3 | Strip/uppercase string columns | Removes leading/trailing whitespace inconsistencies |
| 4 | Parse datetime columns with `errors='coerce'` | Converts invalid dates to NaT safely |
| 5 | Drop rows with null critical fields | Cannot compute duration or route without times/cities |
| 6 | Drop full duplicate rows | Remove exact-copy records |
| 7 | Deduplicate on `flight_id` (keep first) | 16 duplicate flight IDs found |
| 8 | Drop rows where `arrival_time <= departure_time` | Logically invalid records |
| 9 | Impute UNKNOWN airline using `flight_id` prefix | 31 UNKNOWN airlines — prefix maps to carrier |
| 10 | Filter duration: 0 < duration_mins ≤ 1440 | Sanity check — no flight >24h or negative |

### 4.2 UNKNOWN Airline Imputation

Airlines were imputed using the industry-standard ICAO/IATA prefix convention:

| Prefix | Airline |
|--------|---------|
| `AI` | Air India |
| `SJ` | SpiceJet |
| `6F` | IndiGo |
| `UK` | Vistara |
| `G8` | Go First |

### 4.3 Passengers & Bookings Cleaning

- Standardize `gender` to uppercase (M/F)
- Lowercase `email` addresses
- Parse `date_of_birth` and `booking_date` with coerce
- Drop full duplicates

---

## 5. Transformation Steps

### 5.1 Duration Calculation

```python
flights['duration_mins'] = (
    (flights['arrival_time'] - flights['departure_time'])
    .dt.total_seconds() / 60
).round(2)
```

**Overnight flights** are correctly handled because both `departure_time` and `arrival_time` are stored as full datetime objects (not just time strings). Subtracting a next-day datetime from a same-day datetime naturally yields the correct positive duration — no manual +24h adjustment needed.

**Example:**
- Departure: `2026-04-20 23:38`
- Arrival: `2026-04-21 02:32`
- Duration: 174 minutes ✓

### 5.2 Overnight Flag

```python
flights['is_overnight'] = (
    flights['arrival_time'].dt.date > flights['departure_time'].dt.date
).astype(int)
```

### 5.3 Delay Flag

A flight is flagged as **delayed** if its duration exceeds 130% of the average duration for that specific route:

```python
route_avg = flights.groupby('route')['duration_mins'].transform('mean')
flights['is_delayed'] = (flights['duration_mins'] > route_avg * 1.30).astype(int)
```

**Rationale:** A 30% threshold over route average accounts for natural variation while flagging genuine anomalies. This is a heuristic — a production system would use scheduled vs actual times.

### 5.4 Departure Time Slot

| Slot | Hours |
|------|-------|
| Early Morning | 05:00 – 08:59 |
| Morning | 09:00 – 11:59 |
| Afternoon | 12:00 – 16:59 |
| Evening | 17:00 – 20:59 |
| Night | 21:00 – 04:59 |

### 5.5 Route Column

```python
flights['route'] = flights['source'] + ' to ' + flights['destination']
# e.g., "BOM to DEL"
```

---

## 6. PII Masking & Data Governance

### 6.1 Masking Techniques

**SHA-256 Hashing (with salt):**
```python
SALT = 'ASG_AIRLINES_2026_SECURE_SALT'

def sha256_hash(value):
    salted = f"{SALT}:{value}"
    return hashlib.sha256(salted.encode()).hexdigest()
```

Applied to: `aadhaar_id`, `email`, `phone`, `passport_number`, `emergency_contact_phone`

- One-way: original value cannot be recovered
- Deterministic: same input always produces same hash (enables cross-referencing within the system)
- Salted: prevents rainbow table attacks

**Pseudonymisation:**
```python
def pseudonymise_name(value):
    return str(value)[0] + '***'  # e.g., "Vivaan" → "V***"
```

Applied to: `first_name`, `last_name`, `emergency_contact_name`

**Generalisation:**
- `date_of_birth` → `birth_year` (only year retained for age-group analytics)

### 6.2 Access Control Recommendations

| Role | Access Level |
|------|-------------|
| Data Engineer | Full raw data access (secure environment only) |
| Analyst / BI Developer | Cleaned, masked CSVs only |
| Business User | Power BI dashboard (aggregated KPIs only) |
| External Auditor | Aggregated reports only, no individual records |

---

## 7. KPI Definitions

| KPI | Formula | Output |
|-----|---------|--------|
| **Average Flight Duration** | `mean(duration_mins)` per airline/route | Minutes |
| **Route-wise Traffic** | `count(flight_id)` per route | Flight count |
| **Delay Rate** | `sum(is_delayed) / count(flight_id) * 100` | Percentage |
| **Airline Distribution** | `count(flight_id)` per airline | Count + market share % |
| **Revenue by Airline** | `sum(amount)` via bookings→payments join | INR |
| **Overnight Flights** | `sum(is_overnight)` | Count |
| **Departure Slot Traffic** | `count(flight_id)` per time slot | Count |
| **Booking Status** | `count(booking_id)` per status | Count |
| **Payment Method Split** | `count + sum(amount)` per method | Count + INR |

---

## 8. Data Model

```
passengers (1) ──────< bookings (M) >────── (1) flights
                           │
                           │ (1:1)
                           │
                        payments
```

**Star Schema for Power BI:**

```
            ┌──────────────┐
            │  dim_flights │
            │  (fact table)│
            └──────┬───────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
┌─────▼────┐  ┌────▼─────┐ ┌───▼──────┐
│dim_airline│  │dim_route │ │dim_time  │
│           │  │          │ │          │
└───────────┘  └──────────┘ └──────────┘
```

**Files for Power BI:**
- `master_dataset.csv` — main denormalized fact table
- `kpi_*.csv` — pre-aggregated KPI tables for fast visuals

---

## 9. Assumptions

1. **Overnight flights**: The raw Excel stores full `datetime` values for departure and arrival. Overnight scenarios are correctly represented (arrival date is the next day). No manual day-offset is needed.

2. **UNKNOWN airline**: 31 records had `airline = UNKNOWN`. These were imputed using the flight_id prefix (e.g., AI → Air India). Records where prefix was unrecognized kept the UNKNOWN label.

3. **Delay definition**: Since scheduled vs actual departure/arrival times are not available, delay is defined heuristically as a duration >30% above the route mean. In a production system, this would use actual scheduled times.

4. **Duplicate flight_ids**: 16 flight IDs appeared more than once. The first occurrence was retained (assumed most recent/correct entry).

5. **Duration validity**: Flights with duration ≤ 0 or > 1440 minutes (24 hours) are considered data errors and removed.

6. **PII salt**: The salt value (`ASG_AIRLINES_2026_SECURE_SALT`) is hardcoded in the notebook. In production, this should be stored in an environment variable or secrets manager.

7. **Currency**: All payment amounts are assumed to be in Indian Rupees (INR).

---

## 10. Power BI Dashboard Guide

### Pages / Sections

| Page | Visuals |
|------|---------|
| **Overview** | KPI cards: total flights, avg duration, delay rate, overnight count |
| **Duration Analysis** | Avg duration by route (bar), duration distribution (histogram), duration by airline (box) |
| **Route Performance** | Route traffic heatmap, top routes by volume, route delay rate |
| **Airline Trends** | Market share (donut), flights per airline (bar), avg duration per airline |
| **Delay & Anomaly** | Delay rate by airline, delayed vs on-time (stacked bar), overnight flights map |

### Power BI Setup Instructions

1. Open Power BI Desktop
2. Get Data → Text/CSV → load `data/cleaned/master_dataset.csv`
3. Also load `data/aggregated/kpi_*.csv` files as separate tables
4. Use **Transform Data** to set correct data types:
   - `departure_time`, `arrival_time` → DateTime
   - `duration_mins` → Decimal Number
   - `is_delayed`, `is_overnight` → Whole Number
5. Create relationships:
   - `master_dataset[flight_id]` → `kpi_route_traffic` (optional for drill-through)
6. Build visuals using the KPI tables for aggregated views
7. Add slicers: Airline, Route, Departure Slot, Date Range
