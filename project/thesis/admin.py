from django.contrib import admin

from .models import Configuration, Cascade, RecognizerPreTrainedData


# Register your models here.
@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['pk', 'cascade_name', 'recognizer_name',
                    'objdetector_name', 'current']


@admin.register(Cascade)
class CascadeAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name']


@admin.register(RecognizerPreTrainedData)
class RecognizerPreTrainedDataAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'recognizer']
