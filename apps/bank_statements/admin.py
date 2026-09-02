from django.contrib import admin

from apps.bank_statements.models import BankStatementImport, BankTransaction


@admin.register(BankStatementImport)
class BankStatementImportAdmin(admin.ModelAdmin):
    list_display = ["client", "bank_name", "period_label", "source_format", "status", "row_count", "parsed_count", "office"]
    list_filter = ["source_format", "status"]
    search_fields = ["client__title", "bank_name", "period_label"]


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ["client", "transaction_date", "description", "direction", "amount", "account_code", "status", "source"]
    list_filter = ["direction", "status", "source"]
    search_fields = ["client__title", "description", "account_code"]
