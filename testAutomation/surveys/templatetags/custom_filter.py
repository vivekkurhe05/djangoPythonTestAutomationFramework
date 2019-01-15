import re

from django import template
from rolepermissions.roles import get_user_roles

from users.forms import AddUserForm

register = template.Library()


@register.filter
def format_email(string):
    return re.sub(r'\S*@', '****@', string)


@register.filter
def get_permission(user):
    try:
        role_name = get_user_roles(user)[0].get_name()
    except IndexError:
        pass
    else:
        try:
            return dict(AddUserForm.USER_TYPE_CHOICES)[role_name]
        except KeyError:
            pass

    return AddUserForm.USER_TYPE_CHOICES[-1][1]
