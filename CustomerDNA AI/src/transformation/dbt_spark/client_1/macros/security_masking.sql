{% macro tokenize_identifier(value_expression) -%}
sha2(concat('{{ var("pii_token_salt") }}', '::', coalesce(cast({{ value_expression }} as string), 'null')), 256)
{%- endmacro %}
