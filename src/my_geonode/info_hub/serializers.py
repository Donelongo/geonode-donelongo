# agro_advisory_system/info_hub/serializers.py
from rest_framework import serializers
from .models import AdvisoryMessage, Disease # Make sure Disease is imported

class AdvisoryMessageSerializer(serializers.ModelSerializer):
    featured_image_file = serializers.SerializerMethodField() # <--- For full image URL

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