# my_geonde/em/info_hub/admin.py

from django.contrib import admin
from .models import AdvisoryMessage, Disease  # Import your models

@admin.register(AdvisoryMessage)
class AdvisoryMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'published_date', 'last_updated')
    search_fields = ('title', 'advisory_content', 'potential_risks')  # Fixed 'description' to 'advisory_content'
    list_filter = ('category', 'published_date',)

    fieldsets = (
        (None, {  # General information
            'fields': ('title', 'category', 'featured_image_file', 'published_date')
        }),
        ('Advisory Details', {  # This maps to "Advisory Content"
            'fields': ('advisory_content',)
        }),
        ('Forecast & Outlook', {
            'fields': ('rainfall_forecast', 'temperature_outlook')
        }),
        ('Risks & Recommendations', {
            'fields': ('potential_risks', 'suggestion')  # 'suggestion' maps to Recommendation
        }),
        ('System Information', {  # For auto-generated dates
            'fields': ('last_updated',),
            'classes': ('collapse',),  # Makes this section collapsible
        }),
    )

    readonly_fields = ('published_date', 'last_updated')


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'affected_crops')
    search_fields = ('name', 'symptoms', 'affected_crops')

    fieldsets = (
        (None, {
            'fields': ('name', 'affected_crops', 'image')
        }),
        ('Details', {
            'fields': (
                'description',
                'symptoms',
                'causes',
                'treatment_options',
                'prevention_methods'
            )
        }),
    )


# Optional: Customize admin branding
admin.site.site_header = "Agro Advisory Admin"
admin.site.site_title = "Agro Advisory System"
admin.site.index_title = "Welcome to the Advisory Admin"
