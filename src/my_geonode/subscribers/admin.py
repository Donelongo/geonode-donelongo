# subscribers/admin.py
from django.contrib import admin
from .models import Subscriber

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'subscribed_at', 'is_active')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-subscribed_at',)