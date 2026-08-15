
  
    
        create or replace table intermediate.int_customer_360_feature_store
      
      
    using iceberg
      
      
      
      
      
      comment 'Harmonized feature-store style entity table spanning campaign, web, and sales domains without unsafe row-level joins.'
      

      as
      with bank_contacts as (
    select * from intermediate.int_bank_marketing_contacts
),
shopper_sessions as (
    select * from intermediate.int_online_shopper_sessions
),
retail_customers as (
    select * from intermediate.int_online_retail_customer_sales
),
deduplicated_bank_contacts as (
    select distinct *
    from bank_contacts
),
deduplicated_shopper_sessions as (
    select distinct *
    from shopper_sessions
)

select
    concat('bank_marketing:', bank_record_id) as unified_entity_id,
    'bank_marketing' as entity_source,
    'prospect' as entity_grain,
    bank_record_id as entity_key,
    cast(null as bigint) as known_customer_id,
    age,
    cast(null as string) as geography,
    contact_channel as acquisition_channel,
    lifecycle_stage,
    engagement_score,
    conversion_value as monetary_value,
    coalesce(contact_attempt_count, 0) as transaction_count,
    coalesce(subscribed_term_deposit_flag, false) as conversion_flag,
    retention_risk_flag,
    prior_contact_gap_days as recency_days,
    cast(null as date) as feature_snapshot_date
from deduplicated_bank_contacts

union all

select
    concat('online_shoppers_intention:', shopper_session_id) as unified_entity_id,
    'online_shoppers_intention' as entity_source,
    'session' as entity_grain,
    shopper_session_id as entity_key,
    cast(null as bigint) as known_customer_id,
    cast(null as int) as age,
    cast(region_id as string) as geography,
    concat('traffic_', cast(traffic_type_id as string)) as acquisition_channel,
    lifecycle_stage,
    engagement_score,
    coalesce(page_value_score, 0.0) as monetary_value,
    coalesce(total_page_touchpoints, 0) as transaction_count,
    coalesce(converted_in_session_flag, false) as conversion_flag,
    retention_risk_flag,
    cast(null as int) as recency_days,
    cast(null as date) as feature_snapshot_date
from deduplicated_shopper_sessions

union all

select
    concat('online_retail_2:', cast(customer_id as string)) as unified_entity_id,
    'online_retail_2' as entity_source,
    'customer' as entity_grain,
    cast(customer_id as string) as entity_key,
    customer_id as known_customer_id,
    cast(null as int) as age,
    primary_country as geography,
    'retail_transaction' as acquisition_channel,
    case
        when recency_days <= 30 then 'active'
        when recency_days <= 90 then 'warm'
        else 'cooling'
    end as lifecycle_stage,
    round(
        coalesce(completed_invoice_count, 0) * 1.5 +
        coalesce(distinct_product_count, 0) * 0.5 +
        coalesce(net_revenue, 0.0) / 100.0,
        2
    ) as engagement_score,
    coalesce(net_revenue, 0.0) as monetary_value,
    coalesce(completed_invoice_count, 0) as transaction_count,
    case
        when coalesce(net_revenue, 0.0) > 0 then true
        else false
    end as conversion_flag,
    case
        when coalesce(recency_days, 9999) > 180 then true
        else false
    end as retention_risk_flag,
    recency_days,
    to_date(last_order_timestamp) as feature_snapshot_date
from retail_customers
  