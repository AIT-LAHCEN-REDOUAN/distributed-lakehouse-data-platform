
  
    
        create or replace table staging.stg_bank_marketing
      
      
    using iceberg
      
      
      
      
      
      comment 'Typed staging model for outbound bank marketing contacts and conversion outcomes.'
      

      as
      with source as (
    select
        age,
        job,
        marital,
        education,
        `default` as credit_default,
        housing,
        loan,
        contact,
        month,
        day_of_week,
        duration,
        campaign,
        pdays,
        previous,
        poutcome,
        emp_var_rate,
        cons_price_idx,
        cons_conf_idx,
        euribor3m,
        nr_employed,
        y as subscription_result
    from raw_data.bank_marketing
)

select
    sha2(
        concat_ws(
            '||',
            coalesce(cast(age as string), ''),
            coalesce(job, ''),
            coalesce(marital, ''),
            coalesce(education, ''),
            coalesce(credit_default, ''),
            coalesce(housing, ''),
            coalesce(loan, ''),
            coalesce(contact, ''),
            coalesce(month, ''),
            coalesce(day_of_week, ''),
            coalesce(cast(duration as string), ''),
            coalesce(cast(campaign as string), ''),
            coalesce(cast(pdays as string), ''),
            coalesce(cast(previous as string), ''),
            coalesce(poutcome, ''),
            coalesce(cast(emp_var_rate as string), ''),
            coalesce(cast(cons_price_idx as string), ''),
            coalesce(cast(cons_conf_idx as string), ''),
            coalesce(cast(euribor3m as string), ''),
            coalesce(cast(nr_employed as string), ''),
            coalesce(subscription_result, '')
        ),
        256
    ) as bank_record_id,
    cast(
    coalesce(
        try_cast(nullif(trim(age), '') as int),
        try_cast(nullif(trim(age), '') as double)
    ) as int
) as age,
    trim(job) as job,
    trim(marital) as marital_status,
    trim(education) as education_level,
    case
    when lower(trim(credit_default)) in ('1', 'true', 'yes', 'y') then true
    when lower(trim(credit_default)) in ('0', 'false', 'no', 'n') then false
    else null
end as has_credit_default,
    case
    when lower(trim(housing)) in ('1', 'true', 'yes', 'y') then true
    when lower(trim(housing)) in ('0', 'false', 'no', 'n') then false
    else null
end as has_housing_loan,
    case
    when lower(trim(loan)) in ('1', 'true', 'yes', 'y') then true
    when lower(trim(loan)) in ('0', 'false', 'no', 'n') then false
    else null
end as has_personal_loan,
    trim(contact) as contact_channel,
    trim(month) as contact_month,
    trim(day_of_week) as contact_day_of_week,
    cast(
    coalesce(
        try_cast(nullif(trim(duration), '') as int),
        try_cast(nullif(trim(duration), '') as double)
    ) as int
) as call_duration_seconds,
    cast(
    coalesce(
        try_cast(nullif(trim(campaign), '') as int),
        try_cast(nullif(trim(campaign), '') as double)
    ) as int
) as contact_attempt_count,
    case
        when cast(
    coalesce(
        try_cast(nullif(trim(pdays), '') as int),
        try_cast(nullif(trim(pdays), '') as double)
    ) as int
) = 999 then null
        else cast(
    coalesce(
        try_cast(nullif(trim(pdays), '') as int),
        try_cast(nullif(trim(pdays), '') as double)
    ) as int
)
    end as prior_contact_gap_days,
    case
        when cast(
    coalesce(
        try_cast(nullif(trim(pdays), '') as int),
        try_cast(nullif(trim(pdays), '') as double)
    ) as int
) = 999 then false
        else true
    end as had_prior_contact,
    cast(
    coalesce(
        try_cast(nullif(trim(previous), '') as int),
        try_cast(nullif(trim(previous), '') as double)
    ) as int
) as previous_contact_count,
    trim(poutcome) as previous_campaign_outcome,
    try_cast(nullif(trim(emp_var_rate), '') as double) as employment_variation_rate,
    try_cast(nullif(trim(cons_price_idx), '') as double) as consumer_price_index,
    try_cast(nullif(trim(cons_conf_idx), '') as double) as consumer_confidence_index,
    try_cast(nullif(trim(euribor3m), '') as double) as euribor_3m_rate,
    try_cast(nullif(trim(nr_employed), '') as double) as employee_count,
    case
    when lower(trim(subscription_result)) in ('1', 'true', 'yes', 'y') then true
    when lower(trim(subscription_result)) in ('0', 'false', 'no', 'n') then false
    else null
end as subscribed_term_deposit_flag
from source
  