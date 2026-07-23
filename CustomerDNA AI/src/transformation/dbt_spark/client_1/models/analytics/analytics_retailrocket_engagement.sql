select
    date_trunc('day', event_timestamp) as event_day,
    event_type,
    count(*) as event_count,
    count(distinct visitor_id) as active_visitors,
    count(distinct item_id) as active_items
from {{ ref('stg_retailrocket_events') }}
where event_timestamp is not null
group by 1, 2
