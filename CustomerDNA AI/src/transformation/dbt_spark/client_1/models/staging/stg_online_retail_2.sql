select
    trim(invoice) as invoice_no,
    trim(stockcode) as stock_code,
    trim(description) as product_description,
    {{ as_int('quantity') }} as quantity,
    {{ as_timestamp('invoicedate') }} as invoice_timestamp,
    {{ as_double('price') }} as unit_price,
    case
        when {{ as_bigint('customer_id') }} > 0 then {{ as_bigint('customer_id') }}
        else null
    end as customer_id,
    trim(country) as country,
    round(
        coalesce({{ as_int('quantity') }}, 0) * coalesce({{ as_double('price') }}, 0.0),
        2
    ) as line_amount,
    case
        when {{ as_int('quantity') }} < 0 or upper(trim(invoice)) like 'C%' then true
        else false
    end as is_return
from {{ source('raw_data', 'online_retail_2') }}
