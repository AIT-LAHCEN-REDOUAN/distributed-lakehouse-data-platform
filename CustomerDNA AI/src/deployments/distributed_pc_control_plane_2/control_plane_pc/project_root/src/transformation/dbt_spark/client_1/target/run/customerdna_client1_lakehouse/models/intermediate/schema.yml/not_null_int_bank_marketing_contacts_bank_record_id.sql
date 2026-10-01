
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select bank_record_id
from intermediate.int_bank_marketing_contacts
where bank_record_id is null



  
  
      
    ) dbt_internal_test