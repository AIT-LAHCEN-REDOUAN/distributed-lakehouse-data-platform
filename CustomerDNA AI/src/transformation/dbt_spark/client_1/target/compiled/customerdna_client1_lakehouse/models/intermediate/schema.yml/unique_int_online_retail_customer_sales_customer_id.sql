
    
    

select
    customer_id as unique_field,
    count(*) as n_records

from intermediate.int_online_retail_customer_sales
where customer_id is not null
group by customer_id
having count(*) > 1


