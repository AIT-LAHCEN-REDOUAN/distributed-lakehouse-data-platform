
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select unified_entity_token
from analytics.analytics_customer360_overview
where unified_entity_token is null



  
  
      
    ) dbt_internal_test