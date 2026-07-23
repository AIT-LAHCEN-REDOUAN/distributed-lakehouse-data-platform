select
    country,
    date_trunc('month', invoice_timestamp) as sales_month,
    count(distinct invoice_no) as invoice_count,
    count(distinct customer_id) as active_customers,
    sum(quantity) as total_quantity,
    round(sum(quantity * unit_price), 2) as gross_revenue,
    round(avg(unit_price), 2) as average_unit_price
from staging.stg_online_retail
where invoice_timestamp is not null
group by 1, 2