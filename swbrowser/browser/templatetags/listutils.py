from django import template

register = template.Library()


@register.filter
def add(value, arg):
    return list(value) + [arg]


@register.filter
def remove(value, arg):
    return [x for x in value if x != arg]
