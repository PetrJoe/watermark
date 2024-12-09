from django.urls import path
from . import views

urlpatterns = [
    # Template Management
    path('', views.WatermarkTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.WatermarkTemplateCreateView.as_view(), name='template_create'),
    
    # File Watermarking
    path('watermark/', views.watermark_file, name='watermark_file'),
    path('quick-watermark/', views.quick_watermark, name='quick_watermark'),
    
    # Watermarked Files
    path('files/', views.WatermarkedFileListView.as_view(), name='file_list'),

    path('watermarked-file/<int:pk>/', views.watermarked_file_detail, name='watermarked_file_detail'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
