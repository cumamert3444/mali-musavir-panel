from django.contrib import admin

from apps.pos_sync.models import DailyPosReport


@admin.register(DailyPosReport)
class DailyPosReportAdmin(admin.ModelAdmin):
    list_display = ["client", "report_date", "gross_sales", "vat_amount", "pos_collection", "office"]
    list_filter = ["report_date"]
    search_fields = ["client__title", "okc_no"]
