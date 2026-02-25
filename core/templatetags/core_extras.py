from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def closes_in(dt):
    """Format as 'X days Y hours Z minutes' until the given datetime."""
    if dt is None:
        return ""
    now = timezone.now()
    if now >= dt:
        return "closed"
    delta = dt - now
    total_seconds = int(delta.total_seconds())
    days = total_seconds // 86400
    remainder = total_seconds % 86400
    hours = remainder // 3600
    minutes = (remainder % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes or not parts:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return " ".join(parts)
