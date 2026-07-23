select
    visitor_id,
    count(*) as total_events,
    count_if(event_type = 'view') as view_events,
    count_if(event_type = 'addtocart') as add_to_cart_events,
    count_if(event_type = 'transaction') as transaction_events,
    count(distinct item_id) as distinct_items_touched,
    min(event_timestamp) as first_event_timestamp,
    max(event_timestamp) as last_event_timestamp
from {{ ref('stg_retailrocket_events') }}
group by visitor_id
