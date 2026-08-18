
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select bank_record_id
from staging.stg_bank_marketing
where bank_record_id is null



  
  
      
    ) dbt_internal_test