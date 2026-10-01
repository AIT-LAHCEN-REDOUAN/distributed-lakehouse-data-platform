select
    {{ tokenize_identifier('unified_entity_id') }} as unified_entity_token,
    entity_source,
    entity_grain,
    {{ tokenize_identifier('entity_key') }} as entity_key_token,
    case
        when known_customer_id is not null then {{ tokenize_identifier('known_customer_id') }}
        else null
    end as known_customer_token,
    age,
    geography,
    acquisition_channel,
    lifecycle_stage,
    engagement_score,
    monetary_value,
    transaction_count,
    conversion_flag,
    retention_risk_flag,
    recency_days,
    feature_snapshot_date,
    case
        when monetary_value >= 10000 then 'high_value'
        when monetary_value >= 1000 then 'mid_value'
        when monetary_value > 0 then 'emerging_value'
        else 'non_monetized'
    end as value_segment,
    case
        when engagement_score >= 20 then 'high_engagement'
        when engagement_score >= 8 then 'medium_engagement'
        else 'low_engagement'
    end as engagement_segment,
    case
        when retention_risk_flag then 'at_risk'
        when conversion_flag then 'converted'
        else 'nurture'
    end as retention_segment
from {{ ref('int_customer_360_feature_store') }}
