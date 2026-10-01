
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    unified_entity_token as unique_field,
    count(*) as n_records

from analytics.analytics_customer360_overview
where unified_entity_token is not null
group by unified_entity_token
having count(*) > 1



  
  
      
    ) dbt_internal_test