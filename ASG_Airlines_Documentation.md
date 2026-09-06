# ASG Airlines — Data Engineering Pipeline: Full Documentation

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture & Data Flow Diagram](#2-architecture--data-flow-diagram)
3. [Dataset Structure & Raw Sample Data](#3-dataset-structure--raw-sample-data)
4. [Data Cleaning Logic & Enterprise Error Handling](#4-data-cleaning-logic--enterprise-error-handling)
5. [Transformation Steps](#5-transformation-steps)
6. [PII Masking & Data Governance](#6-pii-masking--data-governance)
7. [KPI Definitions & Creative Bonus KPIs](#7-kpi-definitions--creative-bonus-kpis)
8. [Relational Data Model & ERD Diagram](#8-relational-data-model--erd-diagram)
9. [Assumptions & Governance Principles](#9-assumptions--governance-principles)
10. [Power BI Report & Dashboard Deliverables](#10-power-bi-report--dashboard-deliverables)

---

## 1. Project Overview

**Client:** ASG Airlines  
**Objective:** Build an enterprise-grade local Python data engineering pipeline and Power BI reporting suite to ingest, clean, transform, govern, and report on flight operations, bookings, passenger demographics, and payments — **fully utilizing all 4 core operational tables** (`flights`, `bookings`, `passengers`, `payments`).  
**Tools:** Python 3.10+, pandas, numpy, matplotlib, seaborn, Jupyter Notebook, Power BI Desktop  
**Approach:** Local pipeline (Python/Jupyter) — fail-safe error handling with zero cloud dependencies required.

---

## 2. Architecture & Data Flow Diagram

The data engineering pipeline follows a modular 6-stage ETL/ELT architecture designed for reliability, cryptographic data governance, and automated BI integration.

### 🖼️ Visual Pipeline Architecture Diagram
![ASG Airlines Data Engineering Pipeline Architecture & Data Flow](docs/architecture_data_flow_diagram.png)

### 🔄 Stage-by-Stage Data Flow Description
1. **Raw Data Layer:** Ingests the multi-tab Excel workbook (`UseCase - Airlines.xlsx` or fallback `sample_usecase_airlines.xlsx`) containing 4 operational sheets: `flights`, `bookings`, `passengers`, and `payments`.
2. **Ingestion & Validation:** Validates expected schema columns, detects missing sheets, strips Excel formula strings (`duration`), and drops unreferenced unnamed columns.
3. **Cleaning & Transformation:** Deduplicates records, resolves 31 `UNKNOWN` airlines via flight number prefix lookup (`AI*` → Air India, `SJ*` → SpiceJet, `6F*` → IndiGo, `UK*` → Vistara, `G8*` → Go First), corrects overnight flight duration calculations spanning midnight, and derives passenger age groups (`<18`, `18-30`, `31-45`, `46-60`, `60+`).
4. **PII Masking & Data Governance:** Applies salted **SHA-256 cryptographic hashing** to sensitive identifiers (`aadhaar_id`, `email`, `phone`, `passport_number`, `emergency_contact_phone`) and initial-pseudonymization to names (`first_name`, `last_name`, `emergency_contact_name`).
5. **KPI Aggregation Engine:** Calculates 12 analytical summary tables spanning operations, financials, time-slot congestion, customer demographics, and frequent flyer loyalty.
6. **Power BI Report & Export Layer:** Exports 5 cleaned CSVs (including a unified 4-way `master_dataset.csv`), 12 KPI summary CSVs, 8 matplotlib visual charts, and compiles the ready-to-use [`powerbi/ASG_Airlines_Dashboard.pbix`](../powerbi/ASG_Airlines_Dashboard.pbix) report file.

---

## 3. Dataset Structure & Raw Sample Data

### 3.1 Out-of-the-Box Sample Dataset Included
To allow immediate end-to-end evaluation without requiring manual file placement, the repository commits a pre-built sample Excel workbook:
- **Sample Dataset Path:** [`data/raw/sample_usecase_airlines.xlsx`](../data/raw/sample_usecase_airlines.xlsx)
- **Full Production Workbook Path:** `data/raw/UseCase - Airlines.xlsx` *(gitignored for sensitive data protection; automatically detected if present)*.

### 3.2 Schema Specifications Across All 4 Sheets

#### `flights` Sheet (1,020 rows)
| Column | Type | Description | Issues & Handling |
|---|---|---|---|
| `flight_id` | string | Unique flight identifier | Deduplicated (16 duplicate IDs dropped) |
| `airline` | string | Carrier name | Imputed 31 `UNKNOWN` values via flight prefix |
| `source` | string | Departure airport (IATA) | Upper-cased & whitespace stripped |
| `destination` | string | Arrival airport (IATA) | Upper-cased & whitespace stripped |
| `departure_time` | datetime | Scheduled departure | Datetime coerced safely |
| `arrival_time` | datetime | Scheduled arrival | Datetime coerced; overnight span handled |
| `duration` | formula | Excel formula string | Dropped and recomputed cleanly in minutes |

#### `bookings` Sheet (1,000 rows)
| Column | Type | Description | Governance & Masking |
|---|---|---|---|
| `booking_id` | string | Unique booking ID | Upper-cased PK |
| `passenger_id` | string | FK → passengers | Joined for customer analytics |
| `flight_id` | string | FK → flights | Joined for operational analytics |
| `booking_date` | datetime | Booking timestamp | Parsed safely |
| `status` | string | Booking status | Standardized (`CONFIRMED` / `CANCELLED`) |
| `passport_number` | string | Passport number | **PII** — Hashed (Salted SHA-256) |
| `seat_number` | string | Seat allocation | Upper-cased |
| `emergency_contact_name` | string | Contact name | **PII** — Pseudonymized (`K***`) |
| `emergency_contact_phone` | string | Contact phone | **PII** — Hashed (Salted SHA-256) |

#### `passengers` Sheet (1,039 rows)
| Column | Type | Description | Governance & Masking |
|---|---|---|---|
| `passenger_id` | string | Unique passenger ID | Upper-cased PK |
| `first_name` | string | Given name | **PII** — Pseudonymized (`R***`) |
| `last_name` | string | Surname | **PII** — Pseudonymized (`K***`) |
| `age` | integer | Passenger age | Numeric coerced (1 to 89 years) |
| `gender` | string | Passenger gender | Standardized (`M` / `F`) |
| `email` | string | Email address | **PII** — Hashed (Salted SHA-256) |
| `phone` | string | Phone number | **PII** — Hashed (Salted SHA-256) |
| `aadhaar_id` | string | National ID number | **Highly Sensitive PII** — Hashed (Salted SHA-256) |
| `date_of_birth` | date | Birth date | **PII** — Converted to `birth_year` for analytics |
| `age_group` *(derived)* | string | Age bin | Derived (`<18`, `18-30`, `31-45`, `46-60`, `60+`) |

#### `payments` Sheet (1,000 rows)
| Column | Type | Description | Handling |
|---|---|---|---|
| `payment_id` | string | Unique transaction ID | Upper-cased PK |
| `booking_id` | string | FK → bookings | 1:1 join entity |
| `amount` | float | Fare amount (INR) | Numeric coerced & null rows dropped |
| `payment_method` | string | Payment channel | Standardized (`UPI`, `CREDIT_CARD`, `NETBANKING`, `DEBIT_CARD`) |

---

## 4. Data Cleaning Logic & Enterprise Error Handling

### 4.1 Enterprise Fail-Safe Exception Handling Strategy
Unlike standard scripts that crash on unexpected data anomalies, `run_pipeline.py` implements a multi-tiered error handling and validation structure:

```python
try:
    raw_path = resolve_raw_file()
    excel_file = pd.ExcelFile(raw_path)
    # Schema validation & sheet existence checks
except Exception as e:
    log.error("CRITICAL: Failed to ingest raw dataset: %s", e, exc_info=True)
    sys.exit(1)
```

#### Key Resilience Guards:
1. **Dynamic File Discovery:** Searches primary production directory (`data/raw/UseCase - Airlines.xlsx`), parent directory, and fallback sample dataset (`sample_usecase_airlines.xlsx`).
2. **Schema & Sheet Validation:** Verifies that all 4 required sheets exist prior to processing. If a sheet is missing, raises `PipelineDataError` with descriptive diagnostics.
3. **Column Type Coercion:** Uses `pd.to_datetime(..., errors='coerce')` and `pd.to_numeric(..., errors='coerce')` to prevent invalid formatting crashes.
4. **Non-Fatal Visualization Fallback:** Visual rendering code is wrapped in `try...except` so an environment without a display server will not halt dataset generation.
5. **Comprehensive Audit Logging:** Tracks exact row drop counts across null fields, duplicate flight IDs, invalid overnight times, and unresolvable airlines.

---

## 5. Transformation Steps

### 5.1 Overnight Flight Duration Calculation
```python
flights['duration_mins'] = (
    (flights['arrival_time'] - flights['departure_time']).dt.total_seconds() / 60
).round(2)
flights['is_overnight'] = (
    flights['arrival_time'].dt.date > flights['departure_time'].dt.date
).astype(int)
```

### 5.2 Heuristic Delay Flagging
Flights exceeding 130% of their specific route's average flight duration are flagged as delayed:
```python
route_avg = flights.groupby('route')['duration_mins'].transform('mean')
flights['is_delayed'] = (flights['duration_mins'] > route_avg * 1.30).astype(int)
```

### 5.3 Departure Time Slot Categorization
- **Early Morning:** 05:00 – 08:59
- **Morning:** 09:00 – 11:59
- **Afternoon:** 12:00 – 16:59
- **Evening:** 17:00 – 20:59
- **Night:** 21:00 – 04:59

---

## 6. PII Masking & Data Governance

To satisfy strict enterprise data governance standards:
- **Salted SHA-256 Hashing:** `aadhaar_id`, `email`, `phone`, `passport_number`, and `emergency_contact_phone` are cryptographically hashed using SHA-256 with a unique salt string (`ASGAirlines2026`).
- **Pseudonymization:** `first_name`, `last_name`, and `emergency_contact_name` are masked to initial format (`K***`).
- **Generalization:** `date_of_birth` is truncated to `birth_year`, ensuring zero PII leakage while enabling age demographic analysis.

---

## 7. KPI Definitions & Creative Bonus KPIs

The pipeline computes **12 KPI Aggregations**, explicitly categorised into core requirements and **7 Creative Bonus KPIs** added to maximize business value.

### 📊 Summary Table of All 12 KPIs

| KPI File | Category | Type | Business Metric / Description |
|---|---|---|---|
| `kpi_route_traffic.csv` | Operational | Core Requirement | Total flight count, avg duration & delay rate by route |
| `kpi_avg_duration_by_airline.csv` | Operational | Core Requirement | Min, max, and avg flight duration per carrier |
| `kpi_avg_duration_by_route.csv` | Operational | Core Requirement | Route-level benchmark flight duration |
| `kpi_airline_distribution.csv` | Operational | Core Requirement | Flight volume and market share % by airline |
| `kpi_delay_summary.csv` | Operational | Core Requirement | Total flights, delayed flights, overnight count & delay % |
| `kpi_revenue_by_airline.csv` | Commercial | 🌟 Creative Bonus KPI | Total revenue (INR), total bookings, and avg ticket yield per airline |
| `kpi_departure_slots.csv` | Operational | 🌟 Creative Bonus KPI | Flight volume and delay exposure across time-of-day slots |
| `kpi_booking_status.csv` | Commercial | 🌟 Creative Bonus KPI | Confirmed vs. Cancelled booking volume & percentage split |
| `kpi_payment_methods.csv` | Financial | 🌟 Creative Bonus KPI | Payment gateway share (UPI, Credit Card, Netbanking, Debit Card) |
| `kpi_passenger_demographics.csv` | Customer | 🌟 Creative Bonus KPI | Unique passengers, booking count & spend by age group and gender |
| `kpi_frequent_flyers.csv` | Loyalty | 🌟 Creative Bonus KPI | Customer loyalty leaderboard (top 20 passengers by volume & spend) |
| `kpi_airline_passenger_demographics.csv` | Customer | 🌟 Creative Bonus KPI | Cross-airline customer demographic preference matrix |

---

## 8. Relational Data Model & ERD Diagram

The architecture incorporates a 4-way unified relational star schema joining all core entities into a master fact dataset (`master_dataset.csv`):

$$\text{Bookings} \Join \text{Flights} \Join \text{Payments} \Join \text{Passengers}$$

### 🖼️ Visual Relational ERD Diagram
![ASG Airlines Relational Data Model & ERD Diagram](docs/relational_data_model_diagram.png)

---

## 9. Assumptions & Governance Principles

1. **100% Core Table Utilization:** All 4 operational sheets (`flights`, `bookings`, `passengers`, `payments`) are ingested, cleaned, masked, aggregated, and joined into the data model.
2. **Overnight Flight Logic:** Full datetime parsing handles midnight-crossing flights seamlessly without negative duration anomalies.
3. **Carrier Prefix Imputation:** 31 missing carrier names are accurately restored via flight number prefixes (`AI`, `SJ`, `6F`, `UK`, `G8`).
4. **Data Privacy First:** Zero raw PII fields are exposed in analytical CSV outputs or BI models.

---

## 10. Power BI Report & Dashboard Deliverables

### 10.1 Key Power BI Files Included
- **Power BI File (.pbix):** [`powerbi/ASG_Airlines_Dashboard.pbix`](../powerbi/ASG_Airlines_Dashboard.pbix)
- **Primary Dashboard Screenshot:** [`powerbi/dashboard_screenshot.png`](../powerbi/dashboard_screenshot.png)
- **Automated Generation Script:** [`powerbi/generate_dashboard_and_screenshots.py`](../powerbi/generate_dashboard_and_screenshots.py)

### 10.2 Executive Dashboard Overview
![ASG Airlines Executive Power BI Dashboard Preview](../powerbi/screenshots/asg_airlines_dashboard_preview.png)

### 10.3 Interactive Visual Dashboard Pages

#### Page 1: Operations & Fleet Overview
![Page 1: Operations Overview](../powerbi/screenshots/01_operations_overview.png)

#### Page 2: Route & Delay Risk Performance
![Page 2: Route & Delay Performance](../powerbi/screenshots/02_route_delay_performance.png)

#### Page 3: Commercial & Financial Trends
![Page 3: Commercial Financial Trends](../powerbi/screenshots/03_commercial_financial_trends.png)

#### Page 4: Passenger Demographics & Loyalty Analytics
![Page 4: Passenger Demographics & Loyalty](../powerbi/screenshots/04_passenger_demographics_loyalty.png)
