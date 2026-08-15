with bank_performance as (
    select
        'bank_marketing' as source_system,
        contact_month as period_label,
        contact_channel as channel_label,
        count(*) as entity_count,
        sum(case when subscribed_term_deposit_flag then 1 else 0 end) as conversion_count,
        round(avg(engagement_score), 2) as average_engagement_score,
        round(avg(conversion_value), 2) as average_monetary_value
    from intermediate.int_bank_marketing_contacts
    group by 1, 2, 3
),
shopper_performance as (
    select
        'online_shoppers_intention' as source_system,
        session_month as period_label,
        concat('traffic_', cast(traffic_type_id as string)) as channel_label,
        count(*) as entity_count,
        sum(case when converted_in_session_flag then 1 else 0 end) as conversion_count,
        round(avg(engagement_score), 2) as average_engagement_score,
        round(avg(page_value_score), 2) as average_monetary_value
    from intermediate.int_online_shopper_sessions
    group by 1, 2, 3
)

select
    source_system,
    period_label,
    channel_label,
    entity_count,
    conversion_count,
    round(
        case
            when entity_count > 0 then conversion_count / entity_count
            else 0
        end,
        4
    ) as conversion_rate,
    average_engagement_score,
    average_monetary_value
from bank_performance

union all

select
    source_system,
    period_label,
    channel_label,
    entity_count,
    conversion_count,
    round(
        case
            when entity_count > 0 then conversion_count / entity_count
            else 0
        end,
        4
    ) as conversion_rate,
    average_engagement_score,
    average_monetary_value
from shopper_performance