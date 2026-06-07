"""
Sales Performance & Revenue Analysis
=====================================
Python EDA + Analysis pipeline
Author: Aaryendra Kashyap
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 120

df = pd.read_csv("../data/sales_data.csv", parse_dates=["sale_date"])
print(f"Loaded {len(df):,} records | {df['customer_id'].nunique():,} unique customers")
print(df.dtypes)
print(df.describe())

# ── Feature Engineering ──────────────────────────────────────────────────────
df["year"]       = df["sale_date"].dt.year
df["month"]      = df["sale_date"].dt.month
df["month_name"] = df["sale_date"].dt.strftime("%b")
df["year_month"] = df["sale_date"].dt.to_period("M")
df["quarter"]    = df["sale_date"].dt.quarter

# ── 1. Monthly Revenue Trend ─────────────────────────────────────────────────
monthly = (df.groupby("year_month")["net_revenue"]
             .sum()
             .reset_index()
             .sort_values("year_month"))
monthly["mom_growth"] = monthly["net_revenue"].pct_change() * 100

fig, ax1 = plt.subplots(figsize=(12, 4))
ax1.bar(monthly["year_month"].astype(str), monthly["net_revenue"] / 1e6,
        color="steelblue", alpha=0.7, label="Revenue ($M)")
ax2 = ax1.twinx()
ax2.plot(monthly["year_month"].astype(str), monthly["mom_growth"],
         color="tomato", marker="o", linewidth=1.5, label="MoM Growth %")
ax2.axhline(0, color="grey", linestyle="--", linewidth=0.8)
ax1.set_xlabel("Month")
ax1.set_ylabel("Net Revenue ($M)")
ax2.set_ylabel("MoM Growth (%)")
ax1.set_title("Monthly Revenue Trend with Growth Rate")
plt.xticks(rotation=45)
fig.tight_layout()
plt.savefig("../images/01_monthly_revenue_trend.png")
plt.close()
print("Saved: 01_monthly_revenue_trend.png")

# ── 2. Regional Performance ──────────────────────────────────────────────────
region_rev = df.groupby("region")["net_revenue"].sum().sort_values()
avg_rev    = region_rev.mean()
colors     = ["tomato" if v < avg_rev else "steelblue" for v in region_rev]

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(region_rev.index, region_rev.values / 1e6, color=colors)
ax.axvline(avg_rev / 1e6, color="black", linestyle="--", linewidth=1,
           label=f"Avg: ${avg_rev/1e6:.1f}M")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))
ax.set_title("Net Revenue by Region (Red = Below Average)")
ax.set_xlabel("Net Revenue ($M)")
ax.legend()

# Annotate pct vs avg
for bar, val in zip(bars, region_rev.values):
    pct = (val - avg_rev) / avg_rev * 100
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{pct:+.1f}%", va="center", fontsize=9)

plt.tight_layout()
plt.savefig("../images/02_regional_performance.png")
plt.close()
print("Saved: 02_regional_performance.png")

# ── 3. Customer Segmentation ─────────────────────────────────────────────────
seg = df.groupby("customer_segment").agg(
    total_revenue=("net_revenue", "sum"),
    unique_customers=("customer_id", "nunique"),
    avg_order_value=("net_revenue", "mean"),
).reset_index()
seg["revenue_share"] = seg["total_revenue"] / seg["total_revenue"].sum() * 100
seg["revenue_per_customer"] = seg["total_revenue"] / seg["unique_customers"]

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].pie(seg["revenue_share"], labels=seg["customer_segment"],
            autopct="%1.1f%%", startangle=140, colors=sns.color_palette("muted"))
axes[0].set_title("Revenue Share by Segment")

axes[1].bar(seg["customer_segment"], seg["revenue_per_customer"],
            color=sns.color_palette("muted"))
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
axes[1].set_title("Revenue per Customer by Segment")
axes[1].set_ylabel("Revenue per Customer ($)")
plt.tight_layout()
plt.savefig("../images/03_customer_segmentation.png")
plt.close()
print("Saved: 03_customer_segmentation.png")

# ── 4. Product Revenue Heatmap ────────────────────────────────────────────────
pivot = df.pivot_table(index="product", columns="region",
                       values="net_revenue", aggfunc="sum") / 1e6

fig, ax = plt.subplots(figsize=(10, 5))
sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd", ax=ax,
            linewidths=0.5, cbar_kws={"label": "Revenue ($M)"})
ax.set_title("Product Revenue by Region ($M)")
plt.tight_layout()
plt.savefig("../images/04_product_region_heatmap.png")
plt.close()
print("Saved: 04_product_region_heatmap.png")

# ── 5. Channel Effectiveness ──────────────────────────────────────────────────
channel = df.groupby(["channel", "customer_segment"])["net_revenue"].sum().unstack()
channel.plot(kind="bar", figsize=(10, 4), colormap="tab10", width=0.75)
plt.title("Revenue by Channel and Customer Segment")
plt.ylabel("Net Revenue ($)")
plt.xlabel("Channel")
plt.xticks(rotation=0)
plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))
plt.legend(title="Segment", bbox_to_anchor=(1.01, 1))
plt.tight_layout()
plt.savefig("../images/05_channel_effectiveness.png")
plt.close()
print("Saved: 05_channel_effectiveness.png")

# ── 6. Key Findings Summary ──────────────────────────────────────────────────
print("\n" + "="*60)
print("KEY FINDINGS")
print("="*60)

total_rev = df["net_revenue"].sum()
print(f"\nTotal Revenue (2023–2024):  ${total_rev:,.0f}")
print(f"Total Transactions:          {len(df):,}")
print(f"Unique Customers:            {df['customer_id'].nunique():,}")
print(f"Avg Order Value:             ${df['net_revenue'].mean():,.2f}")

print("\n--- Regional Performance vs Average ---")
for region, rev in region_rev.items():
    pct = (rev - avg_rev) / avg_rev * 100
    flag = " ⚠ UNDERPERFORMING" if pct < -5 else ""
    print(f"  {region:<10} ${rev:>15,.0f}   ({pct:+.1f}%){flag}")

print("\n--- Top Segment by Revenue per Customer ---")
top_seg = seg.sort_values("revenue_per_customer", ascending=False).iloc[0]
print(f"  {top_seg['customer_segment']} — ${top_seg['revenue_per_customer']:,.0f} per customer")

print("\n--- Month with Highest Decline ---")
worst = monthly.dropna().sort_values("mom_growth").iloc[0]
print(f"  {worst['year_month']} — {worst['mom_growth']:.1f}% MoM growth")
print("="*60)
