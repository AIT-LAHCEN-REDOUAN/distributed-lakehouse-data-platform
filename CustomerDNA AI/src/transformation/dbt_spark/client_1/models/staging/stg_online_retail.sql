select
    trim(invoice) as invoice_no,
    trim(stockcode) as stock_code,
    trim(description) as product_description,
    {{ as_int('quantity') }} as quantity,
    {{ as_timestamp('invoicedate') }} as invoice_timestamp,
    {{ as_double('price') }} as unit_price,
    {{ as_bigint('customer_id') }} as customer_id,
    trim(country) as country
from {{ source('raw_data', 'online_retail') }}
