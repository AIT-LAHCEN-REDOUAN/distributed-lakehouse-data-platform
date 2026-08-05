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
    from {{ source('raw_data', 'bank_marketing') }}
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
    {{ as_int('age') }} as age,
    trim(job) as job,
    trim(marital) as marital_status,
    trim(education) as education_level,
    {{ as_yes_no_boolean('credit_default') }} as has_credit_default,
    {{ as_yes_no_boolean('housing') }} as has_housing_loan,
    {{ as_yes_no_boolean('loan') }} as has_personal_loan,
    trim(contact) as contact_channel,
    trim(month) as contact_month,
    trim(day_of_week) as contact_day_of_week,
    {{ as_int('duration') }} as call_duration_seconds,
    {{ as_int('campaign') }} as contact_attempt_count,
    case
        when {{ as_int('pdays') }} = 999 then null
        else {{ as_int('pdays') }}
    end as prior_contact_gap_days,
    case
        when {{ as_int('pdays') }} = 999 then false
        else true
    end as had_prior_contact,
    {{ as_int('previous') }} as previous_contact_count,
    trim(poutcome) as previous_campaign_outcome,
    {{ as_double('emp_var_rate') }} as employment_variation_rate,
    {{ as_double('cons_price_idx') }} as consumer_price_index,
    {{ as_double('cons_conf_idx') }} as consumer_confidence_index,
    {{ as_double('euribor3m') }} as euribor_3m_rate,
    {{ as_double('nr_employed') }} as employee_count,
    {{ as_yes_no_boolean('subscription_result') }} as subscribed_term_deposit_flag
from source
