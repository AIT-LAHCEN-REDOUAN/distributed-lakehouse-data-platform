select
    bank_record_id,
    age,
    job,
    marital_status,
    education_level,
    has_credit_default,
    has_housing_loan,
    has_personal_loan,
    contact_channel,
    contact_month,
    contact_day_of_week,
    call_duration_seconds,
    contact_attempt_count,
    prior_contact_gap_days,
    had_prior_contact,
    previous_contact_count,
    previous_campaign_outcome,
    employment_variation_rate,
    consumer_price_index,
    consumer_confidence_index,
    euribor_3m_rate,
    employee_count,
    subscribed_term_deposit_flag,
    round(
        coalesce(call_duration_seconds, 0) / 60.0 +
        coalesce(contact_attempt_count, 0) * 0.5 +
        coalesce(previous_contact_count, 0) * 0.75 +
        case when subscribed_term_deposit_flag then 5.0 else 0.0 end,
        2
    ) as engagement_score,
    case
        when subscribed_term_deposit_flag then 'converted'
        when previous_campaign_outcome = 'success' then 'warm_lead'
        when had_prior_contact then 'nurture'
        else 'new_lead'
    end as lifecycle_stage,
    case
        when not coalesce(subscribed_term_deposit_flag, false)
            and coalesce(contact_attempt_count, 0) >= 5 then true
        when previous_campaign_outcome = 'failure'
            and coalesce(contact_attempt_count, 0) >= 3 then true
        else false
    end as retention_risk_flag,
    case
        when subscribed_term_deposit_flag then 1.0
        else 0.0
    end as conversion_value
from {{ ref('stg_bank_marketing') }}
