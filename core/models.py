from django.db import models
from django.contrib.auth.models import User

class WatermarkTemplate(models.Model):
    WATERMARK_TYPE_CHOICES = [
        ('TEXT', 'Text Watermark'),
        ('IMAGE', 'Image Watermark')
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=5, choices=WATERMARK_TYPE_CHOICES)
    text = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='watermark_templates/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class WatermarkedFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('PDF', 'PDF Document'),
        ('IMAGE', 'Image File')
    ]
    
    original_file = models.FileField(upload_to='original_files/')
    watermarked_file = models.FileField(upload_to='watermarked_files/')
    file_type = models.CharField(max_length=5, choices=FILE_TYPE_CHOICES)
    watermark_template = models.ForeignKey(WatermarkTemplate, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Watermark position settings
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    opacity = models.FloatField(default=0.5)
    rotation = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s {self.file_type} - {self.created_at}"

class WatermarkSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    default_opacity = models.FloatField(default=0.5)
    default_position_x = models.IntegerField(default=0)
    default_position_y = models.IntegerField(default=0)
    default_rotation = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s settings"
