from collections import OrderedDict

from django.core.urlresolvers import reverse


class Sidebar():

    def __init__(self):
        self.sidebar = OrderedDict()
        self.sidebar['main'] = OrderedDict()

        self.sidebar['main']['dashboard'] = {
            'name': 'Dashboard',
            'icon': 'dashboard',
            'link': reverse('home'),
            'roles': ['admin', 'manager', 'user']
        }
        self.sidebar['main']['assessments'] = {
            'name': 'Assessments',
            'icon': 'check-square-o',
            'link': reverse('view-assessment'),
            'roles': ['admin', 'manager', 'user']
        }
        self.sidebar['main']['document'] = {
            'name': 'Document library',
            'icon': 'folder-open-o',
            'link': reverse('document-home'),
            'roles': ['admin', 'manager', 'user']
        }
        self.sidebar['main']['invites'] = {
            'name': 'Invitations',
            'icon': 'plus-square',
            'link': reverse('survey-invite'),
            'roles': ['admin', 'manager']
        }
        self.sidebar['main']['directory'] = {
            'name': 'Directory',
            'icon': 'book',
            'link': reverse('directory'),
            'roles': ['admin', 'manager', 'user']
        }
        self.sidebar['main']['faq'] = {
            'name': 'Help & FAQ',
            'icon': 'question-circle',
            'link': reverse('faq'),
            'roles': ['admin', 'manager', 'user']
        }

        self.sidebar['settings'] = OrderedDict()

        self.sidebar['settings']['profile'] = {
            'name': 'My profile',
            'icon': 'user',
            'link': reverse('edit-profile'),
            'roles': ['admin', 'manager', 'user']
        }
        self.sidebar['settings']['users'] = {
            'name': 'Organization & users',
            'icon': 'users',
            'link': reverse('organization'),
            'roles': ['admin']
        }
        self.sidebar['settings']['subscription'] = {
            'name': 'Subscription & billing',
            'icon': 'dollar',
            'link': reverse('subscription'),
            'roles': ['admin']
        }
        self.sidebar['settings']['logout'] = {
            'name': 'Logout',
            'icon': 'power-off',
            'link': reverse('logout'),
            'roles': ['admin', 'manager', 'user']
        }

    def get(self):
        return self.sidebar

    def set_sidebar_item_active(self, section, item):
        self.sidebar[section][item]['class'] = 'active'
        return self.sidebar
