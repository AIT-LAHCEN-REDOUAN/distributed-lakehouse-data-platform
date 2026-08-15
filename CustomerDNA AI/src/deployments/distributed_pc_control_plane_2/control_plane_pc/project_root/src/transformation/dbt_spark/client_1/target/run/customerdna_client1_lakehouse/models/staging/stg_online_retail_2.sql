
  
    
        create or replace table staging.stg_online_retail_2
      
      
    using iceberg
      
      
      
      
      
      comment 'Typed staging model for retail transactions from Online Retail II.'
      

      as
      select
    trim(invoice) as invoice_no,
    trim(stockcode) as stock_code,
    trim(description) as product_description,
    cast(
    coalesce(
        try_cast(nullif(trim(quantity), '') as int),
        try_cast(nullif(trim(quantity), '') as double)
    ) as int
) as quantity,
    
try_to_timestamp(nullif(trim(invoicedate), ''))
 as invoice_timestamp,
    try_cast(nullif(trim(price), '') as double) as unit_price,
    case
        when cast(
    coalesce(
        try_cast(nullif(trim(customer_id), '') as bigint),
        try_cast(nullif(trim(customer_id), '') as double)
    ) as bigint
) > 0 then cast(
    coalesce(
        try_cast(nullif(trim(customer_id), '') as bigint),
        try_cast(nullif(trim(customer_id), '') as double)
    ) as bigint
)
        else null
    end as customer_id,
    trim(country) as country,
    round(
        coalesce(cast(
    coalesce(
        try_cast(nullif(trim(quantity), '') as int),
        try_cast(nullif(trim(quantity), '') as double)
    ) as int
), 0) * coalesce(try_cast(nullif(trim(price), '') as double), 0.0),
        2
    ) as line_amount,
    case
        when cast(
    coalesce(
        try_cast(nullif(trim(quantity), '') as int),
        try_cast(nullif(trim(quantity), '') as double)
    ) as int
) < 0 or upper(trim(invoice)) like 'C%' then true
        else false
    end as is_return
from raw_data.online_retail_2
  