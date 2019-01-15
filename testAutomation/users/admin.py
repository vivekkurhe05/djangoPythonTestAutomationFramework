from copy import deepcopy

from countries.models import Country
from django.contrib import admin
from orderable.admin import OrderableAdmin
from user_management.models.admin import UserAdmin as BaseUserAdmin

from users.models import Invitation, Organisation, OrganisationType, User


class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + (
        'organisation',
        'last_login',
        'date_joined',
        'is_active',
    )

    list_filter = BaseUserAdmin.list_filter + (
        'organisation',
        'last_login',
        'date_joined',
    )
    fieldsets = deepcopy(BaseUserAdmin.fieldsets)
    fieldsets[1][1]['fields'] += (
        'organisation',
        'job_role',
        'user_mobile',
    )
    add_fieldsets = deepcopy(BaseUserAdmin.add_fieldsets)
    add_fieldsets[0][1]['fields'] = (
        'name',
        'organisation',
    ) + add_fieldsets[0][1]['fields']


class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        'grantor',
        'grantee',
        'survey',
        'accepted',
        'created',
    )
    list_filter = ('grantor', 'grantee', 'survey', 'accepted')


class OrganisationAdmin(admin.ModelAdmin):
    list_display = (
        'legal_name',
        'known_as',
        'parent_organisation',
        'phone_number',
        'last_updated',
    )
    list_filter = ('types', 'country')
    search_fields = (
        'legal_name',
        'known_as',
        'parent_organisation',
        'phone_number',
        'address_1',
        'address_2',
        'city',
        'province',
        'zip',
    )
    raw_id_fields = ('country',)
    filter_horizontal = ('types',)
    readonly_fields = ['last_updated']


class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = list_display


admin.site.register(User, UserAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(OrganisationType, OrderableAdmin)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(Country, CountryAdmin)
