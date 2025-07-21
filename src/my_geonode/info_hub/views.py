# agro_advisory_system/info_hub/views.py
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import AdvisoryMessage, Disease
from .serializers import AdvisoryMessageSerializer, DiseaseSerializer

# For PDF generation (Platypus imports added)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from io import BytesIO
import os # To check for file existence

class AdvisoryMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdvisoryMessage.objects.all().order_by('-last_updated')
    serializer_class = AdvisoryMessageSerializer

    @action(detail=False, methods=['get'])
    def recent_by_category(self, request):
        category = request.query_params.get('category')
        if not category:
            return Response({"detail": "Category parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            recent_advisory = self.get_queryset().filter(category=category).first()
            if recent_advisory:
                serializer = self.get_serializer(recent_advisory)
                return Response(serializer.data)
            else:
                return Response({"detail": f"No recent advisory found for category '{category}'."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DiseaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Disease.objects.all().order_by('name')
    serializer_class = DiseaseSerializer

# UPDATED VIEW FUNCTION TO DOWNLOAD ADVISORY CONTENT AS PDF
@api_view(['GET'])
def download_advisory_pdf(request, advisory_id):
    """
    Generates and serves a PDF of the advisory content for a given AdvisoryMessage
    using ReportLab's Platypus framework for better formatting.
    """
    advisory = get_object_or_404(AdvisoryMessage, pk=advisory_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = [] # List to hold Platypus "flowables" (content elements)

    # Define custom styles if needed (e.g., for spacing below titles)
    # Get the sample stylesheet
    styles = getSampleStyleSheet() # This line should remain as is

    # Define custom styles (use styles.add for NEW names, modify directly for EXISTING ones)
    styles.add(ParagraphStyle(name='AdvisoryTitle',
                              parent=styles['h1'],
                              fontSize=18,
                              spaceAfter=14,
                              alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionTitle',
                              parent=styles['h2'],
                              fontSize=14,
                              spaceBefore=12,
                              spaceAfter=6))

    # --- FIX HERE: Modify the existing 'BodyText' style directly ---
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 12 # Line spacing
    styles['BodyText'].spaceAfter = 8
    styles['BodyText'].alignment = TA_JUSTIFY
    # No need to set parent again, as it's already based on 'Normal' by default for 'BodyText'.
    # If you wanted a completely new style for body text, you'd use a different 'name' like 'MyCustomBodyText'.

    styles.add(ParagraphStyle(name='KeyValue',
                              parent=styles['Normal'],
                              fontSize=10,
                              spaceAfter=4))


    # --- Document Header ---
    Story.append(Paragraph(f"Agro-Climate Advisory System", styles['h1']))
    Story.append(Spacer(1, 0.2 * inch))

    # --- Advisory Title ---
    Story.append(Paragraph(f"{advisory.title}", styles['AdvisoryTitle']))
    Story.append(Spacer(1, 0.1 * inch))

    # --- Key Details ---
    Story.append(Paragraph(f"<b>Date Posted:</b> {advisory.published_date.strftime('%Y-%m-%d')}", styles['KeyValue']))
    Story.append(Paragraph(f"<b>Category:</b> {advisory.get_category_display()}", styles['KeyValue']))
    Story.append(Spacer(1, 0.2 * inch))


    # --- Advisory Content ---
    Story.append(Paragraph("Advisory Content:", styles['SectionTitle']))
    if advisory.advisory_content:
        Story.append(Paragraph(advisory.advisory_content, styles['BodyText']))
    else:
        Story.append(Paragraph("No specific advisory content provided.", styles['BodyText']))
    Story.append(Spacer(1, 0.2 * inch))

    # --- Recommendation/Suggestion ---
    Story.append(Paragraph("Recommendation:", styles['SectionTitle']))
    if advisory.suggestion:
        Story.append(Paragraph(advisory.suggestion, styles['BodyText']))
    else:
        Story.append(Paragraph("No specific recommendation provided.", styles['BodyText']))
    Story.append(Spacer(1, 0.2 * inch))

    # --- Weather Outlook ---
    if advisory.rainfall_forecast or advisory.temperature_outlook:
        Story.append(Paragraph("Weather Outlook:", styles['SectionTitle']))
        if advisory.rainfall_forecast:
            Story.append(Paragraph(f"<b>Rainfall Forecast:</b> {advisory.rainfall_forecast}", styles['BodyText']))
        if advisory.temperature_outlook:
            Story.append(Paragraph(f"<b>Temperature Outlook:</b> {advisory.temperature_outlook}", styles['BodyText']))
        Story.append(Spacer(1, 0.2 * inch))

    # --- Potential Risks ---
    if advisory.potential_risks:
        Story.append(Paragraph("Potential Risks:", styles['SectionTitle']))
        Story.append(Paragraph(advisory.potential_risks, styles['BodyText']))
        Story.append(Spacer(1, 0.2 * inch))

    # --- Featured Image ---
    if advisory.featured_image_file and os.path.exists(advisory.featured_image_file.path):
        try:
            # Create an Image flowable
            # You might need to adjust width/height or use a ratio for proper scaling
            # Let's target a width and scale proportionally
            img = Image(advisory.featured_image_file.path)
            img_width = 4 * inch # Example width
            img_height = img.drawHeight * (img_width / img.drawWidth) # Maintain aspect ratio

            # Ensure image fits within page width
            if img_width > (letter[0] - 2 * inch): # letter[0] is width of page, 2*inch is for margins (1 inch on each side)
                img_width = letter[0] - 2 * inch
                img_height = img.drawHeight * (img_width / img.drawWidth)

            img.drawWidth = img_width
            img.drawHeight = img_height

            Story.append(Paragraph("Featured Image:", styles['SectionTitle']))
            Story.append(Spacer(1, 0.1 * inch))
            Story.append(img)
            Story.append(Spacer(1, 0.2 * inch))
        except Exception as e:
            # Handle cases where image might be corrupt or not readable by ReportLab
            Story.append(Paragraph(f"<i>Could not load featured image: {e}</i>", styles['BodyText']))
            print(f"Error loading image for PDF: {e}")


    # --- Build the PDF ---
    try:
        doc.build(Story)
    except Exception as e:
        print(f"Error building PDF: {e}")
        return HttpResponse(f"Error generating PDF: {e}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Get the value of the BytesIO buffer and set it as the response content.
    pdf_data = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_data, content_type='application/pdf')
    # Sanitize filename by replacing spaces with underscores
    filename_safe = advisory.title.replace(" ", "_").replace("/", "_").replace("\\", "_")
    response['Content-Disposition'] = f'attachment; filename="advisory_{advisory.id}_{filename_safe}.pdf"'

    return response