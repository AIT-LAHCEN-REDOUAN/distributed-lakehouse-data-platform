
  
    
        create or replace table staging.stg_retailrocket_category_tree
      
      
    using iceberg
      
      
      
      
      
      comment 'Typed staging view for retailrocket category hierarchy.'
      

      as
      select
    cast(
    coalesce(
        try_cast(nullif(trim(categoryid), '') as bigint),
        try_cast(nullif(trim(categoryid), '') as double)
    ) as bigint
) as category_id,
    cast(
    coalesce(
        try_cast(nullif(trim(parentid), '') as bigint),
        try_cast(nullif(trim(parentid), '') as double)
    ) as bigint
) as parent_category_id
from raw_data.category_tree
  