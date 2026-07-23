select
    to_timestamp(from_unixtime(cast(
    coalesce(
        try_cast(nullif(trim(timestamp), '') as bigint),
        try_cast(nullif(trim(timestamp), '') as double)
    ) as bigint
) / 1000)) as property_timestamp,
    cast(
    coalesce(
        try_cast(nullif(trim(itemid), '') as bigint),
        try_cast(nullif(trim(itemid), '') as double)
    ) as bigint
) as item_id,
    trim(property) as property_name,
    trim(value) as property_value
from raw_data.item_properties