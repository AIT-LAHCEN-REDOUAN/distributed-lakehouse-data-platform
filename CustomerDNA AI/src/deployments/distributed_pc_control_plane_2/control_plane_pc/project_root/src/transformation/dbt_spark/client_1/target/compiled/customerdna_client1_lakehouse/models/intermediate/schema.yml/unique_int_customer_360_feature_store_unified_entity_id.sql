
    
    

select
    unified_entity_id as unique_field,
    count(*) as n_records

from intermediate.int_customer_360_feature_store
where unified_entity_id is not null
group by unified_entity_id
having count(*) > 1


