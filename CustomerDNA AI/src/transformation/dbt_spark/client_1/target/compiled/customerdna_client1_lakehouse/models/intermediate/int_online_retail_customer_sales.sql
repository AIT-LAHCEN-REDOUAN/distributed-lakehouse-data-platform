select
    customer_id,
    count(distinct invoice_no) as invoice_count,
    count(distinct stock_code) as distinct_product_count,
    sum(quantity) as total_quantity,
    round(sum(quantity * unit_price), 2) as gross_revenue,
    round(avg(quantity * unit_price), 2) as average_invoice_line_amount,
    min(invoice_timestamp) as first_order_timestamp,
    max(invoice_timestamp) as last_order_timestamp,
    count(distinct country) as countries_served_count
from staging.stg_online_retail
where customer_id is not null
group by customer_id