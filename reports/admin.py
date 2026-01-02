from django.contrib import admin
from .models import ReportTemplate

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'shop', 'is_default', 'created_at']
    list_filter = ['report_type', 'shop', 'is_default', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']
