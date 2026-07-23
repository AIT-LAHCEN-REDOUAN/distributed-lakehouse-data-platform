{% macro spark__create_schema(relation) %}
  {% do log(
    "Skipping dbt-driven schema creation for "
    ~ relation.without_identifier()
    ~ " because lakehouse namespaces are initialized by the setup pipeline.",
    info=True
  ) %}
{% endmacro %}


{% macro spark__drop_schema(relation) %}
  {% do log(
    "Skipping dbt-driven schema drop for "
    ~ relation.without_identifier()
    ~ " because lakehouse namespaces are managed outside dbt.",
    info=True
  ) %}
{% endmacro %}


{% macro generate_schema_name(custom_schema_name, node) %}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{% endmacro %}
