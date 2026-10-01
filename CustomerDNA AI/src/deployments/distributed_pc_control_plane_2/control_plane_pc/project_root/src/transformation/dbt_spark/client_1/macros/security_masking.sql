{% macro tokenize_identifier(value_expression) -%}
sha2(
    concat(
        '{{ env_var("CUSTOMERDNA_PII_TOKEN_SALT", "CustomerDNA_PII_Token_Salt_2026!") }}',
        '::',
        coalesce(cast({{ value_expression }} as string), 'null')
    ),
    256
)
{%- endmacro %}
