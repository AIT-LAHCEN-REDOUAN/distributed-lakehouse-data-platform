
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select customer_id
from intermediate.int_customer_commercial_360
where customer_id is null



  
  
      
    ) dbt_internal_test