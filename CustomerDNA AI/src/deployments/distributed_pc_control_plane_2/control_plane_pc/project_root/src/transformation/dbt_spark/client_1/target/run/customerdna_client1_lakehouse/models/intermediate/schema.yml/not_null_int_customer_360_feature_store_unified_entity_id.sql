
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select unified_entity_id
from intermediate.int_customer_360_feature_store
where unified_entity_id is null



  
  
      
    ) dbt_internal_test