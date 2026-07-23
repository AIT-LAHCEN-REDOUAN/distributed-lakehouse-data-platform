with profile as (
    select * from intermediate.int_customer_profile
),
marketing as (
    select * from staging.stg_marketing_campaign
),
sales as (
    select * from intermediate.int_online_retail_customer_sales
)

select
    p.customer_id,
    p.year_birth,
    p.education,
    p.marital_status,
    p.gender,
    p.income,
    p.kidhome,
    p.teenhome,
    p.customer_since_date,
    p.recency_days,
    p.tenure_months,
    p.city_tier,
    p.preferred_login_device,
    p.preferred_payment_mode,
    p.preferred_order_category,
    p.hours_spent_on_app,
    p.registered_device_count,
    p.satisfaction_score,
    p.address_count,
    p.ecommerce_order_count,
    p.days_since_last_order,
    p.order_amount_hike_pct,
    p.cashback_amount,
    p.complaint_flag,
    p.is_churned,
    p.last_campaign_response_flag,
    coalesce(s.invoice_count, 0) as retail_invoice_count,
    coalesce(s.distinct_product_count, 0) as retail_distinct_product_count,
    coalesce(s.total_quantity, 0) as retail_total_quantity,
    coalesce(s.gross_revenue, 0.0) as retail_gross_revenue,
    coalesce(s.average_invoice_line_amount, 0.0) as retail_average_invoice_line_amount,
    s.first_order_timestamp,
    s.last_order_timestamp,
    coalesce(s.countries_served_count, 0) as countries_served_count,
    (
        coalesce(m.amount_wines, 0.0) +
        coalesce(m.amount_fruits, 0.0) +
        coalesce(m.amount_meat, 0.0) +
        coalesce(m.amount_fish, 0.0) +
        coalesce(m.amount_sweets, 0.0) +
        coalesce(m.amount_gold, 0.0)
    ) as campaign_total_spend,
    (
        coalesce(m.web_purchases, 0) +
        coalesce(m.catalog_purchases, 0) +
        coalesce(m.store_purchases, 0)
    ) as total_campaign_purchase_count
from profile p
left join marketing m
    on p.customer_id = m.customer_id
left join sales s
    on p.customer_id = s.customer_id