
  
    
        create or replace table analytics.analytics_retailrocket_engagement
      
      
    using iceberg
      
      
      
      
      
      comment 'Final analytics mart for daily retailrocket behavioral trends.'
      

      as
      select
    date_trunc('day', event_timestamp) as event_day,
    event_type,
    count(*) as event_count,
    count(distinct visitor_id) as active_visitors,
    count(distinct item_id) as active_items
from staging.stg_retailrocket_events
where event_timestamp is not null
group by 1, 2
  