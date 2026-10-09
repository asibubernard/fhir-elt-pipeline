{% macro mask_phi(column) %}
to_hex(sha256(cast({{ column }} as string)))
{% endmacro %}