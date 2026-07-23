select
    to_timestamp(from_unixtime({{ as_bigint('timestamp') }} / 1000)) as event_timestamp,
    {{ as_bigint('visitorid') }} as visitor_id,
    trim(event) as event_type,
    {{ as_bigint('itemid') }} as item_id,
    {{ as_bigint('transactionid') }} as transaction_id
from {{ source('raw_data', 'events') }}
