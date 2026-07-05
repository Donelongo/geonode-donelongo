# my_geonode/info_hub/serializers.py
from rest_framework import serializers
from .models import AdvisoryMessage, Disease, WheatCluster

class AdvisoryMessageSerializer(serializers.ModelSerializer):
    featured_image_file = serializers.SerializerMethodField() # <--- For full image URL
    advisory_pdf = serializers.SerializerMethodField()
    cluster_name = serializers.CharField(source='cluster.name', read_only=True, default=None)

    class Meta:
        model = AdvisoryMessage
        fields = '__all__' # Simpler for now, or list specific fields

    def get_featured_image_file(self, obj):
        if obj.featured_image_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image_file.url)
            return obj.featured_image_file.url
        return None

    def get_advisory_pdf(self, obj):
        if obj.advisory_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.advisory_pdf.url)
            return obj.advisory_pdf.url
        return None

# If you have Disease API, uncomment/add this:
class DiseaseSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Disease
        fields = '__all__'

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class WheatClusterSerializer(serializers.ModelSerializer):
    """Wheat cluster with its linked diseases (FR12, FR21-23). All translated
    field variants (_en/_am/_om/_ti) are included via '__all__' so the frontend's
    pickTranslated() helper can select the active language."""
    diseases = DiseaseSerializer(many=True, read_only=True)

    class Meta:
        model = WheatCluster
        fields = '__all__'