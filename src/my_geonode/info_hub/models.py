# my_geonode/info_hub/models.py

from django.db import models


class WheatCluster(models.Model):
    """A geographically defined area with a significant concentration of wheat
    farms (SRS 'Wheat Cluster', FR12). Geometry is stored as a GeoJSON geometry
    object (Polygon/MultiPolygon in EPSG:4326) so it can be served straight to
    the map without a GeoServer round-trip."""
    name = models.CharField(max_length=255, unique=True, help_text="Cluster name (e.g., 'Bale Wheat Cluster').")
    description = models.TextField(blank=True, help_text="General information about the cluster.")
    suitability_trend = models.TextField(
        blank=True,
        help_text="Narrative of the wheat land suitability trend for this cluster "
                  "(e.g., 'Highly suitable now; declines to moderately suitable by the 2050s under SSP5').",
    )
    region = models.CharField(max_length=255, blank=True, help_text="Administrative region (e.g., 'Oromia').")
    geometry = models.JSONField(
        blank=True, null=True,
        help_text="GeoJSON geometry (Polygon/MultiPolygon, WGS84 lon/lat) of the cluster boundary.",
    )
    diseases = models.ManyToManyField(
        'Disease', blank=True, related_name='clusters',
        help_text="Major wheat diseases common in this cluster.",
    )
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'info_hub'
        verbose_name = "Wheat Cluster"
        verbose_name_plural = "Wheat Clusters"
        ordering = ['name']


class AdvisoryMessage(models.Model):
    title = models.CharField(max_length=255, help_text="A short, descriptive title for the advisory.")
    # Change 'description' to 'advisory_content'
    advisory_content = models.TextField(help_text="A detailed description of the advisory. This will be the 'Advisory Content'.")
    suggestion = models.TextField(blank=True, null=True, help_text="Recommended actions or suggestions. This will be the 'Recommendation'.")

    published_date = models.DateField(auto_now_add=True)

    ADVISORY_CATEGORY_CHOICES = [
        ('Seasonal', 'Seasonal Advisory'),
        ('Monthly', 'Monthly Advisory'),
    ]
    category = models.CharField(
        max_length=20,
        choices=ADVISORY_CATEGORY_CHOICES,
        default='Monthly',
        help_text="Category of the advisory: Seasonal or Monthly."
    )
    rainfall_forecast = models.CharField(max_length=255, blank=True, null=True, help_text="Forecast regarding rainfall (e.g., 'Slightly above average').")
    temperature_outlook = models.CharField(max_length=255, blank=True, null=True, help_text="Outlook regarding temperature (e.g., 'Mild during germination').")
    potential_risks = models.TextField(blank=True, null=True, help_text="Potential risks associated with the advisory (e.g., 'Waterlogging in valley areas').")
    featured_image_file = models.FileField(
        upload_to='advisory_media/',
        blank=True,
        null=True,
        help_text="Optional featured image or file for the advisory."
    )
    advisory_pdf = models.FileField(
        upload_to='advisory_pdfs/',
        blank=True,
        null=True,
        help_text="Optional original advisory document (PDF) as provided by the source (FR20).",
    )
    cluster = models.ForeignKey(
        'WheatCluster',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='advisories',
        help_text="Wheat cluster this advisory targets (leave empty for a general advisory).",
    )

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        app_label = 'info_hub'
        verbose_name = "Advisory Message"
        verbose_name_plural = "Advisory Messages"
        ordering = ['-published_date']
        
class Disease(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Name of the disease (e.g., Stem Rust).")
    description = models.TextField(help_text="A general description of the disease.")
    suggestion = models.TextField(blank=True, null=True, help_text="Overall suggestion for dealing with the disease.")
    causes = models.TextField(blank=True, null=True, help_text="Causes of the disease.")
    treatment_options = models.TextField(blank=True, null=True, help_text="Available treatment options.")
    prevention_methods = models.TextField(blank=True, null=True, help_text="Methods for prevention.")
    symptoms = models.TextField(help_text="Common symptoms observed.")
    affected_crops = models.CharField(max_length=255, help_text="Comma-separated list of affected crops (e.g., 'Wheat, Barley, Rye').")
    image = models.ImageField(
        upload_to='disease_images/',
        blank=True,
        null=True,
        help_text="Image representing the disease."
    )
    
    def __str__(self):
        return self.name
    class Meta:
        app_label = 'info_hub'
        verbose_name = "Disease"
        verbose_name_plural = "Diseases"
        ordering = ['name']