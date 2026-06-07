-- ============================================================
-- Sales Performance & Revenue Analysis
-- Author: Aaryendra Kashyap
-- Description: Advanced SQL analysis on 50,000+ sales records
--              covering revenue trends, segmentation, and KPIs
-- ============================================================

-- ------------------------------------------------------------
-- 0. TABLE SETUP (PostgreSQL)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales (
    sale_id          VARCHAR(10) PRIMARY KEY,
    sale_date        DATE,
    region           VARCHAR(20),
    product          VARCHAR(50),
    customer_segment VARCHAR(20),
    channel          VARCHAR(20),
    units_sold       INT,
    unit_price       NUMERIC(12,2),
    discount_pct     NUMERIC(5,2),
    net_revenue      NUMERIC(12,2),
    sales_rep_id     VARCHAR(10),
    customer_id      VARCHAR(10)
);

-- Load from CSV:
-- \COPY sales FROM 'data/sales_data.csv' CSV HEADER;


-- ============================================================
-- 1. MONTHLY REVENUE TREND  (Window Function: LAG)
-- ============================================================
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', sale_date)  AS month,
        SUM(net_revenue)                AS total_revenue,
        COUNT(DISTINCT customer_id)     AS unique_customers,
        COUNT(sale_id)                  AS total_transactions
    FROM sales
    GROUP BY 1
),
revenue_with_growth AS (
    SELECT
        month,
        total_revenue,
        unique_customers,
        total_transactions,
        LAG(total_revenue) OVER (ORDER BY month)  AS prev_month_revenue,
        ROUND(
            (total_revenue - LAG(total_revenue) OVER (ORDER BY month))
            / NULLIF(LAG(total_revenue) OVER (ORDER BY month), 0) * 100, 2
        ) AS mom_growth_pct
    FROM monthly_revenue
)
SELECT *
FROM revenue_with_growth
ORDER BY month;


-- ============================================================
-- 2. REGIONAL PERFORMANCE vs AVERAGE  (CTE + Window Function)
-- ============================================================
WITH region_totals AS (
    SELECT
        region,
        SUM(net_revenue)                        AS total_revenue,
        COUNT(DISTINCT customer_id)             AS unique_customers,
        ROUND(AVG(discount_pct) * 100, 2)       AS avg_discount_pct,
        ROUND(SUM(net_revenue) / COUNT(sale_id), 2) AS avg_order_value
    FROM sales
    GROUP BY region
),
global_avg AS (
    SELECT AVG(total_revenue) AS avg_regional_revenue
    FROM region_totals
)
SELECT
    r.region,
    r.total_revenue,
    r.unique_customers,
    r.avg_discount_pct,
    r.avg_order_value,
    ROUND((r.total_revenue - g.avg_regional_revenue)
          / g.avg_regional_revenue * 100, 2)  AS pct_vs_avg,
    RANK() OVER (ORDER BY r.total_revenue DESC) AS revenue_rank
FROM region_totals r
CROSS JOIN global_avg g
ORDER BY revenue_rank;


-- ============================================================
-- 3. CUSTOMER SEGMENTATION ANALYSIS  (CTE + JOINs)
-- ============================================================
WITH segment_metrics AS (
    SELECT
        customer_segment,
        COUNT(DISTINCT customer_id)                 AS total_customers,
        SUM(net_revenue)                            AS total_revenue,
        ROUND(AVG(net_revenue), 2)                  AS avg_order_value,
        ROUND(SUM(net_revenue) / COUNT(DISTINCT customer_id), 2) AS revenue_per_customer
    FROM sales
    GROUP BY customer_segment
),
segment_ranked AS (
    SELECT
        *,
        ROUND(total_revenue / SUM(total_revenue) OVER () * 100, 2) AS revenue_share_pct,
        RANK() OVER (ORDER BY total_revenue DESC)                   AS revenue_rank
    FROM segment_metrics
)
SELECT *
FROM segment_ranked
ORDER BY revenue_rank;


-- ============================================================
-- 4. PRODUCT REVENUE BREAKDOWN + RUNNING TOTAL  (Window Function)
-- ============================================================
WITH product_revenue AS (
    SELECT
        product,
        region,
        SUM(net_revenue)    AS revenue,
        SUM(units_sold)     AS units,
        COUNT(sale_id)      AS transactions
    FROM sales
    GROUP BY product, region
)
SELECT
    product,
    region,
    revenue,
    units,
    transactions,
    ROUND(revenue / SUM(revenue) OVER (PARTITION BY product) * 100, 2) AS region_share_pct,
    SUM(revenue) OVER (PARTITION BY product ORDER BY revenue DESC
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM product_revenue
ORDER BY product, revenue DESC;


-- ============================================================
-- 5. TOP 10% CUSTOMERS BY REVENUE  (NTILE + CTE)
-- ============================================================
WITH customer_revenue AS (
    SELECT
        customer_id,
        customer_segment,
        region,
        SUM(net_revenue)            AS lifetime_value,
        COUNT(sale_id)              AS total_orders,
        MIN(sale_date)              AS first_purchase,
        MAX(sale_date)              AS last_purchase,
        NTILE(10) OVER (ORDER BY SUM(net_revenue) DESC) AS revenue_decile
    FROM sales
    GROUP BY customer_id, customer_segment, region
)
SELECT *
FROM customer_revenue
WHERE revenue_decile = 1
ORDER BY lifetime_value DESC;


-- ============================================================
-- 6. SALES REP PERFORMANCE LEADERBOARD  (DENSE_RANK + CTE)
-- ============================================================
WITH rep_stats AS (
    SELECT
        sales_rep_id,
        region,
        COUNT(sale_id)                              AS deals_closed,
        SUM(net_revenue)                            AS total_revenue,
        ROUND(AVG(net_revenue), 2)                  AS avg_deal_size,
        ROUND(AVG(discount_pct) * 100, 2)           AS avg_discount_given,
        COUNT(DISTINCT customer_id)                 AS unique_clients
    FROM sales
    GROUP BY sales_rep_id, region
)
SELECT
    *,
    DENSE_RANK() OVER (ORDER BY total_revenue DESC)          AS overall_rank,
    DENSE_RANK() OVER (PARTITION BY region ORDER BY total_revenue DESC) AS rank_in_region
FROM rep_stats
ORDER BY overall_rank
LIMIT 20;


-- ============================================================
-- 7. UNDERPERFORMING REGIONS — MONTH-OVER-MONTH DECLINE
-- ============================================================
WITH monthly_regional AS (
    SELECT
        region,
        DATE_TRUNC('month', sale_date) AS month,
        SUM(net_revenue)               AS revenue
    FROM sales
    GROUP BY region, DATE_TRUNC('month', sale_date)
),
with_growth AS (
    SELECT
        region,
        month,
        revenue,
        LAG(revenue) OVER (PARTITION BY region ORDER BY month) AS prev_revenue,
        ROUND(
            (revenue - LAG(revenue) OVER (PARTITION BY region ORDER BY month))
            / NULLIF(LAG(revenue) OVER (PARTITION BY region ORDER BY month), 0) * 100, 2
        ) AS mom_growth_pct
    FROM monthly_regional
)
SELECT *
FROM with_growth
WHERE mom_growth_pct < -5          -- flag months with >5% decline
ORDER BY mom_growth_pct ASC;


-- ============================================================
-- 8. CHANNEL EFFECTIVENESS  (JOIN + aggregation)
-- ============================================================
SELECT
    channel,
    customer_segment,
    COUNT(sale_id)                              AS transactions,
    SUM(net_revenue)                            AS total_revenue,
    ROUND(AVG(net_revenue), 2)                  AS avg_order_value,
    ROUND(AVG(discount_pct) * 100, 2)           AS avg_discount_pct,
    ROUND(SUM(net_revenue) /
          SUM(SUM(net_revenue)) OVER (PARTITION BY channel) * 100, 2) AS segment_share_pct
FROM sales
GROUP BY channel, customer_segment
ORDER BY channel, total_revenue DESC;
