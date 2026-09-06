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
10. [Power BI Report & Dashboard Deliverables](#10-power-bi-report--dashboard-deliverables)

---

## 1. Project Overview

**Client:** ASG Airlines  
**Objective:** Build an end-to-end local Python data pipeline to ingest, clean, transform, and export flight operational and customer data across **all 4 core tables** (`flights`, `bookings`, `passengers`, `payments`) for BI reporting.  
**Tools:** Python 3.10+, pandas, numpy, matplotlib, seaborn, Jupyter Notebook, Power BI Desktop  
**Approach:** Local pipeline (Python/Jupyter) — no cloud dependencies required.

---

## 2. Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAW DATA LAYER                           │
│   UseCase - Airlines.xlsx                                       │
│   ├── Sheet: flights    (1,020 rows)                            │
│   ├── Sheet: bookings   (1,000 rows)                            │
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
│   • Parse datetime columns safely with coerce                   │
│   • Impute UNKNOWN airlines via flight_id prefix                │
│   • Calculate duration_mins (overnight-aware)                   │
│   • Flag is_overnight flights & departure_slots                 │
│   • Derive route & heuristic is_delayed flag                    │
│   • Segment passengers by age_group (<18, 18-30, 31-45, etc.)   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PII MASKING                               │
│   • SHA-256 hash: aadhaar_id, email, phone, passport            │
│   • Pseudonymise: first_name, last_name, emergency contacts     │
│   • Generalise: date_of_birth → birth_year                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     KPI AGGREGATION                             │
│   • Flights: avg_duration, route_traffic, delay_summary,        │
│     airline_distribution, departure_slots                       │
│   • Bookings & Payments: revenue_by_airline, booking_status,    │
│     payment_methods                                             │
│   • Passengers (Customer Intelligence): passenger_demographics, │
│     frequent_flyers (loyalty), airline_passenger_demographics   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXPORT LAYER                               │
│   data/cleaned/      → 5 CSV files (All 4 tables + Unified Master)
│   data/aggregated/   → 12 KPI CSV files                         │
│   data/cleaned/      → 8 PNG visualisation charts               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 POWER BI REPORT (.PBIX)                         │
│   powerbi/ASG_Airlines_Dashboard.pbix (Ready-to-use .pbix)     │
│   powerbi/dashboard_screenshot.png (Executive preview)          │
│   powerbi/screenshots/ (Page-by-page visual dashboards)         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Dataset Structure

### 3.1 flights Sheet

| Column | Type | Description | Issues Found |
|---|---|---|---|
| `flight_id` | string | Unique flight identifier (e.g. AI155, SJ010) | 16 duplicate IDs |
| `airline` | string | Airline name | 31 UNKNOWN values |
| `source` | string | IATA departure airport code | Minor nulls |
| `destination` | string | IATA arrival airport code | Minor nulls |
| `departure_time` | datetime | Scheduled departure (full datetime) | None |
| `arrival_time` | datetime | Scheduled arrival (full datetime) | Overnight flights span next day |
| `duration` | formula | Excel formula string `=F2-E2` | Recalculated in pipeline |

### 3.2 bookings Sheet

| Column | Type | Description |
|---|---|---|
| `booking_id` | string | Unique booking identifier |
| `passenger_id` | string | FK → passengers |
| `flight_id` | string | FK → flights |
| `booking_date` | datetime | When the booking was created |
| `status` | string | CONFIRMED / CANCELLED |
| `passport_number` | string | **PII** — hashed (SHA-256) |
| `seat_number` | string | Assigned seat |
| `emergency_contact_name` | string | **PII** — pseudonymised |
| `emergency_contact_phone` | string | **PII** — hashed (SHA-256) |

### 3.3 passengers Sheet

| Column | Type | Description |
|---|---|---|
| `passenger_id` | string | Unique passenger identifier |
| `first_name` | string | **PII** — pseudonymised (`F***`) |
| `last_name` | string | **PII** — pseudonymised (`L***`) |
| `age` | integer | Passenger age (1 to 89) |
| `gender` | string | Standardized (M / F) |
| `email` | string | **PII** — hashed (SHA-256) |
| `phone` | string | **PII** — hashed (SHA-256) |
| `aadhaar_id` | string | **Highly Sensitive PII** — hashed (SHA-256) |
| `date_of_birth` | date | **PII** — birth_year retained for analytics |
| `age_group` *(derived)* | string | `<18`, `18-30`, `31-45`, `46-60`, `60+` |

### 3.4 payments Sheet

| Column | Type | Description |
|---|---|---|
| `payment_id` | string | Unique payment identifier |
| `booking_id` | string | FK → bookings |
| `amount` | float | Payment amount in INR |
| `payment_method` | string | UPI / NETBANKING / CREDIT_CARD / DEBIT_CARD |

---

## 4. Data Cleaning Logic & Strategy

### 4.1 Flights Cleaning Steps

| Step | Action | Reason |
|---|---|---|
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

| Prefix | Airline |
|---|---|
| `AI` | Air India |
| `SJ` | SpiceJet |
| `6F` | IndiGo |
| `UK` | Vistara |
| `G8` | Go First |

### 4.3 Passengers & Bookings Cleaning
- Standardize `gender` to uppercase (`M` / `F`).
- Ensure `age` is numeric; derive `age_group` bins (`Under 18`, `18-30`, `31-45`, `46-60`, `60+`).
- Lowercase `email` addresses before hashing.
- Parse `date_of_birth` and `booking_date` with `errors='coerce'`.
- Drop duplicate rows.

---

## 5. Transformation Steps

### 5.1 Duration Calculation
```python
flights['duration_mins'] = (
    (flights['arrival_time'] - flights['departure_time'])
    .dt.total_seconds() / 60
).round(2)
```

### 5.2 Overnight Flag
```python
flights['is_overnight'] = (
    flights['arrival_time'].dt.date > flights['departure_time'].dt.date
).astype(int)
```

### 5.3 Delay Flag
A flight is flagged as delayed if its duration exceeds 130% of the average duration for that route:
```python
route_avg = flights.groupby('route')['duration_mins'].transform('mean')
flights['is_delayed'] = (flights['duration_mins'] > route_avg * 1.30).astype(int)
```

### 5.4 Departure Time Slot
- Early Morning: 05:00 – 08:59
- Morning: 09:00 – 11:59
- Afternoon: 12:00 – 16:59
- Evening: 17:00 – 20:59
- Night: 21:00 – 04:59

### 5.5 Demographic Age Grouping
```python
def assign_age_group(age):
    if pd.isna(age):  return 'Unknown'
    if age < 18:      return 'Under 18'
    if age <= 30:     return '18-30'
    if age <= 45:     return '31-45'
    if age <= 60:     return '46-60'
    return '60+'
```

---

## 6. PII Masking & Data Governance

- **SHA-256 Hashing (Salted):** Applied to `aadhaar_id`, `email`, `phone`, `passport_number`, and `emergency_contact_phone`.
- **Pseudonymisation:** `first_name`, `last_name`, and `emergency_contact_name` masked to initial + asterisks (e.g. `K***`).
- **Generalisation:** `date_of_birth` generalised to `birth_year`.

---

## 7. KPI Definitions (12 Total)

### Operational & Flight KPIs
| KPI | Formula | Output |
|---|---|---|
| **Average Flight Duration** | `mean(duration_mins)` per airline/route | Minutes |
| **Route-wise Traffic** | `count(flight_id)` per route | Flight count |
| **Delay Rate** | `sum(is_delayed) / count(flight_id) * 100` | Percentage |
| **Airline Distribution** | `count(flight_id)` per airline | Count + market share % |
| **Departure Slot Traffic** | `count(flight_id)` per time slot | Count |

### Commercial & Financial KPIs
| KPI | Formula | Output |
|---|---|---|
| **Revenue by Airline** | `sum(amount)` via bookings→payments join | INR |
| **Booking Status** | `count(booking_id)` per status | Count |
| **Payment Method Split** | `count + sum(amount)` per method | Count + INR |

### Passenger & Customer Intelligence KPIs
| KPI | Formula | Output |
|---|---|---|
| **Passenger Demographics** | `count(passenger_id)`, `count(booking_id)`, `sum(amount)` by gender & age group | Demographics summary |
| **Frequent Flyers / Loyalty** | Top passengers by booking frequency and total spend | Customer leaderboard |
| **Airline Demographics** | Passenger distribution by airline, gender, and age group | Preference matrix |

---

## 8. Data Model

### Relational Schema (All 4 Tables Unified)
```
passengers (1) ──────< bookings (M) >────── (1) flights
                            │
                            │ (1:1)
                            │
                         payments
```

### Unified Master Fact Table (`master_dataset.csv`)
All 4 tables are joined into a single wide dataset for Power BI reporting:
$$\text{Bookings} \Join \text{Flights} \Join \text{Payments} \Join \text{Passengers}$$

---

## 9. Assumptions

1. **Overnight flights**: Departure and arrival are stored as full datetimes, naturally resolving overnight journeys across midnight.
2. **UNKNOWN airline**: Imputed using flight ID 2-character prefixes (`AI`, `SJ`, `6F`, `UK`, `G8`).
3. **Delay heuristic**: Flight duration >30% above the route average indicates delays.
4. **All tables utilized**: All 4 raw tables (`flights`, `bookings`, `passengers`, `payments`) are ingested, cleaned, masked, aggregated, and joined into the analytical data model.

---

## 10. Power BI Report & Dashboard Deliverables

### 10.1 Key Power BI Files Included
- **Power BI File (.pbix):** [`powerbi/ASG_Airlines_Dashboard.pbix`](powerbi/ASG_Airlines_Dashboard.pbix)
- **Primary Dashboard Screenshot:** [`powerbi/dashboard_screenshot.png`](powerbi/dashboard_screenshot.png)
- **Automated Generation Script:** [`powerbi/generate_dashboard_and_screenshots.py`](powerbi/generate_dashboard_and_screenshots.py)

### 10.2 Executive Dashboard Overview
![ASG Airlines Executive Power BI Dashboard Preview](powerbi/screenshots/asg_airlines_dashboard_preview.png)

### 10.3 Interactive Visual Dashboard Pages

#### Page 1: Operations & Fleet Overview
- Executive KPI Cards: Total Revenue, Total Flights, Delay Rate, Unique Passengers, Avg Flight Duration.
- Flight Volume by Airline bar chart.
- Airline Market Share donut chart.
- Flight Duration Trends by Route column chart.
![Page 1: Operations Overview](powerbi/screenshots/01_operations_overview.png)

#### Page 2: Route & Delay Risk Performance
- Top 10 Busiest Flight Routes chart.
- Departure Time Slot Congestion analysis.
- Route Delay Rate (%) leaderboard.
![Page 2: Route & Delay Performance](powerbi/screenshots/02_route_delay_performance.png)

#### Page 3: Commercial & Financial Trends
- Gross Revenue by Airline breakdown.
- Payment Method Distribution (UPI, Credit Card, Netbanking, Debit Card).
- Booking Status Ratio (Confirmed vs. Cancelled).
![Page 3: Commercial Financial Trends](powerbi/screenshots/03_commercial_financial_trends.png)

#### Page 4: Passenger Demographics & Loyalty Analytics
- Passenger Age Group Distribution (<18, 18-30, 31-45, 46-60, 60+).
- Gender Share donut visual.
- Revenue contribution by Passenger Age Group.
- Customer Loyalty Leaderboard (Top Frequent Flyers by booking volume and total spend).
![Page 4: Passenger Demographics & Loyalty](powerbi/screenshots/04_passenger_demographics_loyalty.png)
