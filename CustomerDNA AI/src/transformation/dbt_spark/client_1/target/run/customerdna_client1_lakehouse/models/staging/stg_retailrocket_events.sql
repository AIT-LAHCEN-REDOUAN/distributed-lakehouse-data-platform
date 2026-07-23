
  
    
        create or replace table staging.stg_retailrocket_events
      
      
    using iceberg
      
      
      
      
      
      comment 'Typed staging view for retailrocket events.'
      

      as
      select
    to_timestamp(from_unixtime(cast(
    coalesce(
        try_cast(nullif(trim(timestamp), '') as bigint),
        try_cast(nullif(trim(timestamp), '') as double)
    ) as bigint
) / 1000)) as event_timestamp,
    cast(
    coalesce(
        try_cast(nullif(trim(visitorid), '') as bigint),
        try_cast(nullif(trim(visitorid), '') as double)
    ) as bigint
) as visitor_id,
    trim(event) as event_type,
    cast(
    coalesce(
        try_cast(nullif(trim(itemid), '') as bigint),
        try_cast(nullif(trim(itemid), '') as double)
    ) as bigint
) as item_id,
    cast(
    coalesce(
        try_cast(nullif(trim(transactionid), '') as bigint),
        try_cast(nullif(trim(transactionid), '') as double)
    ) as bigint
) as transaction_id
from raw_data.events
  