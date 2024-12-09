from django import forms
from .models import WatermarkTemplate, WatermarkedFile, WatermarkSettings

class WatermarkTemplateForm(forms.ModelForm):
    class Meta:
        model = WatermarkTemplate
        fields = ['name', 'type', 'text', 'image']
        widgets = {
            'type': forms.RadioSelect(),
        }

    def clean(self):
        cleaned_data = super().clean()
        watermark_type = cleaned_data.get('type')
        text = cleaned_data.get('text')
        image = cleaned_data.get('image')

        if watermark_type == 'TEXT' and not text:
            raise forms.ValidationError("Text is required for text watermark")
        if watermark_type == 'IMAGE' and not image:
            raise forms.ValidationError("Image is required for image watermark")
        return cleaned_data

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = WatermarkedFile
        fields = [
            'original_file',
            'file_type',
            'watermark_template',
            # 'position_x',
            # 'position_y',
            'opacity', 
            # 'rotation'
        ]
        # widgets = {
        #     'opacity': forms.NumberInput(attrs={'type': 'range', 'min': '0', 'max': '1', 'step': '0.1'}),
        #     'rotation': forms.NumberInput(attrs={'type': 'range', 'min': '0', 'max': '360', 'step': '1'}),
        # }

class WatermarkSettingsForm(forms.ModelForm):
    class Meta:
        model = WatermarkSettings
        fields = [
            'default_position_x', 
            'default_position_y',
            # 'default_opacity',
            # 'default_rotation'
        ]
        # widgets = {
        #     'default_opacity': forms.NumberInput(attrs={'type': 'range', 'min': '0', 'max': '1', 'step': '0.1'}),
        #     'default_rotation': forms.NumberInput(attrs={'type': 'range', 'min': '0', 'max': '360', 'step': '1'}),
        # }

class QuickWatermarkForm(forms.Form):
    file = forms.FileField()
    watermark_text = forms.CharField(required=False)
    watermark_image = forms.ImageField(required=False)
    position_x = forms.IntegerField(initial=0)
    position_y = forms.IntegerField(initial=0)
    opacity = forms.FloatField(
        initial=0.5,
        widget=forms.NumberInput(attrs={'type': 'range', 'min': '0', 'max': '1', 'step': '0.1'})
    )
    # rotation = forms.IntegerField(
    #     initial=0,
    #     widget=forms.NumberInput(attrs={'type': 'range', 'min': '0', 'max': '360', 'step': '1'})
    # )

    def clean(self):
        cleaned_data = super().clean()
        watermark_text = cleaned_data.get('watermark_text')
        watermark_image = cleaned_data.get('watermark_image')
        
        if not watermark_text and not watermark_image:
            raise forms.ValidationError("Either watermark text or image must be provided")
        if watermark_text and watermark_image:
            raise forms.ValidationError("Please provide either text or image watermark, not both")
        return cleaned_data
