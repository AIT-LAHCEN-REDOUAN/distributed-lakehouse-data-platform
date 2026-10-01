
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select shopper_session_id
from intermediate.int_online_shopper_sessions
where shopper_session_id is null



  
  
      
    ) dbt_internal_test