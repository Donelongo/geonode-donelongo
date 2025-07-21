# agro_advisory_system/info_hub/admin.py

from django.contrib import admin
from .models import AdvisoryMessage, Disease # Import your models

@admin.register(AdvisoryMessage)
class AdvisoryMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'published_date', 'last_updated')
    search_fields = ('title', 'description', 'potential_risks')
    list_filter = ('category', 'published_date',)

    # Organize fields in the admin add/change form to match your advisory structure
    fieldsets = (
        (None, { # General information
            'fields': ('title', 'category', 'featured_image_file', 'published_date')
        }),
        ('Advisory Details', { # This maps to "Advisory Content"
            'fields': ('advisory_content',)
        }),
        ('Forecast & Outlook', {
            'fields': ('rainfall_forecast', 'temperature_outlook')
        }),
        ('Risks & Recommendations', {
            'fields': ('potential_risks', 'suggestion') # suggestion maps to Recommendation
        }),
        ('System Information', { # For auto-generated dates
            'fields': ('last_updated',),
            'classes': ('collapse',), # Makes this section collapsible
        }),
    )

    # Make published_date and last_updated read-only as they are auto-populated
    readonly_fields = ('published_date', 'last_updated')

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'affected_crops')
    search_fields = ('name', 'symptoms', 'affected_crops')
    # Define fields for the Disease model form
    fieldsets = (
        (None, {
            'fields': ('name', 'affected_crops', 'image')
        }),
        ('Details', {
            'fields': ('description', 'symptoms', 'causes', 'treatment_options', 'prevention_methods')
        }),
    )