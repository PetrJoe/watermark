from rest_framework import serializers
from core.models import WatermarkTemplate, WatermarkedFile, WatermarkSettings

class WatermarkTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatermarkTemplate
        fields = ['id', 'name', 'type', 'text', 'image', 'created_at']
        read_only_fields = ['user']

class WatermarkedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatermarkedFile
        fields = ['id', 'original_file', 'watermarked_file', 'file_type', 
                 'watermark_template', 'position_x', 'position_y', 
                 'opacity', 'rotation', 'created_at']
        read_only_fields = ['user', 'watermarked_file']

class WatermarkSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatermarkSettings
        fields = ['default_opacity', 'default_position_x', 
                 'default_position_y', 'default_rotation']
