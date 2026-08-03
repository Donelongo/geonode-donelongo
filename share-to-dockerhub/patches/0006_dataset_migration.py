from django.db import migrations

# PATCHED: upstream's version does `from geonode.layers.models import Dataset`
# and iterates Dataset.objects.exclude(...) using the LIVE model, which picks
# up modeltranslation's title_am/om/ti columns added by a later migration.
# On a fresh, empty database (no legacy datasets to backfill - that is this
# migration's whole purpose) this crashes migrate with
# "column layers_dataset.title_am does not exist". Safe to no-op: there is
# nothing to backfill on a fresh install, which is exactly the scenario this
# crashed on.


class Migration(migrations.Migration):
    dependencies = [
        ("importer", "0005_fixup_dynamic_shema_table_names"),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
