"""Custom template filters for the blog app."""

from django import template

register = template.Library()


@register.filter
def dict_get(mapping, key):
    """Look up a dictionary value by a variable key in templates.

    Django templates can't do dict[variable], so this filter enables:
        {{ some_dict|dict_get:some_key }}
    Returns an empty string if missing or not a dict.
    """
    if isinstance(mapping, dict):
        return mapping.get(key, "")
    return ""
