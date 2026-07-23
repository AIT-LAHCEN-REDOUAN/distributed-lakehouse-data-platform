
  
    
        create or replace table staging.stg_ecommerce_customer_churn
      
      
    using iceberg
      
      
      
      
      
      comment 'Typed staging view for the ecommerce churn dataset.'
      

      as
      select
    cast(
    coalesce(
        try_cast(nullif(trim(customerid), '') as bigint),
        try_cast(nullif(trim(customerid), '') as double)
    ) as bigint
) as customer_id,
    case
    when lower(trim(churn)) in ('1', 'true', 'yes', 'y') then true
    when lower(trim(churn)) in ('0', 'false', 'no', 'n') then false
    else null
end as is_churned,
    cast(
    coalesce(
        try_cast(nullif(trim(tenure), '') as int),
        try_cast(nullif(trim(tenure), '') as double)
    ) as int
) as tenure_months,
    trim(preferredlogindevice) as preferred_login_device,
    cast(
    coalesce(
        try_cast(nullif(trim(citytier), '') as int),
        try_cast(nullif(trim(citytier), '') as double)
    ) as int
) as city_tier,
    try_cast(nullif(trim(warehousetohome), '') as double) as warehouse_to_home_km,
    trim(preferredpaymentmode) as preferred_payment_mode,
    trim(gender) as gender,
    try_cast(nullif(trim(hourspendonapp), '') as double) as hours_spent_on_app,
    cast(
    coalesce(
        try_cast(nullif(trim(numberofdeviceregistered), '') as int),
        try_cast(nullif(trim(numberofdeviceregistered), '') as double)
    ) as int
) as registered_device_count,
    trim(preferedordercat) as preferred_order_category,
    cast(
    coalesce(
        try_cast(nullif(trim(satisfactionscore), '') as int),
        try_cast(nullif(trim(satisfactionscore), '') as double)
    ) as int
) as satisfaction_score,
    trim(maritalstatus) as marital_status,
    cast(
    coalesce(
        try_cast(nullif(trim(numberofaddress), '') as int),
        try_cast(nullif(trim(numberofaddress), '') as double)
    ) as int
) as address_count,
    cast(
    coalesce(
        try_cast(nullif(trim(complain), '') as int),
        try_cast(nullif(trim(complain), '') as double)
    ) as int
) as complaint_flag,
    try_cast(nullif(trim(orderamounthikefromlastyear), '') as double) as order_amount_hike_pct,
    cast(
    coalesce(
        try_cast(nullif(trim(couponused), '') as int),
        try_cast(nullif(trim(couponused), '') as double)
    ) as int
) as coupon_used_count,
    cast(
    coalesce(
        try_cast(nullif(trim(ordercount), '') as int),
        try_cast(nullif(trim(ordercount), '') as double)
    ) as int
) as order_count,
    cast(
    coalesce(
        try_cast(nullif(trim(daysincelastorder), '') as int),
        try_cast(nullif(trim(daysincelastorder), '') as double)
    ) as int
) as days_since_last_order,
    try_cast(nullif(trim(cashbackamount), '') as double) as cashback_amount
from raw_data.e_commerce_customer_churn
  