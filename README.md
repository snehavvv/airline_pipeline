# ✈️ ASG Airlines — End-to-End Data Engineering Pipeline & Power BI Dashboard

An enterprise-grade, fail-safe local data engineering pipeline and interactive Power BI reporting suite built for ASG Airlines to ingest, clean, standardize, transform, govern, and report on flight operations, bookings, passenger demographics, and payments — **fully utilizing all 4 core operational tables**.

---

> 📖 **Solution Architecture & Workflow Walkthrough:** Read the complete standalone narrative walkthrough in [`Solution_Walkthrough.md`](Solution_Walkthrough.md).

---

## 📊 Power BI Dashboard Preview & Interactive Report

The repository includes a ready-to-use **Power BI Report File (`.pbix`)** with 4 interactive dashboard pages, real-time KPI metrics, DAX measures, dark/glassmorphic executive aesthetics, and interactive visual filtering.

### 🖼️ Executive Dashboard Hero Preview
![ASG Airlines Power BI Executive Dashboard Preview](powerbi/screenshots/asg_airlines_dashboard_preview.png)

### 📁 Primary Power BI Deliverables
- **Power BI Report File:** [`powerbi/ASG_Airlines_Dashboard.pbix`](powerbi/ASG_Airlines_Dashboard.pbix) *(373 KB complete Power BI report model with data, measures, layout, and visual pages)*
- **Main Dashboard Screenshot:** [`powerbi/dashboard_screenshot.png`](powerbi/dashboard_screenshot.png)
- **High-Resolution Page Screenshots:** [`powerbi/screenshots/`](powerbi/screenshots/)
  - `01_operations_overview.png` — Executive KPIs, flight volume, airline market share, duration trends
  - `02_route_delay_performance.png` — Route heatmaps, departure time slot congestion, delay risk rates
  - `03_commercial_financial_trends.png` — Revenue per airline, payment gateway splits, booking status distribution
  - `04_passenger_demographics_loyalty.png` — Passenger age/gender distribution, revenue by age group, top frequent flyers

---

## 🏗️ Architecture & Data Flow Diagram

### 🖼️ Visual Architecture Diagram
![ASG Airlines Data Engineering Pipeline Architecture & Data Flow](docs/architecture_data_flow_diagram.png)

### 🖼️ Relational Data Model & ERD Schema
![ASG Airlines Relational Data Model & ERD Schema](docs/relational_data_model_diagram.png)

---

## 🌟 Creative & Bonus KPIs Beyond Basic Requirements

In addition to all basic required KPIs (Route Traffic, Airline Duration, Route Duration, Airline Distribution, Delay Summary), the pipeline explicitly calculates **7 Creative Bonus KPIs** to unlock deeper commercial, financial, customer, and operational insights:

| KPI File | Category | Business Value & Metric Description |
|---|---|---|
| `kpi_revenue_by_airline.csv` | Commercial | 🌟 Total gross revenue (INR), booking volume & avg ticket yield per carrier |
| `kpi_booking_status.csv` | Commercial | 🌟 Conversion vs. Cancellation volume & percentage distribution |
| `kpi_payment_methods.csv` | Financial | 🌟 Payment gateway share & transaction volume (UPI, Credit Card, Netbanking, Debit Card) |
| `kpi_passenger_demographics.csv` | Customer | 🌟 Unique passengers, booking count & spend by age group and gender |
| `kpi_frequent_flyers.csv` | Customer Loyalty | 🌟 Top 20 customer leaderboard ranked by booking frequency & total spend |
| `kpi_airline_passenger_demographics.csv` | Customer | 🌟 Cross-airline customer preference & demographic segment matrix |
| `kpi_departure_slots.csv` | Operational | 🌟 Flight volume & delay risk exposure by departure time-of-day slots |

---

## 🛡️ Enterprise Error Handling & Data Quality

`run_pipeline.py` is engineered with enterprise fail-safe exception handling:
- **Dynamic Raw File Discovery:** Automatically detects `data/raw/UseCase - Airlines.xlsx` or falls back to the committed sample dataset [`data/raw/sample_usecase_airlines.xlsx`](data/raw/sample_usecase_airlines.xlsx).
- **Try/Except Exception Guards:** Prevents pipeline crashes by catching IO errors, corrupted sheets, and unexpected missing columns with explicit logging diagnostic tracebacks.
- **Salted SHA-256 PII Protection:** Cryptographically hashes Aadhaar, Passport, Email, and Phone numbers with a salt (`ASGAirlines2026`) ensuring 100% compliance with data privacy standards.

---

## 📁 Repository Structure

```
airline_pipeline/
├── ASG_Airlines_Pipeline.ipynb     # Interactive Jupyter Notebook (Full ETL, EDA & Analytics)
├── ASG_Airlines_Documentation.md    # Comprehensive technical documentation & case study
├── run_pipeline.py                 # Standalone fail-safe ETL pipeline script
├── requirements.txt                # Python environment dependencies
├── .gitignore                      # Ignore raw sensitive production data & build artifacts
├── README.md                       # Project overview and run guide
│
├── docs/
│   ├── architecture_data_flow_diagram.png # Visual Architecture & Data Flow PNG
│   ├── relational_data_model_diagram.png # Visual Relational ERD Schema PNG
│   └── generate_diagrams.py        # Python script to regenerate visual diagrams
│
├── powerbi/
│   ├── ASG_Airlines_Dashboard.pbix # ⭐ Built Power BI Report File (.pbix)
│   ├── dashboard_screenshot.png    # Primary Executive Dashboard Screenshot
│   ├── POWERBI_SETUP_GUIDE.md      # Step-by-step Power BI setup & DAX guide
│   ├── check_powerbi_files.py      # Verification script for Power BI data sources
│   ├── generate_dashboard_and_screenshots.py # Script to rebuild .pbix & render screenshots
│   └── screenshots/                # High-resolution visual dashboard screenshots
│
└── data/
    ├── raw/
    │   └── sample_usecase_airlines.xlsx # ⭐ Out-of-the-box runnable sample raw dataset
    │
    ├── cleaned/                    # Cleaned & PII-masked analytical datasets
    │   ├── master_dataset.csv      # 4-way unified fact table (Bookings+Flights+Payments+Passengers)
    │   ├── cleaned_flights.csv     # Cleaned flights (overnight-aware durations)
    │   ├── cleaned_bookings_masked.csv
    │   ├── cleaned_passengers_masked.csv
    │   ├── cleaned_payments.csv
    │   └── *.png                   # Analytical charts (operations + passenger demographics)
    │
    └── aggregated/                 # 12 pre-aggregated KPI summary tables
        ├── kpi_route_traffic.csv
        ├── kpi_avg_duration_by_airline.csv
        ├── kpi_avg_duration_by_route.csv
        ├── kpi_airline_distribution.csv
        ├── kpi_delay_summary.csv
        ├── kpi_revenue_by_airline.csv               # (Bonus) Airline revenue yield
        ├── kpi_departure_slots.csv                  # (Bonus) Departure slot congestion
        ├── kpi_booking_status.csv                   # (Bonus) Cancellation vs confirmed ratio
        ├── kpi_payment_methods.csv                  # (Bonus) Payment gateway distribution
        ├── kpi_passenger_demographics.csv           # (Bonus) Gender & Age group demographics
        ├── kpi_frequent_flyers.csv                  # (Bonus) Customer loyalty leaderboard
        └── kpi_airline_passenger_demographics.csv   # (Bonus) Cross-airline passenger profiles
```

---

## 🛠️ Tech Stack & Dependencies

- **Language:** Python 3.10+
- **Data Engineering:** pandas, numpy, openpyxl
- **Visualizations:** matplotlib, seaborn, PIL/Pillow
- **Reporting & BI:** Power BI Desktop (`.pbix`), DAX, DataModelSchema
- **Security & Privacy:** SHA-256 PII cryptographic hashing with salt & pseudonymisation

To install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

### Option 1: Open the Power BI Dashboard Directly
Double-click [`powerbi/ASG_Airlines_Dashboard.pbix`](powerbi/ASG_Airlines_Dashboard.pbix) to open the report directly in Power BI Desktop with all 4 dashboard pages, interactive slicers, and data models pre-configured.

### Option 2: Run the Automated Fail-Safe Pipeline (Out-of-the-Box)
```bash
python run_pipeline.py
```
*Note: If the full `data/raw/UseCase - Airlines.xlsx` file is present, it will process the production data; otherwise, it seamlessly processes `data/raw/sample_usecase_airlines.xlsx`.*

### Option 3: Regenerate Power BI (.pbix) & Screenshots Programmatically
```bash
python powerbi/generate_dashboard_and_screenshots.py
```

### Option 4: Explore via Jupyter Notebook
```bash
jupyter notebook ASG_Airlines_Pipeline.ipynb
```
