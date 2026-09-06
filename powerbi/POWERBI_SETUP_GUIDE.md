# Power BI Dashboard Setup Guide

This guide details how to build the ASG Airlines interactive reporting suite in Power BI Desktop utilizing data from **all 4 core operational tables**: `flights`, `bookings`, `passengers`, and `payments`.

---

## Loading Data into Power BI

### Step 1: Import the Master Dataset (Unified 4-Way Model)

1. Open **Power BI Desktop**
2. Click **Home → Get Data → Text/CSV**
3. Navigate to: `data/cleaned/master_dataset.csv`
4. Click **Load**

> **Note:** `master_dataset.csv` is a comprehensive denormalized fact table joining **all 4 tables**:
> $$\text{Bookings} \Join \text{Flights} \Join \text{Payments} \Join \text{Passengers}$$
> It includes flight schedules, durations, delays, financial amounts, payment methods, and passenger demographics (`age`, `age_group`, `gender`, `birth_year`, masked identifiers).

---

### Step 2: Import KPI Aggregation Tables

Repeat **Home → Get Data → Text/CSV** for each file in `data/aggregated/`:

| File | Table Name in Power BI | Description / Domain |
|---|---|---|
| `kpi_route_traffic.csv` | `RouteTraffic` | Flight volume, delays, and overnight status per route |
| `kpi_avg_duration_by_airline.csv` | `AvgDurationAirline` | Average, min, max flight duration by airline |
| `kpi_avg_duration_by_route.csv` | `AvgDurationRoute` | Average duration and flight count by route |
| `kpi_airline_distribution.csv` | `AirlineDistribution` | Airline market share and flight counts |
| `kpi_delay_summary.csv` | `DelaySummary` | Delay volumes and delay rate (%) by airline |
| `kpi_revenue_by_airline.csv` | `RevenueByAirline` | Total revenue, average ticket price by airline |
| `kpi_departure_slots.csv` | `DepartureSlots` | Flight count by time-of-day slots |
| `kpi_booking_status.csv` | `BookingStatus` | Confirmed vs Cancelled bookings count |
| `kpi_payment_methods.csv` | `PaymentMethods` | Revenue and transactions by payment method |
| `kpi_passenger_demographics.csv` | `PassengerDemographics` | Bookings, revenue, and passenger count by gender & age group |
| `kpi_frequent_flyers.csv` | `FrequentFlyers` | Top travelers ranked by booking volume and lifetime spend |
| `kpi_airline_passenger_demographics.csv` | `AirlinePassengerDemographics` | Demographic breakdown of travelers across airlines |

*(Optional Dimension Tables)*: If preferring a normalized star schema, you can also load `cleaned_passengers_masked.csv`, `cleaned_flights.csv`, and `cleaned_bookings_masked.csv` from `data/cleaned/`.

---

### Step 3: Set Data Types (Transform Data)

Open **Transform Data (Power Query)** and set:

| Column | Recommended Type | Table(s) |
|---|---|---|
| `departure_time` | Date/Time | `master_dataset`, `cleaned_flights` |
| `arrival_time` | Date/Time | `master_dataset`, `cleaned_flights` |
| `departure_date` | Date | `master_dataset`, `cleaned_flights` |
| `booking_date` | Date | `master_dataset`, `cleaned_bookings_masked` |
| `duration_mins` | Decimal Number | `master_dataset`, `cleaned_flights` |
| `amount` | Decimal Number | `master_dataset`, `cleaned_payments`, `RevenueByAirline` |
| `is_delayed` | Whole Number | `master_dataset`, `cleaned_flights` |
| `is_overnight` | Whole Number | `master_dataset`, `cleaned_flights` |
| `age` | Whole Number | `master_dataset`, `cleaned_passengers_masked` |
| `birth_year` | Whole Number | `master_dataset`, `cleaned_passengers_masked` |
| `gender` | Text | `master_dataset`, `PassengerDemographics` |
| `age_group` | Text | `master_dataset`, `PassengerDemographics` |

---

### Step 4: Recommended Dashboard Pages

#### Page 1 — Operations Overview
- **KPI Card:** Total Flights (`COUNTROWS(cleaned_flights)`)
- **KPI Card:** Average Duration (`AVERAGE(master_dataset[duration_mins])`)
- **KPI Card:** Delay Rate %
- **KPI Card:** Total Revenue (INR)
- **KPI Card:** Total Unique Passengers
- **Donut Chart:** Airline Market Share (`AirlineDistribution`)
- **Line/Area Chart:** Daily flight volume over time

#### Page 2 — Duration Analysis
- **Bar Chart:** Average Duration by Route (`AvgDurationRoute`)
- **Histogram:** Flight Duration Distribution (`master_dataset[duration_mins]`)
- **Clustered Bar:** Average Duration by Airline (`AvgDurationAirline`)
- **Slicers:** Airline, Departure Slot

#### Page 3 — Route Performance
- **Matrix / Heatmap:** Source Airport vs Destination Airport volume (`RouteTraffic`)
- **Bar Chart:** Top 10 Busiest Flight Routes
- **Table:** Route traffic metrics with delay rate %
- **Slicers:** Source City, Destination City

#### Page 4 — Airline & Commercial Trends
- **Bar Chart:** Total Flights by Airline (`AirlineDistribution`)
- **Stacked Bar:** Delayed vs On-Time Flights by Airline (`DelaySummary`)
- **Bar Chart:** Total Revenue by Airline (`RevenueByAirline`)
- **Donut Chart:** Payment Method Split by Revenue (`PaymentMethods`)
- **Pie Chart:** Booking Status Breakdown (Confirmed vs Cancelled)

#### Page 5 — Delay & Anomaly Insights
- **Bar Chart:** Delay Rate (%) by Airline (`DelaySummary`)
- **KPI Card:** Route with Highest Delay Rate
- **Table:** Delayed Flights Detail (`master_dataset` filtered `is_delayed = 1`)
- **Bar Chart:** Overnight Flights Count by Airline
- **Slicers:** Airline, Time Slot, Is Delayed

#### Page 6 — Passenger & Customer Demographics (New)
- **KPI Card:** Total Unique Passengers (`DISTINCTCOUNT(master_dataset[passenger_id])`)
- **KPI Card:** Average Passenger Age (`AVERAGE(master_dataset[age])`)
- **KPI Card:** Average Spend per Passenger (`[Total Revenue] / [Total Unique Passengers]`)
- **Donut Chart:** Passenger Gender Split (`PassengerDemographics`)
- **Clustered Column Chart:** Total Revenue and Bookings by Age Group (`Under 18`, `18-30`, `31-45`, `46-60`, `60+`)
- **Matrix / Leaderboard:** Top Frequent Travelers (`FrequentFlyers`: masked name, total bookings, confirmed count, total spend)
- **Stacked Bar:** Airline Passenger Demographics (`AirlinePassengerDemographics`: age group & gender breakdown per airline)
- **Slicers:** Passenger Gender, Age Group, Airline

---

### Step 5: Recommended Slicers (Global & Page-Level)
- **Airline** (dropdown)
- **Route / Cities** (search dropdown)
- **Departure Time Slot** (Early Morning, Morning, Afternoon, Evening, Night)
- **Booking Status** (CONFIRMED / CANCELLED)
- **Passenger Gender** (M / F)
- **Passenger Age Group** (`Under 18`, `18-30`, `31-45`, `46-60`, `60+`)
- **Date Range** (Timeline slider on `departure_date`)

---

### Step 6: Core DAX Measures

```dax
// 1. Average Flight Duration (Minutes)
Avg Duration = AVERAGE(master_dataset[duration_mins])

// 2. Flight Delay Rate (%)
Delay Rate % = 
DIVIDE(
    COUNTROWS(FILTER(master_dataset, master_dataset[is_delayed] = 1)),
    COUNTROWS(master_dataset),
    0
) * 100

// 3. Total Commercial Revenue (INR)
Total Revenue = SUM(master_dataset[amount])

// 4. Overnight Flights Percentage (%)
Overnight % = 
DIVIDE(
    COUNTROWS(FILTER(master_dataset, master_dataset[is_overnight] = 1)),
    COUNTROWS(master_dataset),
    0
) * 100

// 5. Total Unique Passengers
Total Unique Passengers = DISTINCTCOUNT(master_dataset[passenger_id])

// 6. Average Passenger Age
Avg Passenger Age = AVERAGE(master_dataset[age])

// 7. Average Spend per Passenger
Avg Spend per Passenger = 
DIVIDE([Total Revenue], [Total Unique Passengers], 0)

// 8. Booking Confirmation Rate (%)
Confirmation Rate % = 
DIVIDE(
    COUNTROWS(FILTER(master_dataset, master_dataset[status] = "CONFIRMED")),
    COUNTROWS(master_dataset),
    0
) * 100
```
