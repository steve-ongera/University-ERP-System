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