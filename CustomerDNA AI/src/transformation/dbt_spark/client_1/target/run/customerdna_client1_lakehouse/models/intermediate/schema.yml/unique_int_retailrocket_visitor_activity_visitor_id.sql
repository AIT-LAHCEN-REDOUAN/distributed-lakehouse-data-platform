
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    visitor_id as unique_field,
    count(*) as n_records

from intermediate.int_retailrocket_visitor_activity
where visitor_id is not null
group by visitor_id
having count(*) > 1



  
  
      
    ) dbt_internal_test