select
    {{ as_bigint('categoryid') }} as category_id,
    {{ as_bigint('parentid') }} as parent_category_id
from {{ source('raw_data', 'category_tree') }}
