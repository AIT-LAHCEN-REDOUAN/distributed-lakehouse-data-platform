{% macro empty_to_null(column_name) -%}
nullif(trim({{ column_name }}), '')
{%- endmacro %}

{% macro as_int(column_name) -%}
cast(
    coalesce(
        try_cast({{ empty_to_null(column_name) }} as int),
        try_cast({{ empty_to_null(column_name) }} as double)
    ) as int
)
{%- endmacro %}

{% macro as_bigint(column_name) -%}
cast(
    coalesce(
        try_cast({{ empty_to_null(column_name) }} as bigint),
        try_cast({{ empty_to_null(column_name) }} as double)
    ) as bigint
)
{%- endmacro %}

{% macro as_double(column_name) -%}
try_cast({{ empty_to_null(column_name) }} as double)
{%- endmacro %}

{% macro as_date(column_name, pattern='yyyy-MM-dd') -%}
coalesce(
    try_to_date({{ empty_to_null(column_name) }}, '{{ pattern }}'),
    try_to_date({{ empty_to_null(column_name) }})
)
{%- endmacro %}

{% macro as_timestamp(column_name, pattern=None) -%}
{% if pattern %}
coalesce(
    try_to_timestamp({{ empty_to_null(column_name) }}, '{{ pattern }}'),
    try_to_timestamp({{ empty_to_null(column_name) }})
)
{% else %}
try_to_timestamp({{ empty_to_null(column_name) }})
{% endif %}
{%- endmacro %}

{% macro as_boolean_flag(column_name) -%}
case
    when lower(trim({{ column_name }})) in ('1', 'true', 'yes', 'y') then true
    when lower(trim({{ column_name }})) in ('0', 'false', 'no', 'n') then false
    else null
end
{%- endmacro %}

{% macro as_yes_no_boolean(column_name) -%}
case
    when lower(trim({{ column_name }})) = 'yes' then true
    when lower(trim({{ column_name }})) = 'no' then false
    else null
end
{%- endmacro %}
