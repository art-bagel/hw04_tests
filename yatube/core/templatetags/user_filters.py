from django import template
from django.forms import BoundField

register = template.Library()


@register.filter
def addclass(field: BoundField, css: str) -> str:
    """Добавляет атрибут class в html тег."""
    return field.as_widget(attrs={'class': css})
