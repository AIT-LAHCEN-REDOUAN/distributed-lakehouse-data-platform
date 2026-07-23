
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select visitor_id
from intermediate.int_retailrocket_visitor_activity
where visitor_id is null



  
  
      
    ) dbt_internal_test