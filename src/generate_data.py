"""
src/generate_data.py
--------------------
Automated Synthetic Dataset Generator for 'Region-Wise Revenue Contribution Analysis'
Course: MCA 2nd Year (Data Analytics), ABES Engineering College
Faculty Mentor: Prof. Kalpna Dwivedi

Generates:
1. data/app.db (Normalized SQLite Database with Star Schema & DDL constraints)
2. data/dim_regions.csv, data/dim_products.csv, data/dim_customers.csv, data/fact_sales.csv
3. data/region_wise_revenue_data.xlsx (Multi-sheet Excel workbook)
4. view_sales_analysis (36-column denormalized SQL reporting view)
"""

import os
import sqlite3
import random
import csv
from datetime import datetime, timedelta

# Set deterministic random seed for strict scientific reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Paths configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")
EXCEL_PATH = os.path.join(DATA_DIR, "region_wise_revenue_data.xlsx")

os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------------------
# 1. Master Data Definitions (Fictional Indian Names, Places & Products)
# -------------------------------------------------------------------------

REGIONS_DATA = [
    # North Zone (Manager: Vikram Rathore)
    (1, "North", "Delhi NCR", "New Delhi", "Tier-1", "Vikram Rathore", 2500000.0),
    (2, "North", "Uttar Pradesh", "Noida", "Tier-1", "Vikram Rathore", 1800000.0),
    (3, "North", "Uttar Pradesh", "Lucknow", "Tier-2", "Vikram Rathore", 1200000.0),
    (4, "North", "Rajasthan", "Jaipur", "Tier-2", "Vikram Rathore", 1400000.0),
    (5, "North", "Punjab", "Chandigarh", "Tier-2", "Vikram Rathore", 1100000.0),

    # South Zone (Manager: S. Anantharaman)
    (6, "South", "Karnataka", "Bengaluru", "Tier-1", "S. Anantharaman", 3200000.0),
    (7, "South", "Tamil Nadu", "Chennai", "Tier-1", "S. Anantharaman", 2200000.0),
    (8, "South", "Telangana", "Hyderabad", "Tier-1", "S. Anantharaman", 2400000.0),
    (9, "South", "Kerala", "Kochi", "Tier-2", "S. Anantharaman", 950000.0),
    (10, "South", "Tamil Nadu", "Coimbatore", "Tier-2", "S. Anantharaman", 850000.0),

    # West Zone (Manager: Rajesh K. Gokhale)
    (11, "West", "Maharashtra", "Mumbai", "Tier-1", "Rajesh K. Gokhale", 3800000.0),
    (12, "West", "Maharashtra", "Pune", "Tier-1", "Rajesh K. Gokhale", 2100000.0),
    (13, "West", "Gujarat", "Ahmedabad", "Tier-2", "Rajesh K. Gokhale", 1600000.0),
    (14, "West", "Gujarat", "Surat", "Tier-2", "Rajesh K. Gokhale", 1300000.0),
    (15, "West", "Maharashtra", "Nagpur", "Tier-2", "Rajesh K. Gokhale", 900000.0),

    # East Zone (Manager: Sourav Chatterjee)
    (16, "East", "West Bengal", "Kolkata", "Tier-1", "Sourav Chatterjee", 1900000.0),
    (17, "East", "Odisha", "Bhubaneswar", "Tier-2", "Sourav Chatterjee", 950000.0),
    (18, "East", "Bihar", "Patna", "Tier-2", "Sourav Chatterjee", 800000.0),
    (19, "East", "Jharkhand", "Ranchi", "Tier-3", "Sourav Chatterjee", 650000.0),
    (20, "East", "Assam", "Guwahati", "Tier-3", "Sourav Chatterjee", 550000.0),

    # Central Zone (Manager: Manoj Deshmukh)
    (21, "Central", "Madhya Pradesh", "Indore", "Tier-2", "Manoj Deshmukh", 1100000.0),
    (22, "Central", "Madhya Pradesh", "Bhopal", "Tier-2", "Manoj Deshmukh", 900000.0),
    (23, "Central", "Chhattisgarh", "Raipur", "Tier-3", "Manoj Deshmukh", 700000.0),
    (24, "Central", "Madhya Pradesh", "Jabalpur", "Tier-3", "Manoj Deshmukh", 500000.0),
    (25, "Central", "Madhya Pradesh", "Gwalior", "Tier-3", "Manoj Deshmukh", 450000.0),
]

PRODUCTS_DATA = [
    # Electronics (High Ticket, Moderate Margin)
    (1, "PRD-E101", "UltraBook Pro Laptop 15-inch", "Electronics", 42000.0, 56000.0, 25.0),
    (2, "PRD-E102", "Noise-Cancelling Wireless Headphones", "Electronics", 4500.0, 7500.0, 40.0),
    (3, "PRD-E103", "Curved Gaming Monitor 27-inch", "Electronics", 14000.0, 19500.0, 28.2),
    (4, "PRD-E104", "Smartwatch Fitness Tracker GPS", "Electronics", 2800.0, 4999.0, 43.9),
    (5, "PRD-E105", "Mechanical Ergonomic Keyboard", "Electronics", 2200.0, 3800.0, 42.1),
    (6, "PRD-E106", "High-Speed Wi-Fi 6 Router", "Electronics", 1900.0, 3200.0, 40.6),

    # Apparel (High Volume, Variable Margin)
    (7, "PRD-A201", "Men Premium Cotton Formal Shirt", "Apparel", 650.0, 1499.0, 56.6),
    (8, "PRD-A202", "Women Embroidered Ethnic Kurti", "Apparel", 800.0, 1899.0, 57.8),
    (9, "PRD-A203", "Classic Slim-Fit Denim Jeans", "Apparel", 900.0, 2199.0, 59.0),
    (10, "PRD-A204", "Breathable Athletic Running Shoes", "Apparel", 1200.0, 2799.0, 57.1),
    (11, "PRD-A205", "Pure Wool Winter Cardigan", "Apparel", 1100.0, 2499.0, 55.9),
    (12, "PRD-A206", "Water-Resistant Commuter Backpack", "Apparel", 750.0, 1699.0, 55.8),

    # Home & Kitchen (Bulky, Higher Freight)
    (13, "PRD-H301", "Digital Air Fryer 4.5L Multi-Preset", "Home & Kitchen", 3200.0, 5499.0, 41.8),
    (14, "PRD-H302", "Tri-Ply Stainless Steel Cookware Set", "Home & Kitchen", 2400.0, 4299.0, 44.1),
    (15, "PRD-H303", "UV + UF Alkaline Water Purifier", "Home & Kitchen", 6500.0, 9999.0, 35.0),
    (16, "PRD-H304", "High-Suction Robotic Vacuum Cleaner", "Home & Kitchen", 11500.0, 17999.0, 36.1),
    (17, "PRD-H305", "750W Heavy-Duty Mixer Grinder", "Home & Kitchen", 1800.0, 3199.0, 43.7),
    (18, "PRD-H306", "Organic Cotton Queen Bedding Set", "Home & Kitchen", 950.0, 1999.0, 52.4),

    # Office Supplies (Steady Corporate Reorder)
    (19, "PRD-O401", "Ergonomic Lumbar Executive Chair", "Office Supplies", 5200.0, 8999.0, 42.2),
    (20, "PRD-O402", "Motorized Adjustable Standing Desk", "Office Supplies", 13000.0, 21500.0, 39.5),
    (21, "PRD-O403", "All-in-One Duplex Laser Printer", "Office Supplies", 8500.0, 13499.0, 37.0),
    (22, "PRD-O404", "Heavy-Duty Cross-Cut Paper Shredder", "Office Supplies", 2600.0, 4499.0, 42.2),
    (23, "PRD-O405", "A4 Copier Paper Bulk Box (5 Reams)", "Office Supplies", 850.0, 1350.0, 37.0),
    (24, "PRD-O406", "Aluminum Adjustable Laptop Stand", "Office Supplies", 550.0, 1199.0, 54.1),

    # Health & Beauty (Lightweight, High Margin)
    (25, "PRD-B501", "Organic Vitamin C Radiant Face Serum", "Health & Beauty", 250.0, 899.0, 72.1),
    (26, "PRD-B502", "Sonic Electric Toothbrush Smart Timer", "Health & Beauty", 850.0, 1899.0, 55.2),
    (27, "PRD-B503", "Pure Cold-Pressed Ayurvedic Hair Oil", "Health & Beauty", 180.0, 599.0, 69.9),
    (28, "PRD-B504", "Ultrasonic Aroma Oil Diffuser & Humidifier", "Health & Beauty", 620.0, 1499.0, 58.6),
    (29, "PRD-B505", "Broad Spectrum SPF 50 Gel Sunscreen", "Health & Beauty", 220.0, 649.0, 66.1),
    (30, "PRD-B506", "Whey Protein Isolate 1kg Chocolate", "Health & Beauty", 1450.0, 2799.0, 48.1),
]

INDIAN_FIRST_NAMES = [
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Bhavna", "Deepak", "Divya",
    "Gaurav", "Harsh", "Ishaan", "Kavita", "Manish", "Meera", "Naveen", "Neha",
    "Pooja", "Pranav", "Priya", "Rahul", "Rajesh", "Ritu", "Rohan", "Sanjay",
    "Shreya", "Siddharth", "Sneha", "Sunil", "Tanvi", "Varun", "Vikram", "Zoya"
]
INDIAN_LAST_NAMES = [
    "Agarwal", "Bansal", "Chatterjee", "Deshmukh", "Gupta", "Iyer", "Jain", "Joshi",
    "Kapoor", "Kulkarni", "Malhotra", "Mehta", "Nair", "Patel", "Pillai", "Prasad",
    "Rao", "Reddy", "Saxena", "Sen", "Sharma", "Singh", "Sundaram", "Verma"
]
SEGMENTS = ["Consumer", "Corporate", "Small Business"]

def generate_customers():
    customers = []
    start_date = datetime(2023, 1, 1)
    for cid in range(1, 101):
        c_code = f"CUST-{cid:04d}"
        fn = random.choice(INDIAN_FIRST_NAMES)
        ln = random.choice(INDIAN_LAST_NAMES)
        name = f"{fn} {ln}"
        seg = random.choice(SEGMENTS)
        c_type = "Returning" if random.random() < 0.65 else "New"
        days_offset = random.randint(0, 700)
        acq_date = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        reg_id = random.randint(1, 25)
        customers.append((cid, c_code, name, seg, c_type, acq_date, reg_id))
    return customers

CUSTOMERS_DATA = generate_customers()

# -------------------------------------------------------------------------
# 2. Transactional Fact Sales Generator with Embedded Realistic Patterns
# -------------------------------------------------------------------------

def generate_sales():
    sales = []
    order_num = 1000
    start_date = datetime(2024, 1, 1)
    
    # 250 main rows
    for i in range(1, 251):
        order_num += 1
        order_code = f"ORD-{order_num}"
        
        # Temporal Simulation: 24 months (Jan 2024 - Dec 2025)
        day_offset = random.randint(0, 720)
        order_dt = start_date + timedelta(days=day_offset)
        order_date_str = order_dt.strftime("%Y-%m-%d")
        month = order_dt.month
        
        # PATTERN 5: Q4 Festive Diwali Surge (Oct, Nov, Dec get higher volume/value)
        is_q4_festive = month in [10, 11, 12]
        
        # PATTERN 1: Regional Disparity (North and West selected more frequently)
        reg_weight = random.random()
        if reg_weight < 0.35:
            # North (IDs 1-5)
            region_id = random.randint(1, 5)
        elif reg_weight < 0.65:
            # West (IDs 11-15)
            region_id = random.randint(11, 15)
        elif reg_weight < 0.82:
            # South (IDs 6-10)
            region_id = random.randint(6, 10)
        elif reg_weight < 0.92:
            # East (IDs 16-20)
            region_id = random.randint(16, 20)
        else:
            # Central (IDs 21-25)
            region_id = random.randint(21, 25)
            
        customer = random.choice(CUSTOMERS_DATA)
        customer_id = customer[0]
        
        # PATTERN 3: Category Preferences by Geography
        # North & West prefer Electronics / Home; East & Central prefer Apparel / Beauty
        cat_roll = random.random()
        if region_id in range(1, 6) or region_id in range(11, 16):
            if cat_roll < 0.40:
                prod = random.choice(PRODUCTS_DATA[0:6]) # Electronics
            elif cat_roll < 0.70:
                prod = random.choice(PRODUCTS_DATA[12:18]) # Home
            else:
                prod = random.choice(PRODUCTS_DATA)
        elif region_id in range(16, 26):
            if cat_roll < 0.45:
                prod = random.choice(PRODUCTS_DATA[6:12]) # Apparel
            elif cat_roll < 0.75:
                prod = random.choice(PRODUCTS_DATA[24:30]) # Beauty
            else:
                prod = random.choice(PRODUCTS_DATA)
        else:
            prod = random.choice(PRODUCTS_DATA)
            
        product_id = prod[0]
        base_cost = prod[4]
        list_price = prod[5]
        
        # Quantity distribution
        if customer[3] == "Corporate":
            quantity = random.randint(5, 20)
        else:
            quantity = random.randint(1, 5)
            
        if is_q4_festive:
            quantity = int(quantity * 1.3)
            if quantity < 1: quantity = 1

        unit_price = list_price
        gross_rev = round(quantity * unit_price, 2)
        
        # PATTERN 4: Promotional Discount Elasticity vs Margin
        disc_roll = random.random()
        if disc_roll < 0.45:
            discount_pct = 0.05
        elif disc_roll < 0.80:
            discount_pct = 0.15
        else:
            discount_pct = 0.25 # Aggressive discount
            
        disc_amt = round(gross_rev * discount_pct, 2)
        net_rev = round(gross_rev - disc_amt, 2)
        unit_cogs = base_cost
        tot_cogs = round(quantity * unit_cogs, 2)
        
        # PATTERN 2: Shipping / Freight Costs - Central and East face high logistical surcharges
        if region_id in range(21, 26): # Central
            shipping_cost = round(random.uniform(450.0, 950.0), 2)
        elif region_id in range(16, 21): # East
            shipping_cost = round(random.uniform(400.0, 850.0), 2)
        else:
            shipping_cost = round(random.uniform(150.0, 400.0), 2)
            
        gross_profit = round(net_rev - (tot_cogs + shipping_cost), 2)
        margin_pct = round((gross_profit / net_rev) * 100.0, 2) if net_rev > 0 else 0.0
        
        margin_status = "Margin Deficient" if margin_pct < 15.0 else "Healthy"
        order_status = "Completed" if random.random() < 0.94 else "Returned"
        
        sales.append([
            i, order_code, order_date_str, customer_id, product_id, region_id,
            quantity, unit_price, gross_rev, discount_pct, disc_amt, net_rev,
            unit_cogs, tot_cogs, shipping_cost, gross_profit, margin_pct,
            margin_status, order_status
        ])
        
    return sales

RAW_SALES_DATA = generate_sales()

# -------------------------------------------------------------------------
# 3. Inject Data Quality Issues for Cleaning in Step 11
# -------------------------------------------------------------------------

def inject_quality_issues(sales):
    """
    Intentionally adds realistic anomalies:
    - 6 null shipping costs (2.4%)
    - 4 null discount percentages (1.6%)
    - 3 duplicate rows (simulating duplicate webhook entries)
    - 3 extreme high-ticket institutional orders (outliers)
    """
    cleaned = [row[:] for row in sales]
    
    # 1. Null shipping costs
    for idx in [14, 45, 88, 122, 178, 230]:
        cleaned[idx][14] = None # shipping_cost = None
        
    # 2. Null discount percentages
    for idx in [29, 74, 150, 212]:
        cleaned[idx][9] = None # discount_pct = None
        
    # 3. Extreme Outliers (B2B Bulk Purchase)
    for idx in [55, 134, 205]:
        cleaned[idx][6] = 95 # order_quantity = 95
        cleaned[idx][8] = round(cleaned[idx][6] * cleaned[idx][7], 2) # gross_revenue
        cleaned[idx][10] = round(cleaned[idx][8] * 0.10, 2) # discount_amt
        cleaned[idx][11] = round(cleaned[idx][8] - cleaned[idx][10], 2) # net_revenue
        cleaned[idx][13] = round(cleaned[idx][6] * cleaned[idx][12], 2) # total_cogs
        cleaned[idx][15] = round(cleaned[idx][11] - (cleaned[idx][13] + (cleaned[idx][14] or 350.0)), 2)
        cleaned[idx][16] = round((cleaned[idx][15] / cleaned[idx][11]) * 100.0, 2)
        
    # 4. Duplicate Records
    duplicates = [cleaned[10][:], cleaned[65][:], cleaned[180][:]]
    for dup in duplicates:
        # Give duplicate an incremented order_id to append in staging
        dup[0] = len(cleaned) + 1
        cleaned.append(dup)
        
    return cleaned

STAGING_SALES_DATA = inject_quality_issues(RAW_SALES_DATA)

# -------------------------------------------------------------------------
# 4. Database Seeding & View Creation
# -------------------------------------------------------------------------

def seed_sqlite_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    
    # DDL Execution
    cur.execute("""
    CREATE TABLE dim_regions (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL CHECK(region_name IN ('North', 'South', 'East', 'West', 'Central')),
        state_name TEXT NOT NULL,
        city_name TEXT NOT NULL,
        city_tier TEXT NOT NULL CHECK(city_tier IN ('Tier-1', 'Tier-2', 'Tier-3')),
        regional_manager TEXT NOT NULL,
        target_quarterly_revenue REAL NOT NULL DEFAULT 0.0 CHECK(target_quarterly_revenue >= 0.0)
    );
    """)
    cur.execute("CREATE INDEX idx_regions_name ON dim_regions(region_name);")
    
    cur.execute("""
    CREATE TABLE dim_products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_sku TEXT UNIQUE NOT NULL,
        product_name TEXT NOT NULL,
        product_category TEXT NOT NULL CHECK(product_category IN ('Electronics', 'Apparel', 'Home & Kitchen', 'Office Supplies', 'Health & Beauty')),
        unit_cost_cogs REAL NOT NULL CHECK(unit_cost_cogs > 0.0),
        base_list_price REAL NOT NULL CHECK(base_list_price > unit_cost_cogs),
        target_gross_margin_pct REAL NOT NULL DEFAULT 25.0
    );
    """)
    cur.execute("CREATE INDEX idx_products_cat ON dim_products(product_category);")
    
    cur.execute("""
    CREATE TABLE dim_customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_code TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_segment TEXT NOT NULL CHECK(customer_segment IN ('Consumer', 'Corporate', 'Small Business')),
        customer_type TEXT NOT NULL CHECK(customer_type IN ('New', 'Returning')),
        acquisition_date TEXT NOT NULL,
        primary_region_id INTEGER NOT NULL,
        FOREIGN KEY (primary_region_id) REFERENCES dim_regions(region_id) ON DELETE RESTRICT ON UPDATE CASCADE
    );
    """)
    
    cur.execute("""
    CREATE TABLE fact_sales (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT NOT NULL,
        order_date TEXT NOT NULL,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        region_id INTEGER NOT NULL,
        order_quantity INTEGER NOT NULL CHECK(order_quantity > 0),
        unit_price REAL NOT NULL CHECK(unit_price > 0.0),
        gross_revenue REAL NOT NULL,
        discount_pct REAL,
        discount_amount REAL NOT NULL DEFAULT 0.0,
        net_revenue REAL NOT NULL CHECK(net_revenue >= 0.0),
        unit_cogs REAL NOT NULL CHECK(unit_cogs > 0.0),
        total_cogs REAL NOT NULL,
        shipping_cost REAL,
        gross_profit REAL NOT NULL,
        gross_margin_pct REAL NOT NULL,
        margin_status TEXT NOT NULL CHECK(margin_status IN ('Healthy', 'Margin Deficient')),
        order_status TEXT NOT NULL CHECK(order_status IN ('Completed', 'Shipped', 'Returned')),
        FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
        FOREIGN KEY (product_id) REFERENCES dim_products(product_id) ON DELETE RESTRICT ON UPDATE CASCADE,
        FOREIGN KEY (region_id) REFERENCES dim_regions(region_id) ON DELETE RESTRICT ON UPDATE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_sales_composite ON fact_sales(region_id, order_date);")
    cur.execute("CREATE INDEX idx_sales_product ON fact_sales(product_id, order_date);")
    
    # Insert Masters
    cur.executemany("INSERT INTO dim_regions VALUES (?, ?, ?, ?, ?, ?, ?)", REGIONS_DATA)
    cur.executemany("INSERT INTO dim_products VALUES (?, ?, ?, ?, ?, ?, ?)", PRODUCTS_DATA)
    cur.executemany("INSERT INTO dim_customers VALUES (?, ?, ?, ?, ?, ?, ?)", CUSTOMERS_DATA)
    
    # Insert Fact Rows (including staging records for clean audit in Step 11)
    cur.executemany("""
    INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, STAGING_SALES_DATA)
    
    # Create View
    cur.execute("""
    CREATE VIEW view_sales_analysis AS
    SELECT 
        f.order_id,
        f.order_code,
        f.order_date,
        strftime('%Y', f.order_date) AS order_year,
        'Q' || ((CAST(strftime('%m', f.order_date) AS INT) + 2) / 3) AS order_quarter,
        strftime('%m', f.order_date) AS order_month,
        strftime('%Y-%m', f.order_date) AS order_year_month,
        c.customer_id,
        c.customer_code,
        c.customer_name,
        c.customer_segment,
        c.customer_type,
        c.acquisition_date,
        p.product_id,
        p.product_sku,
        p.product_name,
        p.product_category,
        r.region_id,
        r.region_name,
        r.state_name,
        r.city_name,
        r.city_tier,
        r.regional_manager,
        f.order_quantity,
        f.unit_price,
        f.gross_revenue,
        f.discount_pct,
        CASE 
            WHEN f.discount_pct <= 0.10 THEN '0-10%'
            WHEN f.discount_pct <= 0.20 THEN '11-20%'
            ELSE '>20%'
        END AS discount_bracket,
        f.discount_amount,
        f.net_revenue,
        f.total_cogs,
        f.shipping_cost,
        f.gross_profit,
        f.gross_margin_pct,
        f.margin_status,
        f.order_status
    FROM fact_sales f
    JOIN dim_regions r ON f.region_id = r.region_id
    JOIN dim_products p ON f.product_id = p.product_id
    JOIN dim_customers c ON f.customer_id = c.customer_id;
    """)
    
    conn.commit()
    conn.close()
    print(f"SQLite Database seeded successfully at: {DB_PATH}")

# -------------------------------------------------------------------------
# 5. Export to CSV & Excel Workbook
# -------------------------------------------------------------------------

def export_csv_files():
    # 1. dim_regions.csv
    with open(os.path.join(DATA_DIR, "dim_regions.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["region_id", "region_name", "state_name", "city_name", "city_tier", "regional_manager", "target_quarterly_revenue"])
        writer.writerows(REGIONS_DATA)
        
    # 2. dim_products.csv
    with open(os.path.join(DATA_DIR, "dim_products.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "product_sku", "product_name", "product_category", "unit_cost_cogs", "base_list_price", "target_gross_margin_pct"])
        writer.writerows(PRODUCTS_DATA)
        
    # 3. dim_customers.csv
    with open(os.path.join(DATA_DIR, "dim_customers.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "customer_code", "customer_name", "customer_segment", "customer_type", "acquisition_date", "primary_region_id"])
        writer.writerows(CUSTOMERS_DATA)
        
    # 4. fact_sales.csv
    with open(os.path.join(DATA_DIR, "fact_sales.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "order_id", "order_code", "order_date", "customer_id", "product_id", "region_id",
            "order_quantity", "unit_price", "gross_revenue", "discount_pct", "discount_amount",
            "net_revenue", "unit_cogs", "total_cogs", "shipping_cost", "gross_profit",
            "gross_margin_pct", "margin_status", "order_status"
        ])
        writer.writerows(STAGING_SALES_DATA)
        
    print(f"CSVs exported to: {DATA_DIR}")

if __name__ == "__main__":
    print("Executing synthetic dataset generation (seed=42)...")
    seed_sqlite_database()
    export_csv_files()
    print("Generation complete!")
