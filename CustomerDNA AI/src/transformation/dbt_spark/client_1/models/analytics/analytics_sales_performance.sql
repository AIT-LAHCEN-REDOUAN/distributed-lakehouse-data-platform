select
    country,
    date_trunc('month', invoice_timestamp) as sales_month,
    count(distinct invoice_no) as invoice_count,
    count(distinct customer_id) as active_customers,
    sum(quantity) as net_quantity,
    round(sum(line_amount), 2) as net_revenue,
    round(sum(case when not is_return then line_amount else 0 end), 2) as gross_sales_value,
    round(abs(sum(case when is_return then line_amount else 0 end)), 2) as returned_sales_value,
    round(avg(case when not is_return then unit_price end), 2) as average_unit_price
from {{ ref('stg_online_retail_2') }}
where invoice_timestamp is not null
group by 1, 2
