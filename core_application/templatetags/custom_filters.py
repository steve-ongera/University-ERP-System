# templatetags/custom_filters.py
# Create this file in your app's templatetags directory

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary using key
    Usage: {{ dict|get_item:key }}
    """
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def lookup(dictionary, key):
    """
    Alternative name for get_item filter
    Usage: {{ dict|lookup:key }}
    """
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def filter_by_course(queryset, course_code):
    """
    Filter queryset by course code
    Usage: {{ timetable_entries|filter_by_course:course_code }}
    """
    if queryset:
        return queryset.filter(course__code=course_code)
    return queryset

@register.filter
def filter_by_programme(queryset, programme_code):
    """
    Filter queryset by programme code
    Usage: {{ timetable_entries|filter_by_programme:programme_code }}
    """
    if queryset:
        return queryset.filter(programme__code=programme_code)
    return queryset

@register.simple_tag
def multiply(value, arg):
    """
    Multiply two numbers
    Usage: {% multiply value arg %}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    
from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value"""
    try:
        return value - arg
    except (TypeError, ValueError):
        return value


from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary using key
    Usage: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def subtract(value, arg):
    """
    Subtract the argument from the value
    Usage: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def percentage(value, total):
    """
    Calculate percentage
    Usage: {{ value|percentage:total }}
    """
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def index(sequence, position):
    """
    Get item at index from list/tuple
    Usage: {{ list|index:0 }}
    """
    try:
        return sequence[int(position)]
    except (IndexError, ValueError, TypeError):
        return None
    

from django import template

register = template.Library()

@register.filter(name='range_filter')
def range_filter(value):
    """
    Creates a range from 1 to value (inclusive)
    Usage: {% for year in programme.duration_years|range_filter %}
    """
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return range(0)


@register.filter(name='get_range')
def get_range(value, start=1):
    """
    Alternative filter that allows specifying start value
    Usage: {% for i in 5|get_range %}
    """
    try:
        return range(start, int(value) + 1)
    except (ValueError, TypeError):
        return range(0)


@register.filter(name='times')
def times(number):
    """
    Returns a range for the given number
    Usage: {% for i in 5|times %}
    """
    try:
        return range(1, int(number) + 1)
    except (ValueError, TypeError):
        return range(0)