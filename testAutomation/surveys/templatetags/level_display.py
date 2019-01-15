from django import template
from django.utils.safestring import mark_safe

from users.models import get_invitation_status

from ..models import get_level_name

register = template.Library()


@register.filter
def level_display(value, css_class=''):
    value = 1 if not value else value
    return mark_safe(
        '''
            <span class="badge bg-level-{} {}">{}</span>
        '''.format(value, css_class, get_level_name(int(value)))
    )


@register.filter
def invite_status_display(value):
    return mark_safe(
        '''
            <td class="text-muted-md">{}</td>
        '''.format(get_invitation_status(int(value)))
    )
