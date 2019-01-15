from django.contrib import admin
from django.db import models

# Register your models here.

from .models import (
    AssessmentPackage,
    AssessmentPurchase,
    Order,
    Subscription,
)


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    list_display = (
        'created',
        'order',
        'start_date',
        'end_date',
    )
    list_filter = ('order', 'start_date', 'end_date')


class AssessmentPurchaseAdmin(admin.ModelAdmin):
    model = AssessmentPurchase
    list_display = (
        'created',
        'order',
        'package',
        'number_included',
        'price'
    )
    list_filter = ('order', 'package')


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    formfield_overrides = {
        models.DateField: {'initial': None},
    }


class AssessmentPurchaseInline(admin.TabularInline):
    model = AssessmentPurchase
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'organisation',
        'status',
        'created',
    )
    inlines = [
        SubscriptionInline,
        AssessmentPurchaseInline,
    ]
    list_filter = ('organisation', 'status',)


class AssessmentPackageAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
        'number_included',
        'price',
    )
    list_filter = ('name', 'number_included', 'price',)


admin.site.register(AssessmentPackage, AssessmentPackageAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(AssessmentPurchase, AssessmentPurchaseAdmin)
