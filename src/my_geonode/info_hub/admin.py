from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import AdvisoryMessage, Disease, WheatCluster


# TranslationAdmin expands each registered field into its per-language
# variants (en/am/om/ti) in the form, so admins can enter translations.

@admin.register(AdvisoryMessage)
class AdvisoryMessageAdmin(TranslationAdmin):
    list_display = ('title', 'category', 'cluster', 'published_date', 'last_updated')
    search_fields = ('title', 'advisory_content', 'potential_risks')
    list_filter = ('category', 'cluster', 'published_date',)

    fieldsets = (
        (None, {  # General information
            'fields': ('title', 'category', 'cluster', 'featured_image_file', 'advisory_pdf', 'published_date')
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
class DiseaseAdmin(TranslationAdmin):
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


@admin.register(WheatCluster)
class WheatClusterAdmin(TranslationAdmin):
    list_display = ('name', 'region', 'last_updated')
    search_fields = ('name', 'region', 'description')
    filter_horizontal = ('diseases',)

    fieldsets = (
        (None, {
            'fields': ('name', 'region')
        }),
        ('Details', {
            'fields': ('description', 'suitability_trend', 'diseases')
        }),
        ('Boundary', {
            'fields': ('geometry',),
            'description': 'Paste a GeoJSON geometry object (Polygon or MultiPolygon, '
                           'WGS84 lon/lat), e.g. {"type": "Polygon", "coordinates": [[[39.5, 7.0], ...]]}',
        }),
    )


# Optional: Customize admin branding
admin.site.site_header = "Agro Advisory Admin"
admin.site.site_title = "Agro Advisory System"
admin.site.index_title = "Welcome to the Advisory Admin"
