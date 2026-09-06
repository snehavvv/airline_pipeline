"""
ASG Airlines — Architectural & Data Model Diagram Generator
Generates publication-quality visual PNG diagrams for repository documentation.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_architecture_diagram(output_path: Path):
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    ax.axis('off')

    plt.title("ASG AIRLINES — END-TO-END DATA PIPELINE ARCHITECTURE & DATA FLOW", 
              fontsize=15, fontweight='bold', color='#f8fafc', pad=25)

    stages = [
        {
            "num": "1",
            "title": "RAW DATA LAYER",
            "subtitle": "Excel Workbook Ingestion\n(UseCase - Airlines.xlsx)",
            "items": ["• flights (1,020 rows)", "• bookings (1,000 rows)", "• passengers (1,039 rows)", "• payments (1,000 rows)"],
            "x": 0.08, "bg": "#1e293b", "border": "#3b82f6"
        },
        {
            "num": "2",
            "title": "INGESTION & VALIDATION",
            "subtitle": "Data Quality Checks",
            "items": ["• Schema validation", "• Unnamed column drop", "• Datetime parse (coerce)", "• Empty sheet detection"],
            "x": 0.25, "bg": "#1e293b", "border": "#06b6d4"
        },
        {
            "num": "3",
            "title": "CLEANING & TRANSFORM",
            "subtitle": "Business Rule Logic",
            "items": ["• Deduplication (16 IDs)", "• Impute UNKNOWN airline", "• Overnight duration fix", "• Age group segmentation"],
            "x": 0.42, "bg": "#1e293b", "border": "#10b981"
        },
        {
            "num": "4",
            "title": "PII GOVERNANCE",
            "subtitle": "Cryptographic Security",
            "items": ["• SHA-256 Hashing:", "  Aadhaar, Email, Phone", "• Pseudonymization:", "  First/Last Names"],
            "x": 0.59, "bg": "#1e293b", "border": "#8b5cf6"
        },
        {
            "num": "5",
            "title": "KPI AGGREGATION",
            "subtitle": "Analytics Engine",
            "items": ["• 12 Aggregated Tables", "• Demographics & Loyalty", "• Delay & Duration KPIs", "• Revenue per Airline"],
            "x": 0.76, "bg": "#1e293b", "border": "#f59e0b"
        },
        {
            "num": "6",
            "title": "POWER BI & EXPORT",
            "subtitle": "Reporting & Storage",
            "items": ["• master_dataset.csv", "• 12 KPI Summary CSVs", "• Matplotlib Visuals", "• ASG_Airlines_Dashboard.pbix"],
            "x": 0.93, "bg": "#1e293b", "border": "#ec4899"
        }
    ]

    for s in stages:
        cx = s["x"]
        w, h = 0.14, 0.65
        rect = patches.FancyBboxPatch((cx - w/2, 0.18), w, h, boxstyle="round,pad=0.03", 
                                     facecolor=s["bg"], edgecolor=s["border"], linewidth=2.5)
        ax.add_patch(rect)
        
        circle = patches.Circle((cx, 0.82), 0.025, facecolor=s["border"], edgecolor="#ffffff", lw=1.5)
        ax.add_patch(circle)
        ax.text(cx, 0.82, s["num"], color="#ffffff", fontsize=11, fontweight='bold', ha='center', va='center')
        
        ax.text(cx, 0.74, s["title"], color="#ffffff", fontsize=10, fontweight='bold', ha='center', va='center')
        ax.text(cx, 0.67, s["subtitle"], color="#94a3b8", fontsize=8, fontweight='bold', ha='center', va='center')
        
        ax.plot([cx - w/2 + 0.015, cx + w/2 - 0.015], [0.62, 0.62], color=s["border"], lw=1.5, alpha=0.6)
        ax.text(cx, 0.42, "\n".join(s["items"]), color="#cbd5e1", fontsize=8, ha='center', va='center', multialignment='left')

    for i in range(len(stages) - 1):
        x1 = stages[i]["x"] + 0.075
        x2 = stages[i+1]["x"] - 0.075
        ax.annotate('', xy=(x2, 0.50), xytext=(x1, 0.50),
                    arrowprops=dict(arrowstyle='->', color='#e2e8f0', lw=2.5, mutation_scale=15))

    rect_bot = patches.FancyBboxPatch((0.01, 0.03), 0.98, 0.09, boxstyle="round,pad=0.01", 
                                     facecolor="#1e293b", edgecolor="#475569", linewidth=1.5)
    ax.add_patch(rect_bot)
    ax.text(0.5, 0.075, "Automated Fail-safe Pipeline (Logging & Error Handling)  |  100% Core Table Utilization  |  Zero PII Exposure Guarantee", 
            color="#38bdf8", fontsize=10, fontweight='bold', ha='center', va='center')

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', facecolor='#0f172a')
    plt.close()
    print(f"Architecture diagram created: {output_path}")

def create_data_model_diagram(output_path: Path):
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    ax.axis('off')

    plt.title("ASG AIRLINES — RELATIONAL DATA MODEL & UNIFIED FACT SCHEMA", 
              fontsize=15, fontweight='bold', color='#f8fafc', pad=25)

    entities = [
        {
            "name": "passengers (Dimension)",
            "x": 0.15, "y": 0.68, "w": 0.22, "h": 0.40,
            "header_bg": "#8b5cf6", "border": "#a78bfa",
            "cols": [
                "[PK] passenger_id",
                "• first_name (Pseudonymized)",
                "• last_name (Pseudonymized)",
                "• age (integer)",
                "• gender (M / F)",
                "• age_group (<18, 18-30, etc.)",
                "[PII] email (SHA-256 Hash)",
                "[PII] phone (SHA-256 Hash)",
                "[PII] aadhaar_id (SHA-256 Hash)"
            ]
        },
        {
            "name": "bookings (Bridge/Fact)",
            "x": 0.50, "y": 0.68, "w": 0.22, "h": 0.40,
            "header_bg": "#3b82f6", "border": "#60a5fa",
            "cols": [
                "[PK] booking_id",
                "[FK] passenger_id -> passengers",
                "[FK] flight_id -> flights",
                "• booking_date (datetime)",
                "• status (CONFIRMED/CANCELLED)",
                "• seat_number (string)",
                "[PII] passport_number (SHA-256)",
                "• emergency_contact_name",
                "[PII] emergency_contact_phone"
            ]
        },
        {
            "name": "flights (Dimension)",
            "x": 0.85, "y": 0.68, "w": 0.22, "h": 0.40,
            "header_bg": "#10b981", "border": "#34d399",
            "cols": [
                "[PK] flight_id",
                "• airline (Imputed)",
                "• source (IATA code)",
                "• destination (IATA code)",
                "• route (SRC-DST)",
                "• departure_time (datetime)",
                "• arrival_time (datetime)",
                "• duration_mins (numeric)",
                "• is_overnight (0/1)",
                "• is_delayed (0/1)"
            ]
        },
        {
            "name": "payments (Fact Attribute)",
            "x": 0.50, "y": 0.18, "w": 0.22, "h": 0.28,
            "header_bg": "#f59e0b", "border": "#fbbf24",
            "cols": [
                "[PK] payment_id",
                "[FK] booking_id -> bookings",
                "• amount (INR Float)",
                "• payment_method (UPI/CC/etc.)"
            ]
        }
    ]

    for e in entities:
        cx, cy, w, h = e["x"], e["y"], e["w"], e["h"]
        rect = patches.FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0.02", 
                                     facecolor="#1e293b", edgecolor=e["border"], linewidth=2)
        ax.add_patch(rect)
        
        header = patches.Rectangle((cx - w/2 + 0.005, cy + h/2 - 0.07), w - 0.01, 0.065, 
                                   facecolor=e["header_bg"], edgecolor="none")
        ax.add_patch(header)
        ax.text(cx, cy + h/2 - 0.038, e["name"], color="#ffffff", fontsize=9.5, fontweight='bold', ha='center', va='center')
        
        col_text = "\n".join(e["cols"])
        ax.text(cx - w/2 + 0.015, cy + h/2 - 0.10, col_text, color="#e2e8f0", fontsize=7.5, ha='left', va='top')

    ax.annotate('', xy=(0.39, 0.68), xytext=(0.26, 0.68),
                arrowprops=dict(arrowstyle='<->', color='#a78bfa', lw=2))
    ax.text(0.325, 0.70, "1 : N (passenger_id)", color="#a78bfa", fontsize=8, fontweight='bold', ha='center')

    ax.annotate('', xy=(0.74, 0.68), xytext=(0.61, 0.68),
                arrowprops=dict(arrowstyle='<->', color='#60a5fa', lw=2))
    ax.text(0.675, 0.70, "N : 1 (flight_id)", color="#60a5fa", fontsize=8, fontweight='bold', ha='center')

    ax.annotate('', xy=(0.50, 0.32), xytext=(0.50, 0.48),
                arrowprops=dict(arrowstyle='<->', color='#fbbf24', lw=2))
    ax.text(0.57, 0.40, "1 : 1 (booking_id)", color="#fbbf24", fontsize=8, fontweight='bold', ha='center')

    master_box = patches.FancyBboxPatch((0.05, 0.03), 0.90, 0.09, boxstyle="round,pad=0.01", 
                                        facecolor="#0284c7", edgecolor="#38bdf8", linewidth=2)
    ax.add_patch(master_box)
    ax.text(0.50, 0.075, "UNIFIED MASTER FACT DATASET (master_dataset.csv) = Bookings ⋈ Flights ⋈ Payments ⋈ Passengers", 
            color="#ffffff", fontsize=10.5, fontweight='bold', ha='center', va='center')

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', facecolor='#0f172a')
    plt.close()
    print(f"Data Model diagram created: {output_path}")

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = repo_root / "docs"
    create_architecture_diagram(docs_dir / "architecture_data_flow_diagram.png")
    create_data_model_diagram(docs_dir / "relational_data_model_diagram.png")
    
    asg_root = repo_root.parent / "ASG-Airlines-Pipeline"
    if asg_root.exists():
        asg_docs = asg_root / "docs"
        create_architecture_diagram(asg_docs / "architecture_data_flow_diagram.png")
        create_data_model_diagram(asg_docs / "relational_data_model_diagram.png")
