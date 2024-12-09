from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
import PyPDF2
from PIL import Image, ImageDraw, ImageFont
import io
from .models import WatermarkTemplate, WatermarkedFile, WatermarkSettings
from .forms import WatermarkTemplateForm, FileUploadForm, WatermarkSettingsForm, QuickWatermarkForm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.core.files.base import ContentFile
import os

def get_default_font():
    system_fonts = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        'C:\\Windows\\Fonts\\arial.ttf'
    ]
    
    for font_path in system_fonts:
        if os.path.exists(font_path):
            return font_path
    
    return ImageFont.load_default()


class WatermarkTemplateListView(LoginRequiredMixin, ListView):
    model = WatermarkTemplate
    template_name = 'template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return WatermarkTemplate.objects.filter(user=self.request.user)

class WatermarkTemplateCreateView(LoginRequiredMixin, CreateView):
    model = WatermarkTemplate
    form_class = WatermarkTemplateForm
    template_name = 'template_form.html'
    success_url = reverse_lazy('template_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

@login_required
def watermark_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            watermarked_file = form.save(commit=False)
            watermarked_file.user = request.user
            
            # Process the file based on type
            if watermarked_file.file_type == 'PDF':
                processed_file = process_pdf_watermark(
                    watermarked_file.original_file,
                    watermarked_file.watermark_template,
                    watermarked_file.position_x,
                    watermarked_file.position_y,
                    watermarked_file.opacity,
                    watermarked_file.rotation
                )
            else:
                processed_file = process_image_watermark(
                    watermarked_file.original_file,
                    watermarked_file.watermark_template,
                    watermarked_file.position_x,
                    watermarked_file.position_y,
                    watermarked_file.opacity,
                    watermarked_file.rotation
                )
            
            watermarked_file.watermarked_file = processed_file
            watermarked_file.save()
            return redirect('watermarked_file_detail', pk=watermarked_file.pk)
    else:
        form = FileUploadForm()
    return render(request, 'watermark_form.html', {'form': form})

@login_required
def quick_watermark(request):
    if request.method == 'POST':
        form = QuickWatermarkForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            watermark_text = form.cleaned_data['watermark_text']
            watermark_image = form.cleaned_data['watermark_image']
            original_filename = file.name
            
            # Determine file type
            if original_filename.lower().endswith('.pdf'):
                processed_file = process_pdf_watermark_quick(
                    file, watermark_text, watermark_image,
                    form.cleaned_data['position_x'],
                    form.cleaned_data['position_y'],
                    form.cleaned_data['opacity'],
                    form.cleaned_data['rotation']
                )
            else:
                processed_file = process_image_watermark_quick(
                    file, watermark_text, watermark_image,
                    form.cleaned_data['position_x'],
                    form.cleaned_data['position_y'],
                    form.cleaned_data['opacity'],
                    form.cleaned_data['rotation']
                )
            
            response = HttpResponse(processed_file, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="watermarked_{original_filename}"'
            return response
    else:
        form = QuickWatermarkForm()
    return render(request, 'quick_watermark.html', {'form': form})

@login_required
def settings_view(request):
    settings, created = WatermarkSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = WatermarkSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('settings')
    else:
        form = WatermarkSettingsForm(instance=settings)
    
    return render(request, 'settings.html', {'form': form})

class WatermarkedFileListView(LoginRequiredMixin, ListView):
    model = WatermarkedFile
    template_name = 'watermarked_file_list.html'
    context_object_name = 'files'

    def get_queryset(self):
        return WatermarkedFile.objects.filter(user=self.request.user)


def process_image_watermark(original_file, watermark_template, pos_x, pos_y, opacity, rotation):
    with Image.open(original_file) as img:
        if watermark_template.type == 'TEXT':
            txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            font = ImageFont.truetype(get_default_font(), 36) if isinstance(get_default_font(), str) else get_default_font()
            
            # Create diagonal watermarks
            text = watermark_template.text
            diagonal_spacing = int(min(img.width, img.height) / 4)
            
            # Top-left to bottom-right
            for i in range(-img.height, img.width, diagonal_spacing):
                draw.text((i, 0), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
            
            # Bottom-left to top-right
            for i in range(-img.height, img.width, diagonal_spacing):
                draw.text((i, img.height), text, font=font, fill=(255, 255, 255, int(255 * opacity)), angle=45)
            
            img = Image.alpha_composite(img.convert('RGBA'), txt_layer)
        else:
            with Image.open(watermark_template.image) as watermark:
                watermark = watermark.convert('RGBA')
                # Make watermark smaller for scattering
                watermark = watermark.resize((int(img.width * 0.2), int(img.height * 0.2)))
                
                # Create scattered pattern
                temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
                watermark.putalpha(int(255 * opacity))
                
                # Scatter watermarks in a grid pattern
                grid_size = 4
                for x in range(grid_size):
                    for y in range(grid_size):
                        pos_x = int((img.width / grid_size) * x)
                        pos_y = int((img.height / grid_size) * y)
                        # Add some randomness to positions
                        offset_x = int(img.width * 0.05 * (x % 2))
                        offset_y = int(img.height * 0.05 * (y % 2))
                        temp.paste(watermark, (pos_x + offset_x, pos_y + offset_y))
                
                img = Image.alpha_composite(img.convert('RGBA'), temp)
        
        output = io.BytesIO()
        img.save(output, format='PNG')
        return ContentFile(output.getvalue(), name='watermarked.png')

def process_pdf_watermark(original_file, watermark_template, pos_x, pos_y, opacity, rotation):
    watermark_layer = io.BytesIO()
    pdf_reader = PyPDF2.PdfReader(original_file)
    pdf_writer = PyPDF2.PdfWriter()
    
    for page in pdf_reader.pages:
        watermark_layer = io.BytesIO()
        c = canvas.Canvas(watermark_layer)
        
        if watermark_template.type == 'TEXT':
            c.setFillAlpha(opacity)
            text = watermark_template.text
            
            # Create diagonal pattern
            page_width = page.mediabox.width
            page_height = page.mediabox.height
            diagonal_spacing = min(page_width, page_height) / 4
            
            # Draw diagonal text patterns
            for i in range(0, int(page_width + page_height), int(diagonal_spacing)):
                c.saveState()
                c.translate(i, 0)
                c.rotate(45)
                c.drawString(0, 0, text)
                c.restoreState()
                
                c.saveState()
                c.translate(i, page_height)
                c.rotate(-45)
                c.drawString(0, 0, text)
                c.restoreState()
                
        else:
            with watermark_template.image.open() as img_file:
                img = ImageReader(img_file)
                c.setFillAlpha(opacity)
                
                # Create scattered pattern
                grid_size = 4
                img_width = 50
                img_height = 50
                
                for x in range(grid_size):
                    for y in range(grid_size):
                        pos_x = (page.mediabox.width / grid_size) * x
                        pos_y = (page.mediabox.height / grid_size) * y
                        c.drawImage(img, pos_x, pos_y, width=img_width, height=img_height, mask='auto')
        
        c.save()
        watermark_pdf = PyPDF2.PdfReader(watermark_layer)
        page.merge_page(watermark_pdf.pages[0])
        pdf_writer.add_page(page)

    output = io.BytesIO()
    pdf_writer.write(output)
    return ContentFile(output.getvalue(), name='watermarked.pdf')



def process_image_watermark_quick(file, text, image, pos_x, pos_y, opacity, rotation):
    with Image.open(file) as img:
        if text:
            txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            font = ImageFont.truetype(get_default_font(), 36) if isinstance(get_default_font(), str) else get_default_font()
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = int(pos_x * (img.width - text_width))
            y = int(pos_y * (img.height - text_height))
            
            draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
            txt_layer = txt_layer.rotate(rotation, expand=True)
            img = Image.alpha_composite(img.convert('RGBA'), txt_layer)
        elif image:
            with Image.open(image) as watermark:
                watermark = watermark.convert('RGBA')
                watermark = watermark.resize((int(img.width * 0.5), int(img.height * 0.5)))
                
                x = int(pos_x * (img.width - watermark.width))
                y = int(pos_y * (img.height - watermark.height))
                
                watermark.putalpha(int(255 * opacity))
                watermark = watermark.rotate(rotation, expand=True)
                
                temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
                temp.paste(watermark, (x, y))
                img = Image.alpha_composite(img.convert('RGBA'), temp)
        
        output = io.BytesIO()
        img.save(output, format='PNG')
        return ContentFile(output.getvalue(), name=f'watermarked_{file.name}')


def process_pdf_watermark_quick(file, text, image, pos_x, pos_y, opacity, rotation):
    pdf_reader = PyPDF2.PdfReader(file)
    pdf_writer = PyPDF2.PdfWriter()
    
    for page in pdf_reader.pages:
        watermark_layer = io.BytesIO()
        
        # Create watermark layer
        c = canvas.Canvas(watermark_layer)
        if text:
            c.setFillAlpha(opacity)
            c.translate(pos_x * page.mediabox.width, pos_y * page.mediabox.height)
            c.rotate(rotation)
            c.drawString(0, 0, text)
        elif image:
            img = ImageReader(image)
            c.setFillAlpha(opacity)
            c.translate(pos_x * page.mediabox.width, pos_y * page.mediabox.height)
            c.rotate(rotation)
            c.drawImage(img, 0, 0, width=100, height=100, mask='auto')
        
        c.save()
        
        # Merge watermark with page
        watermark_pdf = PyPDF2.PdfReader(watermark_layer)
        page.merge_page(watermark_pdf.pages[0])
        pdf_writer.add_page(page)
    
    # output = io.BytesIO()
    # pdf_writer.write(output)
    # return output.getvalue()

    output = io.BytesIO()
    pdf_writer.write(output)
    return ContentFile(output.getvalue(), name=f'watermarked_{file.name}')


@login_required
def watermarked_file_detail(request, pk):
    watermarked_file = get_object_or_404(WatermarkedFile, pk=pk, user=request.user)
    return render(request, 'watermarked_file_detail.html', {'file': watermarked_file})





