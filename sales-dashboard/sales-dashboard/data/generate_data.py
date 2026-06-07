import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

regions = {
    "North":   1.10,
    "South":   0.88,   # underperforming — ~12% below average
    "East":    1.05,
    "West":    0.95,
    "Central": 1.02,
}

products = {
    "Enterprise Suite":  (8000, 20000),
    "Pro License":       (1500, 5000),
    "Basic License":     (300,  1200),
    "Support Contract":  (500,  3000),
    "Training Package":  (200,  800),
    "Cloud Add-on":      (100,  600),
}

segments = ["Enterprise", "SMB", "Startup", "Government"]
channels  = ["Direct", "Partner", "Online", "Referral"]

rows = []
start = datetime(2023, 1, 1)

for i in range(50000):
    region  = random.choice(list(regions.keys()))
    product = random.choice(list(products.keys()))
    segment = random.choice(segments)
    channel = random.choice(channels)

    sale_date  = start + timedelta(days=random.randint(0, 729))
    base_low, base_high = products[product]
    base_rev   = random.uniform(base_low, base_high)

    month_factor = 1 + 0.05 * np.sin(2 * np.pi * sale_date.month / 12)
    unit_price   = round(base_rev * regions[region] * month_factor, 2)
    units        = random.randint(1, 10)
    discount     = round(random.uniform(0, 0.25), 2)
    net_revenue  = round(unit_price * units * (1 - discount), 2)

    rows.append({
        "sale_id":          f"S{i+1:05d}",
        "sale_date":        sale_date.strftime("%Y-%m-%d"),
        "region":           region,
        "product":          product,
        "customer_segment": segment,
        "channel":          channel,
        "units_sold":       units,
        "unit_price":       unit_price,
        "discount_pct":     discount,
        "net_revenue":      net_revenue,
        "sales_rep_id":     f"REP{random.randint(1, 50):03d}",
        "customer_id":      f"CUST{random.randint(1, 5000):05d}",
    })

df = pd.DataFrame(rows)
df.to_csv("sales_data.csv", index=False)
print(f"Generated {len(df):,} rows")
print("\nNet Revenue by Region:")
print(df.groupby("region")["net_revenue"].sum().sort_values().apply(lambda x: f"${x:,.0f}"))
