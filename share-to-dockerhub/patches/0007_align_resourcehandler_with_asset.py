from django.db import migrations

# PATCHED: same bug as 0006_dataset_migration.py - imports the LIVE
# geonode.layers.models.Dataset (with modeltranslation's title_am/om/ti
# fields added by a later migration) instead of the historical model, so it
# crashes with "column layers_dataset.title_am does not exist" on a fresh,
# empty database. This migration backfills legacy resource-handler data for
# datasets imported before this system existed; on a fresh install there is
# nothing to backfill, so it is safe to no-op.


class Migration(migrations.Migration):
    dependencies = [
        ("importer", "0006_dataset_migration"),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
