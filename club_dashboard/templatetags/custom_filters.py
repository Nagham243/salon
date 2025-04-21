from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def divisibleby(value, arg):
    return value // arg

@register.filter
def modulo(value, arg):
    return value % arg

@register.filter
def get_item(dictionary, key):
    """Returns an item from a dictionary by key"""
    if isinstance(key, int):
        # Handle numeric indices for lists
        try:
            return dictionary[key]
        except (IndexError, TypeError):
            return None
    # Handle dictionary keys
    return dictionary.get(key)

@register.filter
def get_range(value):
    """Returns a range of numbers from 0 to value-1"""
    return range(value)

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    try:
        if not isinstance(arg, Decimal):
            arg = Decimal(str(arg))
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return value / arg
    except (ValueError, ZeroDivisionError, TypeError):
        return Decimal('0')

@register.filter
def subtract(value, arg):
    try:
        return value - arg
    except (ValueError, TypeError):
        return value