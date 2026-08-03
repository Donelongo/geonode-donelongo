import logging

from django.db import migrations

logger = logging.getLogger(__name__)

# PATCHED: upstream GeoNode's original version of this migration does
# `from ..models import Document` and iterates `Document.objects.all()`.
# Because it imports the LIVE model class (not the historical one via
# apps.get_model), it picks up modeltranslation's title_am/om/ti fields,
# which are added to the schema by a LATER migration. On a fresh, empty
# database this migration runs before those columns exist and crashes with
# "column documents_document.title_am does not exist", aborting the entire
# migrate step. This only cleans up thumbnail_url for non-image documents
# (cosmetic), so it is safe to make this a no-op.


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0033_remove_document_doc_type'),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
