with source as (
    select *
    from staging.stg_online_retail_2
    where customer_id is not null
),
customer_sales as (
    select
        customer_id,
        min(country) as primary_country,
        count(distinct invoice_no) as invoice_count,
        count(distinct case when not is_return then invoice_no end) as completed_invoice_count,
        count(distinct stock_code) as distinct_product_count,
        sum(quantity) as net_quantity,
        sum(case when quantity > 0 then quantity else 0 end) as sold_quantity,
        sum(case when quantity < 0 then abs(quantity) else 0 end) as returned_quantity,
        round(sum(line_amount), 2) as net_revenue,
        round(sum(case when not is_return then line_amount else 0 end), 2) as gross_sales_value,
        round(abs(sum(case when is_return then line_amount else 0 end)), 2) as returned_sales_value,
        round(avg(case when not is_return then line_amount end), 2) as average_invoice_line_amount,
        min(invoice_timestamp) as first_order_timestamp,
        max(invoice_timestamp) as last_order_timestamp,
        count(distinct country) as countries_served_count,
        sum(case when is_return then 1 else 0 end) as return_line_count
    from source
    group by customer_id
),
global_snapshot as (
    select max(invoice_timestamp) as snapshot_timestamp
    from source
)

select
    s.customer_id,
    s.primary_country,
    s.invoice_count,
    s.completed_invoice_count,
    s.distinct_product_count,
    s.net_quantity,
    s.sold_quantity,
    s.returned_quantity,
    s.net_revenue,
    s.gross_sales_value,
    s.returned_sales_value,
    s.average_invoice_line_amount,
    s.first_order_timestamp,
    s.last_order_timestamp,
    s.countries_served_count,
    s.return_line_count,
    datediff(to_date(g.snapshot_timestamp), to_date(s.last_order_timestamp)) as recency_days,
    datediff(to_date(s.last_order_timestamp), to_date(s.first_order_timestamp)) as customer_active_span_days,
    round(
        case
            when s.completed_invoice_count > 0 then s.net_revenue / s.completed_invoice_count
            else null
        end,
        2
    ) as average_order_value
from customer_sales s
cross join global_snapshot g