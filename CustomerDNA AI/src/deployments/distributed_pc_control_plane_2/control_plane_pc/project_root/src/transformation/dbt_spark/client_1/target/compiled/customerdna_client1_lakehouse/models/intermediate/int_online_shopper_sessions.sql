select
    shopper_session_id,
    session_month,
    visitor_type,
    operating_system_id,
    browser_id,
    region_id,
    traffic_type_id,
    is_weekend_session,
    converted_in_session_flag,
    administrative_page_count,
    informational_page_count,
    product_related_page_count,
    administrative_duration_seconds,
    informational_duration_seconds,
    product_related_duration_seconds,
    bounce_rate,
    exit_rate,
    page_value_score,
    special_day_score,
    coalesce(administrative_page_count, 0) +
    coalesce(informational_page_count, 0) +
    coalesce(product_related_page_count, 0) as total_page_touchpoints,
    round(
        coalesce(administrative_duration_seconds, 0.0) +
        coalesce(informational_duration_seconds, 0.0) +
        coalesce(product_related_duration_seconds, 0.0),
        2
    ) as total_session_duration_seconds,
    round(
        coalesce(product_related_page_count, 0) * 1.0 +
        coalesce(page_value_score, 0.0) * 0.15 +
        (
            coalesce(administrative_duration_seconds, 0.0) +
            coalesce(informational_duration_seconds, 0.0) +
            coalesce(product_related_duration_seconds, 0.0)
        ) / 300.0 -
        coalesce(bounce_rate, 0.0) * 50.0 -
        coalesce(exit_rate, 0.0) * 25.0 +
        case when converted_in_session_flag then 10.0 else 0.0 end,
        2
    ) as engagement_score,
    case
        when converted_in_session_flag then 'converted'
        when coalesce(page_value_score, 0.0) >= 25 then 'high_intent'
        when coalesce(product_related_page_count, 0) >= 20 then 'researching'
        else 'browsing'
    end as lifecycle_stage,
    case
        when not coalesce(converted_in_session_flag, false)
            and coalesce(exit_rate, 0.0) >= 0.15
            and coalesce(bounce_rate, 0.0) >= 0.05 then true
        else false
    end as retention_risk_flag
from staging.stg_online_shoppers_intention