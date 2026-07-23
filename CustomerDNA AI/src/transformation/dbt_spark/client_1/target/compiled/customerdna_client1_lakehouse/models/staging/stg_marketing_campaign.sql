select
    cast(
    coalesce(
        try_cast(nullif(trim(id), '') as bigint),
        try_cast(nullif(trim(id), '') as double)
    ) as bigint
) as customer_id,
    cast(
    coalesce(
        try_cast(nullif(trim(year_birth), '') as int),
        try_cast(nullif(trim(year_birth), '') as double)
    ) as int
) as year_birth,
    trim(education) as education,
    trim(marital_status) as marital_status,
    try_cast(nullif(trim(income), '') as double) as income,
    cast(
    coalesce(
        try_cast(nullif(trim(kidhome), '') as int),
        try_cast(nullif(trim(kidhome), '') as double)
    ) as int
) as kidhome,
    cast(
    coalesce(
        try_cast(nullif(trim(teenhome), '') as int),
        try_cast(nullif(trim(teenhome), '') as double)
    ) as int
) as teenhome,
    coalesce(
    try_to_date(nullif(trim(dt_customer), ''), 'd-M-yyyy'),
    try_to_date(nullif(trim(dt_customer), ''))
) as customer_since_date,
    cast(
    coalesce(
        try_cast(nullif(trim(recency), '') as int),
        try_cast(nullif(trim(recency), '') as double)
    ) as int
) as recency_days,
    try_cast(nullif(trim(mntwines), '') as double) as amount_wines,
    try_cast(nullif(trim(mntfruits), '') as double) as amount_fruits,
    try_cast(nullif(trim(mntmeatproducts), '') as double) as amount_meat,
    try_cast(nullif(trim(mntfishproducts), '') as double) as amount_fish,
    try_cast(nullif(trim(mntsweetproducts), '') as double) as amount_sweets,
    try_cast(nullif(trim(mntgoldprods), '') as double) as amount_gold,
    cast(
    coalesce(
        try_cast(nullif(trim(numdealspurchases), '') as int),
        try_cast(nullif(trim(numdealspurchases), '') as double)
    ) as int
) as deal_purchases,
    cast(
    coalesce(
        try_cast(nullif(trim(numwebpurchases), '') as int),
        try_cast(nullif(trim(numwebpurchases), '') as double)
    ) as int
) as web_purchases,
    cast(
    coalesce(
        try_cast(nullif(trim(numcatalogpurchases), '') as int),
        try_cast(nullif(trim(numcatalogpurchases), '') as double)
    ) as int
) as catalog_purchases,
    cast(
    coalesce(
        try_cast(nullif(trim(numstorepurchases), '') as int),
        try_cast(nullif(trim(numstorepurchases), '') as double)
    ) as int
) as store_purchases,
    cast(
    coalesce(
        try_cast(nullif(trim(numwebvisitsmonth), '') as int),
        try_cast(nullif(trim(numwebvisitsmonth), '') as double)
    ) as int
) as monthly_web_visits,
    cast(
    coalesce(
        try_cast(nullif(trim(acceptedcmp1), '') as int),
        try_cast(nullif(trim(acceptedcmp1), '') as double)
    ) as int
) as accepted_campaign_1,
    cast(
    coalesce(
        try_cast(nullif(trim(acceptedcmp2), '') as int),
        try_cast(nullif(trim(acceptedcmp2), '') as double)
    ) as int
) as accepted_campaign_2,
    cast(
    coalesce(
        try_cast(nullif(trim(acceptedcmp3), '') as int),
        try_cast(nullif(trim(acceptedcmp3), '') as double)
    ) as int
) as accepted_campaign_3,
    cast(
    coalesce(
        try_cast(nullif(trim(acceptedcmp4), '') as int),
        try_cast(nullif(trim(acceptedcmp4), '') as double)
    ) as int
) as accepted_campaign_4,
    cast(
    coalesce(
        try_cast(nullif(trim(acceptedcmp5), '') as int),
        try_cast(nullif(trim(acceptedcmp5), '') as double)
    ) as int
) as accepted_campaign_5,
    cast(
    coalesce(
        try_cast(nullif(trim(complain), '') as int),
        try_cast(nullif(trim(complain), '') as double)
    ) as int
) as complaint_flag,
    try_cast(nullif(trim(z_costcontact), '') as double) as campaign_contact_cost,
    try_cast(nullif(trim(z_revenue), '') as double) as campaign_revenue,
    cast(
    coalesce(
        try_cast(nullif(trim(response), '') as int),
        try_cast(nullif(trim(response), '') as double)
    ) as int
) as last_campaign_response_flag
from raw_data.marketing_campaign