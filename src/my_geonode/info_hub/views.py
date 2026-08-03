# my_geonode/info_hub/views.py
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import AdvisoryMessage, Disease, WheatCluster
from .serializers import AdvisoryMessageSerializer, DiseaseSerializer, WheatClusterSerializer
from django.http import JsonResponse
import requests




# For PDF generation (Platypus imports added)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from io import BytesIO
import os # To check for file existence

# Shared PDF branding (matches the web app's green accent).
_PDF_GREEN = colors.HexColor('#2E6B2F')
_PDF_GREY = colors.HexColor('#666666')


def _pdf_letterhead(title_text):
    """A colored letterhead bar (Table, not plain text) so exports look
    like a branded document rather than a plain text dump."""
    cell = Paragraph(
        f'<font color="white"><b>{title_text}</b></font>',
        ParagraphStyle(name='Letterhead', fontSize=13, leading=16),
    )
    t = Table([[cell]], colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), _PDF_GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    return t


def _pdf_footer(canvas, doc):
    """Page number + a thin brand-colored rule, drawn on every page."""
    canvas.saveState()
    canvas.setStrokeColor(_PDF_GREEN)
    canvas.setLineWidth(1)
    canvas.line(0.75 * inch, 0.6 * inch, letter[0] - 0.75 * inch, 0.6 * inch)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(_PDF_GREY)
    canvas.drawString(0.75 * inch, 0.45 * inch, "Agro-Climate Advisory System")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _pdf_capped_image(img, max_width, max_height):
    """Scale an Image flowable to fit within both a max width AND max
    height, preserving aspect ratio (prevents a tall portrait photo from
    stretching across most of the page)."""
    ratio = img.drawHeight / float(img.drawWidth)
    width, height = max_width, max_width * ratio
    if height > max_height:
        height = max_height
        width = max_height / ratio
    img.drawWidth = width
    img.drawHeight = height
    return img

from django.core.mail import send_mail
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


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

    def get_queryset(self):
        """Optionally filter diseases to those linked to a wheat cluster
        (FR21: diseases common in the selected cluster's region).
        Usage: /api/info_hub/diseases/?cluster=<id>"""
        qs = super().get_queryset()
        cluster_id = self.request.query_params.get('cluster')
        if cluster_id:
            qs = qs.filter(clusters__id=cluster_id)
        return qs


class WheatClusterViewSet(viewsets.ReadOnlyModelViewSet):
    """Wheat clusters (FR12). `/clusters/` returns full records including
    linked diseases; `/clusters/geojson/` returns a GeoJSON FeatureCollection
    ready for direct rendering as a map vector layer."""
    queryset = WheatCluster.objects.all().prefetch_related('diseases')
    serializer_class = WheatClusterSerializer

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        features = []
        for cluster in self.get_queryset():
            if not cluster.geometry:
                continue
            props = {
                'feature_type': 'wheat_cluster',
                'cluster_id': cluster.id,
                'region': cluster.region,
                'diseases': [
                    {'id': d.id, 'name': d.name}
                    for d in cluster.diseases.all()
                ],
            }
            # Include base + per-language variants so the frontend's
            # pickTranslated() helper can resolve the active language.
            for field in ('name', 'description', 'suitability_trend'):
                props[field] = getattr(cluster, field, '') or ''
                for lang in ('en', 'am', 'om', 'ti'):
                    val = getattr(cluster, f'{field}_{lang}', None)
                    if val:
                        props[f'{field}_{lang}'] = val
            features.append({
                'type': 'Feature',
                'id': cluster.id,
                'geometry': cluster.geometry,
                'properties': props,
            })
        return Response({'type': 'FeatureCollection', 'features': features})


# UPDATED VIEW FUNCTION TO DOWNLOAD ADVISORY CONTENT AS PDF
@api_view(['GET'])
@permission_classes([AllowAny]) # <--- ADD THIS LINE
def download_advisory_pdf(request, advisory_id):
    """
    Generates and serves a PDF of the advisory content for a given AdvisoryMessage
    using ReportLab's Platypus framework for better formatting.
    """
    advisory = get_object_or_404(AdvisoryMessage, pk=advisory_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                             topMargin=0.6 * inch, bottomMargin=0.9 * inch,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    Story = [] # List to hold Platypus "flowables" (content elements)

    styles.add(ParagraphStyle(name='AdvisoryTitle',
                            parent=styles['h1'],
                            fontSize=18,
                            spaceBefore=16,
                            spaceAfter=10,
                            alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionTitle',
                            parent=styles['h2'],
                            fontSize=13,
                            textColor=_PDF_GREEN,
                            spaceBefore=14,
                            spaceAfter=6))

    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14 # Line spacing
    styles['BodyText'].spaceAfter = 8
    styles['BodyText'].alignment = TA_JUSTIFY

    styles.add(ParagraphStyle(name='KeyValue',
                            parent=styles['Normal'],
                            fontSize=10,
                            spaceAfter=4))

    # --- Branded letterhead ---
    Story.append(_pdf_letterhead("Agro-Climate Advisory System"))
    Story.append(Spacer(1, 0.25 * inch))

    # --- Advisory Title ---
    Story.append(Paragraph(f"{advisory.title}", styles['AdvisoryTitle']))

    # --- Featured Image directly after title (no label) ---
    if advisory.featured_image_file:
        loaded = False
        errors = []
        try:
            if hasattr(advisory.featured_image_file, 'path') and os.path.exists(advisory.featured_image_file.path):
                with open(advisory.featured_image_file.path, 'rb') as f:
                    image_data = BytesIO(f.read())
                img = Image(image_data)
                loaded = True
        except Exception as e:
            errors.append(f"fs:{e}")
        if not loaded:
            try:
                image_url = request.build_absolute_uri(advisory.featured_image_file.url)
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                image_data = BytesIO(response.content)
                img = Image(image_data)
                loaded = True
            except Exception as e:
                errors.append(f"http:{e}")
        if loaded:
            max_width = 4.5 * inch
            max_height = 3 * inch
            img = _pdf_capped_image(img, max_width, max_height)
            img.hAlign = 'CENTER'
            Story.append(img)
            Story.append(Spacer(1, 0.2 * inch))
        else:
            err_msg = '; '.join(errors) if errors else 'unknown'
            Story.append(Paragraph(f"<i>Could not load featured image: {err_msg}</i>", styles['BodyText']))
            Story.append(Spacer(1, 0.1 * inch))

    # --- Key Details (after image) ---
    Story.append(Paragraph(f"<b>Date Posted:</b> {advisory.published_date.strftime('%Y-%m-%d')}", styles['KeyValue']))
    Story.append(Paragraph(f"<b>Category:</b> {advisory.get_category_display()}", styles['KeyValue']))
    Story.append(Spacer(1, 0.15 * inch))
    Story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CCCCCC'),
                             spaceBefore=2, spaceAfter=10))

    # Each section is wrapped in KeepTogether(heading + first paragraph) so a
    # heading never gets stranded alone at the bottom of a page with its
    # content pushed to the next one.
    def add_section(title, body_text, fallback=None):
        if body_text:
            Story.append(KeepTogether([
                Paragraph(f"{title}", styles['SectionTitle']),
                Paragraph(body_text, styles['BodyText']),
            ]))
        elif fallback:
            Story.append(KeepTogether([
                Paragraph(f"{title}", styles['SectionTitle']),
                Paragraph(fallback, styles['BodyText']),
            ]))

    add_section("Advisory Content", advisory.advisory_content, "No specific advisory content provided.")
    add_section("Recommendation", advisory.suggestion, "No specific recommendation provided.")

    if advisory.rainfall_forecast or advisory.temperature_outlook:
        lines = []
        if advisory.rainfall_forecast:
            lines.append(f"<b>Rainfall Forecast:</b> {advisory.rainfall_forecast}")
        if advisory.temperature_outlook:
            lines.append(f"<b>Temperature Outlook:</b> {advisory.temperature_outlook}")
        add_section("Weather Outlook", "<br/><br/>".join(lines))

    add_section("Potential Risks", advisory.potential_risks)

    # --- Build the PDF ---
    try:
        doc.build(Story, onFirstPage=_pdf_footer, onLaterPages=_pdf_footer)
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


@api_view(['GET'])
@permission_classes([AllowAny])
def download_disease_pdf(request, disease_id):
    """Generates and serves a PDF of a Disease's information (FR25):
    name, image, description/symptoms, and recommended controls."""
    disease = get_object_or_404(Disease, pk=disease_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                             topMargin=0.6 * inch, bottomMargin=0.9 * inch,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='DiseaseTitle', parent=styles['h1'],
                              fontSize=18, spaceBefore=16, spaceAfter=10, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionTitle', parent=styles['h2'],
                              fontSize=13, textColor=_PDF_GREEN, spaceBefore=14, spaceAfter=6))
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceAfter = 8
    styles['BodyText'].alignment = TA_JUSTIFY

    story = [
        _pdf_letterhead("Agro-Climate Advisory System — Wheat Disease Information"),
        Spacer(1, 0.25 * inch),
        Paragraph(disease.name, styles['DiseaseTitle']),
    ]

    # Disease image (filesystem first, HTTP fallback — same approach as advisory)
    if disease.image:
        loaded = False
        try:
            if hasattr(disease.image, 'path') and os.path.exists(disease.image.path):
                with open(disease.image.path, 'rb') as f:
                    img = Image(BytesIO(f.read()))
                loaded = True
        except Exception:
            pass
        if not loaded:
            try:
                image_url = request.build_absolute_uri(disease.image.url)
                resp = requests.get(image_url, timeout=10)
                resp.raise_for_status()
                img = Image(BytesIO(resp.content))
                loaded = True
            except Exception:
                pass
        if loaded:
            img = _pdf_capped_image(img, 4.5 * inch, 3 * inch)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"<b>Affected Crops:</b> {disease.affected_crops}", styles['BodyText']))
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CCCCCC'),
                            spaceBefore=2, spaceAfter=10))

    # Each section is wrapped in KeepTogether(heading + body) so a heading
    # never gets stranded alone at the bottom of a page.
    sections = [
        ("Description", disease.description),
        ("Symptoms", disease.symptoms),
        ("Causes", disease.causes),
        ("Treatment Options", disease.treatment_options),
        ("Prevention Methods", disease.prevention_methods),
        ("Recommendation", disease.suggestion),
    ]
    for title, content in sections:
        if content:
            story.append(KeepTogether([
                Paragraph(f"{title}", styles['SectionTitle']),
                Paragraph(content, styles['BodyText']),
            ]))

    try:
        doc.build(story, onFirstPage=_pdf_footer, onLaterPages=_pdf_footer)
    except Exception as e:
        return HttpResponse(f"Error generating PDF: {e}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    pdf_data = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_data, content_type='application/pdf')
    filename_safe = disease.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    response['Content-Disposition'] = f'attachment; filename="disease_{disease.id}_{filename_safe}.pdf"'
    return response

