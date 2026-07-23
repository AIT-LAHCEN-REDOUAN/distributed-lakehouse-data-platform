select
    to_timestamp(from_unixtime({{ as_bigint('timestamp') }} / 1000)) as property_timestamp,
    {{ as_bigint('itemid') }} as item_id,
    trim(property) as property_name,
    trim(value) as property_value
from {{ source('raw_data', 'item_properties') }}
