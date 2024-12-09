from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from PIL import Image
import PyPDF2
import io
from PIL import Image, ImageDraw, ImageFont
from core.models import WatermarkTemplate, WatermarkedFile, WatermarkSettings
from .serializers import (WatermarkTemplateSerializer, WatermarkedFileSerializer, 
                         WatermarkSettingsSerializer)



class WatermarkTemplateList(generics.ListCreateAPIView):
    serializer_class = WatermarkTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return WatermarkTemplate.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WatermarkTemplateDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WatermarkTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return WatermarkTemplate.objects.filter(user=self.request.user)

class WatermarkedFileList(generics.ListCreateAPIView):
    serializer_class = WatermarkedFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return WatermarkedFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        if instance.file_type == 'PDF':
            # Process PDF watermark
            pdf_reader = PyPDF2.PdfReader(instance.file)
            pdf_writer = PyPDF2.PdfWriter()
            
            for page in pdf_reader.pages:
                page.merge_page(instance.watermark_template.template)
                pdf_writer.add_page(page)
            
            output = io.BytesIO()
            pdf_writer.write(output)
            instance.watermarked_file.save(f'watermarked_{instance.file.name}', output)
        else:
            # Process image watermark
            with Image.open(instance.file) as img:
                watermark = Image.open(instance.watermark_template.template)
                
                # Resize watermark to fit the image
                watermark = watermark.resize((img.width // 2, img.height // 2))
                
                # Calculate position to place watermark
                position = ((img.width - watermark.width) // 2,
                          (img.height - watermark.height) // 2)
                
                # Create a new image with transparency
                transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
                transparent.paste(img, (0, 0))
                transparent.paste(watermark, position, mask=watermark)
                
                # Save the watermarked image
                output = io.BytesIO()
                transparent.save(output, format='PNG')
                instance.watermarked_file.save(f'watermarked_{instance.file.name}', output)

class WatermarkedFileDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WatermarkedFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return WatermarkedFile.objects.filter(user=self.request.user)

class QuickWatermarkView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        file = request.FILES.get('file')
        watermark_text = request.data.get('watermark_text')
        watermark_image = request.FILES.get('watermark_image')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a watermarked file instance
        watermarked_file = WatermarkedFile(
            user=request.user,
            original_file=file,
            file_type='PDF' if file.name.lower().endswith('.pdf') else 'IMAGE'
        )
        
        if watermark_text:
            # Create text watermark
            img = Image.new('RGBA', (500, 100), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial.ttf", 36)
            draw.text((10, 10), watermark_text, font=font, fill=(0, 0, 0, 128))
            
            # Save temporary watermark
            temp_watermark = io.BytesIO()
            img.save(temp_watermark, format='PNG')
            watermark = temp_watermark.getvalue()
        elif watermark_image:
            watermark = watermark_image.read()
        else:
            return Response({'error': 'No watermark provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if watermarked_file.file_type == 'PDF':
            # Process PDF watermark
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_writer = PyPDF2.PdfWriter()
            
            watermark_pdf = PyPDF2.PdfReader(io.BytesIO(watermark))
            watermark_page = watermark_pdf.pages[0]
            
            for page in pdf_reader.pages:
                page.merge_page(watermark_page)
                pdf_writer.add_page(page)
            
            output = io.BytesIO()
            pdf_writer.write(output)
            watermarked_file.watermarked_file.save(f'quick_watermarked_{file.name}', 
                                                 output)
        else:
            # Process image watermark
            with Image.open(file) as img:
                watermark = Image.open(io.BytesIO(watermark))
                
                # Resize watermark
                watermark = watermark.resize((img.width // 2, img.height // 2))
                position = ((img.width - watermark.width) // 2,
                          (img.height - watermark.height) // 2)
                
                transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
                transparent.paste(img, (0, 0))
                transparent.paste(watermark, position, mask=watermark)
                
                output = io.BytesIO()
                transparent.save(output, format='PNG')
                watermarked_file.watermarked_file.save(
                    f'quick_watermarked_{file.name}', output)
        
        watermarked_file.save()
        return Response({
            'status': 'success',
            'watermarked_file_url': watermarked_file.watermarked_file.url
        }, status=status.HTTP_200_OK)

class WatermarkSettingsList(generics.ListCreateAPIView):
    serializer_class = WatermarkSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WatermarkSettings.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WatermarkSettingsDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WatermarkSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WatermarkSettings.objects.filter(user=self.request.user)
