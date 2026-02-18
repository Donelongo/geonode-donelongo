from django.db import migrations, models


def copy_base_to_en(apps, schema_editor):
    AdvisoryMessage = apps.get_model('info_hub', 'AdvisoryMessage')
    Disease = apps.get_model('info_hub', 'Disease')

    # AdvisoryMessage fields mapping: base_field -> en_field
    am_fields = [
        ('title', 'title_en'),
        ('advisory_content', 'advisory_content_en'),
        ('suggestion', 'suggestion_en'),
        ('potential_risks', 'potential_risks_en'),
        ('rainfall_forecast', 'rainfall_forecast_en'),
        ('temperature_outlook', 'temperature_outlook_en'),
    ]

    for obj in AdvisoryMessage.objects.all():
        changed = False
        for base, en in am_fields:
            base_val = getattr(obj, base, None)
            en_val = getattr(obj, en, None)
            if (en_val is None or en_val == '') and base_val not in (None, ''):
                setattr(obj, en, base_val)
                changed = True
        if changed:
            obj.save()

    # Disease fields mapping
    dis_fields = [
        ('name', 'name_en'),
        ('description', 'description_en'),
        ('suggestion', 'suggestion_en'),
        ('causes', 'causes_en'),
        ('treatment_options', 'treatment_options_en'),
        ('prevention_methods', 'prevention_methods_en'),
        ('symptoms', 'symptoms_en'),
    ]

    for obj in Disease.objects.all():
        changed = False
        for base, en in dis_fields:
            base_val = getattr(obj, base, None)
            en_val = getattr(obj, en, None)
            if (en_val is None or en_val == '') and base_val not in (None, ''):
                setattr(obj, en, base_val)
                changed = True
        if changed:
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('info_hub', '0002_rename_description_advisorymessage_advisory_content'),
    ]

    operations = [
        # AdvisoryMessage translation fields
        migrations.AddField(
            model_name='advisorymessage',
            name='title_en',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='title_am',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='title_ti',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='title_om',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),

        migrations.AddField(
            model_name='advisorymessage',
            name='advisory_content_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='advisory_content_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='advisory_content_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='advisory_content_om',
            field=models.TextField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='advisorymessage',
            name='suggestion_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='suggestion_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='suggestion_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='suggestion_om',
            field=models.TextField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='advisorymessage',
            name='potential_risks_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='potential_risks_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='potential_risks_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='potential_risks_om',
            field=models.TextField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='advisorymessage',
            name='rainfall_forecast_en',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='rainfall_forecast_am',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='rainfall_forecast_ti',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='rainfall_forecast_om',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),

        migrations.AddField(
            model_name='advisorymessage',
            name='temperature_outlook_en',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='temperature_outlook_am',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='temperature_outlook_ti',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='advisorymessage',
            name='temperature_outlook_om',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),

        # Disease translation fields
        migrations.AddField(
            model_name='disease',
            name='name_en',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='name_am',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='name_ti',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='name_om',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),

        migrations.AddField(
            model_name='disease',
            name='description_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='description_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='description_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='description_om',
            field=models.TextField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='disease',
            name='suggestion_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='suggestion_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='suggestion_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='suggestion_om',
            field=models.TextField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='disease',
            name='causes_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='causes_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='causes_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='causes_om',
            field=models.TextField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='disease',
            name='treatment_options_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='treatment_options_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='treatment_options_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='treatment_options_om',
            field=models.TextField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='disease',
            name='prevention_methods_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='prevention_methods_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='prevention_methods_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='prevention_methods_om',
            field=models.TextField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='disease',
            name='symptoms_en',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='symptoms_am',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='symptoms_ti',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='disease',
            name='symptoms_om',
            field=models.TextField(null=True, blank=True),
        ),

        # Data migration: copy base -> _en when empty
        migrations.RunPython(copy_base_to_en, migrations.RunPython.noop),
    ]
