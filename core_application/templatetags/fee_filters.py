# templatetags/fee_filters.py
from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """Get a value from a dictionary using a key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def get_fee_data(fees_by_year, keys):
    """
    Get nested fee data using year.semester format
    Usage: {{ fees_by_year|get_fee_data:"1.2" }} for year 1, semester 2
    """
    if not isinstance(fees_by_year, dict):
        return None
    
    try:
        if '.' in str(keys):
            year, semester = str(keys).split('.', 1)
            year = int(year)
            semester = int(semester)
        else:
            return None
            
        year_data = fees_by_year.get(year, {})
        if isinstance(year_data, dict):
            return year_data.get(semester, None)
        return None
    except (ValueError, AttributeError):
        return None

@register.filter
def get_nested_value(data, path):
    """
    Get nested value from dictionary using dot notation
    Usage: {{ data|get_nested_value:"key1.key2.key3" }}
    """
    if not data:
        return None
    
    keys = str(path).split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            try:
                current = getattr(current, key, None)
            except (AttributeError, TypeError):
                return None
        
        if current is None:
            return None
    
    return current

@register.filter
def has_fee_structure(fees_by_year, year_semester):
    """
    Check if fee structure exists for year.semester
    Usage: {{ fees_by_year|has_fee_structure:"1.2" }}
    """
    fee_data = get_fee_data(fees_by_year, year_semester)
    if fee_data and isinstance(fee_data, dict):
        return fee_data.get('exists', False)
    return False

@register.filter
def get_net_fee(fees_by_year, year_semester):
    """
    Get net fee for specific year.semester
    Usage: {{ fees_by_year|get_net_fee:"1.2" }}
    """
    fee_data = get_fee_data(fees_by_year, year_semester)
    if fee_data and isinstance(fee_data, dict):
        return fee_data.get('net_fee', 0)
    return 0

@register.filter
def div(value, divisor):
    """Divide a value by a divisor"""
    try:
        return float(value) / float(divisor)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def multiply(value, multiplier):
    """Multiply a value by a multiplier"""
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0

@register.filter
def currency(value):
    """Format a number as currency"""
    try:
        return f"KSh {float(value):,.2f}"
    except (ValueError, TypeError):
        return "KSh 0.00"

@register.filter
def safe_get_attr(obj, attr_name):
    """Safely get an attribute from an object"""
    try:
        return getattr(obj, attr_name, None)
    except (AttributeError, TypeError):
        return None

@register.filter
def make_key(year, semester):
    """Create a key for year.semester lookup"""
    return f"{year}.{semester}"

@register.simple_tag
def get_semester_fee_data(fees_by_year, year, semester):
    """Template tag to get fee data for specific year and semester"""
    if not isinstance(fees_by_year, dict):
        return None
    
    year_data = fees_by_year.get(year, {})
    if isinstance(year_data, dict):
        return year_data.get(semester, None)
    return None