# finance/templatetags/fee_filters.py
# Create this file in: finance/templatetags/fee_filters.py

from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """
    Template filter to get dictionary value by key
    Usage: {{ my_dict|dict_get:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def div(value, arg):
    """
    Template filter to divide a value by an argument
    Usage: {{ value|div:3 }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.filter
def multiply(value, arg):
    """
    Template filter to multiply a value by an argument
    Usage: {{ value|multiply:0.5 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """
    Calculate percentage of value from total
    Usage: {{ value|percentage:total }}
    """
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """
    Subtract arg from value
    Usage: {{ value|subtract:10 }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def add_values(value, arg):
    """
    Add two values together
    Usage: {{ value|add_values:10 }}
    """
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0