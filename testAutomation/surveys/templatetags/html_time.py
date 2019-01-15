from django import template

register = template.Library()


@register.inclusion_tag('surveys/html_time.html')
def html_time(dt, format=None, format_title='DATETIME_FORMAT'):
    return {'datetime': dt, 'format': format, 'format_title': format_title}
