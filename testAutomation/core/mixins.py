import math

from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from rolepermissions.roles import get_user_roles

from .utils import Sidebar


class AppMixin:
    sidebar_section = 'main'
    sidebar_item = None
    page_title = None

    def get_sidebar(self, user):
        if self.sidebar_section is None:
            raise ImproperlyConfigured(
                "You must specify 'sidebar_section' or override 'get_sidebar'."
            )
        if self.sidebar_item is None:
            raise ImproperlyConfigured(
                "You must specify 'sidebar_item' or override 'get_sidebar'."
            )

        filtered_sidebar = OrderedDict()

        if user.is_anonymous:
            return filtered_sidebar

        sidebar = Sidebar().set_sidebar_item_active(
            self.sidebar_section,
            self.sidebar_item
        )

        user_roles = set([role.get_name() for role in get_user_roles(user)])

        for type in sidebar:
            filtered_sidebar[type] = OrderedDict()
            for item in sidebar[type]:
                roles = set(sidebar[type][item]['roles'])
                if(user_roles & roles):
                    filtered_sidebar[type][item] = sidebar[type][item]

        return filtered_sidebar

    def get_page_title(self):
        if self.page_title is None:
            raise ImproperlyConfigured(
                "You must specify 'page_title' or override 'get_page_title'."
            )
        return self.page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sidebar = self.get_sidebar(self.request.user)
        context.update({
            'page_title': self.get_page_title(),
            'sidebar_main': sidebar['main'],
            'sidebar_settings': sidebar['settings'],
        })

        return context


class AjaxMixin:
    """Raise Http404 for non ajax get requests"""
    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404('GET method not allowed unless using AJAX')

        return super().get(request, *args, **kwargs)


class PaginationMixin:
    page_limit = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        limit = self.page_limit

        left = (limit / 2) + 1
        right = limit / 2
        page_range = context['paginator'].page_range
        total = len(page_range)
        current = int(context['page_obj'].number)

        if limit % 2 == 0:
            right -= 1

        if current < left:
            page_range = page_range[:limit]
        elif current > total - right:
            page_range = page_range[total-limit:]
        else:
            page_range = page_range[math.ceil(current-left):int(current+right)]

        context.update({
            'page_range': page_range,
        })

        return context
