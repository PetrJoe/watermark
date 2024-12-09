from django.contrib import admin
from .models import WatermarkTemplate, WatermarkedFile, WatermarkSettings

@admin.register(WatermarkTemplate)
class WatermarkTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'user', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'user__username')

@admin.register(WatermarkedFile)
class WatermarkedFileAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_type', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('user__username',)

@admin.register(WatermarkSettings)
class WatermarkSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_opacity', 'default_rotation')
    search_fields = ('user__username',)
