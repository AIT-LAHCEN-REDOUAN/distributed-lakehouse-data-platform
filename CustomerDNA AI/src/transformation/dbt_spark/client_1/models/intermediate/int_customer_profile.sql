with marketing as (
    select * from {{ ref('stg_marketing_campaign') }}
),
churn as (
    select * from {{ ref('stg_ecommerce_customer_churn') }}
)

select
    m.customer_id,
    m.year_birth,
    m.education,
    coalesce(c.marital_status, m.marital_status) as marital_status,
    c.gender,
    m.income,
    m.kidhome,
    m.teenhome,
    m.customer_since_date,
    m.recency_days,
    c.tenure_months,
    c.city_tier,
    c.preferred_login_device,
    c.preferred_payment_mode,
    c.preferred_order_category,
    c.hours_spent_on_app,
    c.registered_device_count,
    c.satisfaction_score,
    c.address_count,
    c.order_count as ecommerce_order_count,
    c.days_since_last_order,
    c.order_amount_hike_pct,
    c.cashback_amount,
    coalesce(c.complaint_flag, m.complaint_flag) as complaint_flag,
    c.is_churned,
    m.last_campaign_response_flag
from marketing m
left join churn c
    on m.customer_id = c.customer_id
