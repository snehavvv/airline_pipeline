# ✈️ ASG Airlines — End-to-End Data Engineering Pipeline & Power BI Dashboard

An end-to-end local data engineering pipeline and Power BI reporting suite built for ASG Airlines to ingest, clean, standardize, transform, and report on flight operations, bookings, passenger demographics, and payments.

---

## 📁 Repository Structure

```
airline_pipeline/
├── ASG_Airlines_Pipeline.ipynb     # Interactive Jupyter Notebook (Full ETL & EDA)
├── ASG_Airlines_Documentation.md    # Detailed technical documentation & case study
├── run_pipeline.py                 # Standalone automated ETL pipeline script
├── requirements.txt                # Python environment dependencies
├── .gitignore                      # Ignore raw sensitive data & build artifacts
├── README.md                       # Project overview and run guide
│
├── powerbi/
│   ├── POWERBI_SETUP_GUIDE.md      # Step-by-step Power BI guide with DAX measures
│   └── check_powerbi_files.py      # Verification script for Power BI data sources
│
└── data/
    ├── cleaned/                    # Cleaned & PII-masked analytical datasets
    │   ├── master_dataset.csv      # Primary analytical fact table
    │   ├── cleaned_flights.csv     # Cleaned flights (overnight-aware durations)
    │   ├── cleaned_bookings_masked.csv
    │   ├── cleaned_passengers_masked.csv
    │   ├── cleaned_payments.csv
    │   └── *.png                   # Generated analytical charts
    │
    └── aggregated/                 # Pre-aggregated KPI summary tables
        ├── kpi_route_traffic.csv
        ├── kpi_avg_duration_by_airline.csv
        ├── kpi_avg_duration_by_route.csv
        ├── kpi_airline_distribution.csv
        ├── kpi_delay_summary.csv
        ├── kpi_revenue_by_airline.csv
        ├── kpi_departure_slots.csv
        ├── kpi_booking_status.csv
        └── kpi_payment_methods.csv
```

---

## 🛠️ Tech Stack & Dependencies

- **Language:** Python 3.10+
- **Data Engineering:** pandas, numpy, openpyxl
- **Visualizations:** matplotlib, seaborn
- **Notebook & Reporting:** Jupyter Notebook, Power BI Desktop
- **Security & Privacy:** SHA-256 PII cryptographic hashing

To install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

### Option 1: Run the Automated Python Pipeline
```bash
python run_pipeline.py
```
This processes raw datasets, cleans anomalies, handles overnight flights, applies PII masking, and exports all cleaned & KPI CSVs.

### Option 2: Explore via Jupyter Notebook
```bash
jupyter notebook ASG_Airlines_Pipeline.ipynb
```

---

## 📊 Key Business Insights & KPIs

1. **Overnight Flight Logic**: Correctly handles cross-day flights where arrival time < departure time by adding 24 hours.
2. **Airline Imputation**: Missing or corrupted airline names restored using flight number prefixes (`AI*` → Air India, `6E*` → IndiGo, `SG*` → SpiceJet, etc.).
3. **Data Privacy & Governance**: All PII fields (Passenger Name, Email, Phone Number, Aadhaar, Passport) are cryptographically masked with SHA-256 hashes.
4. **Analytical Outputs**:
   - Route-wise flight volume & delay rates
   - Airline market share & revenue contributions
   - Average duration by route & carrier
   - Peak departure time slot distribution

---

## 📈 Power BI Setup

1. Run `python powerbi/check_powerbi_files.py` to ensure all data tables are present.
2. Open **Power BI Desktop** and load `data/cleaned/master_dataset.csv`.
3. Follow [`powerbi/POWERBI_SETUP_GUIDE.md`](powerbi/POWERBI_SETUP_GUIDE.md) to set up dashboard visuals, filters, and copy the provided DAX measures.
