
  
    
        create or replace table staging.stg_online_shoppers_intention
      
      
    using iceberg
      
      
      
      
      
      comment 'Typed staging model for digital browsing sessions and purchase intent.'
      

      as
      select
    sha2(
        concat_ws(
            '||',
            coalesce(cast(administrative as string), ''),
            coalesce(cast(administrative_duration as string), ''),
            coalesce(cast(informational as string), ''),
            coalesce(cast(informational_duration as string), ''),
            coalesce(cast(productrelated as string), ''),
            coalesce(cast(productrelated_duration as string), ''),
            coalesce(cast(bouncerates as string), ''),
            coalesce(cast(exitrates as string), ''),
            coalesce(cast(pagevalues as string), ''),
            coalesce(cast(specialday as string), ''),
            coalesce(month, ''),
            coalesce(cast(operatingsystems as string), ''),
            coalesce(cast(browser as string), ''),
            coalesce(cast(region as string), ''),
            coalesce(cast(traffictype as string), ''),
            coalesce(visitortype, ''),
            coalesce(weekend, ''),
            coalesce(revenue, '')
        ),
        256
    ) as shopper_session_id,
    cast(
    coalesce(
        try_cast(nullif(trim(administrative), '') as int),
        try_cast(nullif(trim(administrative), '') as double)
    ) as int
) as administrative_page_count,
    try_cast(nullif(trim(administrative_duration), '') as double) as administrative_duration_seconds,
    cast(
    coalesce(
        try_cast(nullif(trim(informational), '') as int),
        try_cast(nullif(trim(informational), '') as double)
    ) as int
) as informational_page_count,
    try_cast(nullif(trim(informational_duration), '') as double) as informational_duration_seconds,
    cast(
    coalesce(
        try_cast(nullif(trim(productrelated), '') as int),
        try_cast(nullif(trim(productrelated), '') as double)
    ) as int
) as product_related_page_count,
    try_cast(nullif(trim(productrelated_duration), '') as double) as product_related_duration_seconds,
    try_cast(nullif(trim(bouncerates), '') as double) as bounce_rate,
    try_cast(nullif(trim(exitrates), '') as double) as exit_rate,
    try_cast(nullif(trim(pagevalues), '') as double) as page_value_score,
    try_cast(nullif(trim(specialday), '') as double) as special_day_score,
    trim(month) as session_month,
    cast(
    coalesce(
        try_cast(nullif(trim(operatingsystems), '') as int),
        try_cast(nullif(trim(operatingsystems), '') as double)
    ) as int
) as operating_system_id,
    cast(
    coalesce(
        try_cast(nullif(trim(browser), '') as int),
        try_cast(nullif(trim(browser), '') as double)
    ) as int
) as browser_id,
    cast(
    coalesce(
        try_cast(nullif(trim(region), '') as int),
        try_cast(nullif(trim(region), '') as double)
    ) as int
) as region_id,
    cast(
    coalesce(
        try_cast(nullif(trim(traffictype), '') as int),
        try_cast(nullif(trim(traffictype), '') as double)
    ) as int
) as traffic_type_id,
    trim(visitortype) as visitor_type,
    case
    when lower(trim(weekend)) in ('1', 'true', 'yes', 'y') then true
    when lower(trim(weekend)) in ('0', 'false', 'no', 'n') then false
    else null
end as is_weekend_session,
    case
    when lower(trim(revenue)) in ('1', 'true', 'yes', 'y') then true
    when lower(trim(revenue)) in ('0', 'false', 'no', 'n') then false
    else null
end as converted_in_session_flag
from raw_data.online_shoppers_intention
  