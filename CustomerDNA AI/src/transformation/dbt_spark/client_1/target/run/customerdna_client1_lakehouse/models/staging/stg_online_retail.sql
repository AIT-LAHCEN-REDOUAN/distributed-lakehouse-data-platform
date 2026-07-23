
  
    
        create or replace table staging.stg_online_retail
      
      
    using iceberg
      
      
      
      
      
      comment 'Typed staging view for online retail transactions.'
      

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
    cast(
    coalesce(
        try_cast(nullif(trim(customer_id), '') as bigint),
        try_cast(nullif(trim(customer_id), '') as double)
    ) as bigint
) as customer_id,
    trim(country) as country
from raw_data.online_retail
  