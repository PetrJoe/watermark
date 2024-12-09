from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Template URLs
    path('templates/', views.WatermarkTemplateList.as_view(), name='template-list'),
    path('templates/<int:pk>/', views.WatermarkTemplateDetail.as_view(), name='template-detail'),
    
    # File URLs
    path('files/', views.WatermarkedFileList.as_view(), name='file-list'),
    path('files/<int:pk>/', views.WatermarkedFileDetail.as_view(), name='file-detail'),
    path('files/quick-watermark/', views.QuickWatermarkView.as_view(), name='quick-watermark'),
    
    # Settings URLs
    path('settings/', views.WatermarkSettingsList.as_view(), name='settings-list'),
    path('settings/<int:pk>/', views.WatermarkSettingsDetail.as_view(), name='settings-detail'),
]
