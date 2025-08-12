# templatetags/room_filters.py
from django import template

register = template.Library()

@register.filter
def active_count(rooms):
    return rooms.filter(is_active=True).count()

@register.filter
def inactive_count(rooms):
    return rooms.filter(is_active=False).count()
