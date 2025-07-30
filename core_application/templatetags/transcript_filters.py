# templatetags/marks_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary using key"""
    if dictionary and key is not None:
        # Handle both string and integer keys
        try:
            if isinstance(key, str) and key.isdigit():
                key = int(key)
            return dictionary.get(key, {})
        except (TypeError, ValueError):
            return {}
    return {}

@register.filter
def get_nested(dictionary, key):
    """Get nested item from dictionary"""
    if dictionary and key:
        try:
            return dictionary.get(int(key), {})
        except (TypeError, ValueError):
            return {}
    return {}

@register.filter
def default_if_none(value, default=''):
    """Return default if value is None"""
    return default if value is None else value