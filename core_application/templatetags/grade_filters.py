from django import template

register = template.Library()


@register.filter
def calculate_semester_gpa(grades):
    total_quality_points = 0
    total_credit_hours = 0
    
    for grade in grades:
        if hasattr(grade, 'quality_points') and grade.quality_points:
            total_quality_points += grade.quality_points
            total_credit_hours += grade.enrollment.course.credit_hours
    
    return total_quality_points / total_credit_hours if total_credit_hours > 0 else 0



# your_app/templatetags/grade_filters.py
from django import template

register = template.Library()

@register.filter
def calculate_semester_gpa(grades):
    """
    Calculate GPA for a list of grades in a semester
    """
    total_quality_points = 0
    total_credit_hours = 0
    
    for grade in grades:
        if hasattr(grade, 'quality_points') and grade.quality_points is not None:
            total_quality_points += grade.quality_points
            total_credit_hours += grade.enrollment.course.credit_hours
    
    if total_credit_hours > 0:
        return round(total_quality_points / total_credit_hours, 2)
    return None

@register.filter
def passed_courses_count(grades):
    """Count how many courses were passed in a semester"""
    return sum(1 for grade in grades if hasattr(grade, 'is_passed') and grade.is_passed)

@register.filter
def failed_courses_count(grades):
    """Count how many courses were failed in a semester"""
    return sum(1 for grade in grades if hasattr(grade, 'is_passed') and not grade.is_passed and grade.grade)