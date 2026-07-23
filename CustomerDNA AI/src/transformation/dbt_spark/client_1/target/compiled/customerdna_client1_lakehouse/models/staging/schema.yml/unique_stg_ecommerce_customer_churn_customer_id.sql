
    
    

select
    customer_id as unique_field,
    count(*) as n_records

from staging.stg_ecommerce_customer_churn
where customer_id is not null
group by customer_id
having count(*) > 1


