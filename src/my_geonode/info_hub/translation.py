from modeltranslation.translator import translator, TranslationOptions
from .models import AdvisoryMessage, Disease


class AdvisoryMessageTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'advisory_content',
        'suggestion',
        'potential_risks',
        'rainfall_forecast',
        'temperature_outlook',
    )


class DiseaseTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
        'suggestion',
        'causes',
        'treatment_options',
        'prevention_methods',
        'symptoms',
    )


translator.register(AdvisoryMessage, AdvisoryMessageTranslationOptions)
translator.register(Disease, DiseaseTranslationOptions)
