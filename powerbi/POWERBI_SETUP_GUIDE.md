# Power BI Dashboard Setup Guide

## Loading Data into Power BI

### Step 1: Import the Master Dataset (Primary Source)

1. Open **Power BI Desktop**
2. Click **Home → Get Data → Text/CSV**
3. Navigate to: `data/cleaned/master_dataset.csv`
4. Click **Load**

### Step 2: Import KPI Aggregation Tables

Repeat for each file in `data/aggregated/`:

| File | Table Name in Power BI |
|------|----------------------|
| `kpi_route_traffic.csv` | RouteTraffic |
| `kpi_avg_duration_by_airline.csv` | AvgDurationAirline |
| `kpi_avg_duration_by_route.csv` | AvgDurationRoute |
| `kpi_airline_distribution.csv` | AirlineDistribution |
| `kpi_delay_summary.csv` | DelaySummary |
| `kpi_revenue_by_airline.csv` | RevenueByAirline |
| `kpi_departure_slots.csv` | DepartureSlots |
| `kpi_booking_status.csv` | BookingStatus |
| `kpi_payment_methods.csv` | PaymentMethods |

### Step 3: Set Data Types (Transform Data)

Open **Transform Data (Power Query)** and set:

| Column | Type |
|--------|------|
| `departure_time` | Date/Time |
| `arrival_time` | Date/Time |
| `departure_date` | Date |
| `duration_mins` | Decimal Number |
| `is_delayed` | Whole Number |
| `is_overnight` | Whole Number |
| `amount` | Decimal Number |

### Step 4: Recommended Dashboard Pages

#### Page 1 — Operations Overview
- KPI Card: Total Flights
- KPI Card: Average Duration (mins)
- KPI Card: Overall Delay Rate (%)
- KPI Card: Overnight Flights Count
- KPI Card: Total Revenue (INR)
- Donut Chart: Airline Market Share
- Line Chart: Flights over time

#### Page 2 — Duration Analysis
- Bar Chart: Avg Duration by Route (from `AvgDurationRoute`)
- Histogram: Duration Distribution (from `master_dataset`)
- Clustered Bar: Avg Duration by Airline (from `AvgDurationAirline`)
- Slicer: Airline, Route

#### Page 3 — Route Performance
- Matrix/Heatmap: Source vs Destination flight count (from `RouteTraffic`)
- Bar Chart: Top 10 Busiest Routes
- Table: Route traffic with delay rate
- Slicer: Source city, Destination city

#### Page 4 — Airline Trends
- Bar Chart: Flights per Airline (from `AirlineDistribution`)
- Stacked Bar: Delayed vs On-time per Airline (from `DelaySummary`)
- Bar Chart: Revenue by Airline (from `RevenueByAirline`)
- Donut: Payment Method Split (from `PaymentMethods`)

#### Page 5 — Delay & Anomaly Insights
- Bar Chart: Delay Rate by Airline (from `DelaySummary`)
- KPI Card: Most Delayed Route
- Table: Delayed flights detail (from `master_dataset` filtered is_delayed=1)
- Bar Chart: Overnight flights by airline
- Slicer: Airline, is_delayed, departure_slot

### Step 5: Recommended Slicers (All Pages)
- Airline (dropdown)
- Route (dropdown or search)
- Departure Slot (checkbox list)
- Booking Status (radio)
- Date Range (date picker on departure_date)

### Step 6: DAX Measures to Create

```dax
// Average Duration
Avg Duration = AVERAGE(master_dataset[duration_mins])

// Delay Rate
Delay Rate % = 
DIVIDE(
    COUNTROWS(FILTER(master_dataset, master_dataset[is_delayed] = 1)),
    COUNTROWS(master_dataset),
    0
) * 100

// Total Revenue
Total Revenue = SUM(master_dataset[amount])

// Overnight %
Overnight % = 
DIVIDE(
    COUNTROWS(FILTER(master_dataset, master_dataset[is_overnight] = 1)),
    COUNTROWS(master_dataset),
    0
) * 100
```
