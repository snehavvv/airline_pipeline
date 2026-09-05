# ✈️ ASG Airlines — End-to-End Data Engineering Pipeline

## Repository Contents

| File | Description |
|------|-------------|
| `ASG_Airlines_Pipeline.ipynb` | Complete data engineering notebook — ingestion, cleaning, transformation, PII masking, KPI aggregation, visualisations |
| `ASG_Airlines_Documentation.md` | Full documentation — architecture, data model, cleaning logic, assumptions, KPI definitions, Power BI guide |
| `ASG_Airlines_Dashboard.pbix` | Power BI dashboard *(add after export from Power BI Desktop)* |

## Pipeline Summary

- **Source:** `UseCase - Airlines.xlsx` (4 sheets: flights, bookings, passengers, payments)
- **Tool Stack:** Python · pandas · matplotlib · seaborn · Jupyter Notebook · Power BI
- **Output:** Cleaned CSVs + 9 KPI aggregation tables ready for Power BI

## Key KPIs
- Average Flight Duration (overall, per airline, per route)
- Route-wise Traffic with Delay Rate
- Overnight Flight Detection
- Airline Market Share
- Revenue by Airline
- Departure Slot Analysis
- PII masked: Aadhaar, email, phone, passport (SHA-256)

## How to Run

```bash
pip install pandas numpy matplotlib seaborn openpyxl jupyter
jupyter notebook ASG_Airlines_Pipeline.ipynb
```
