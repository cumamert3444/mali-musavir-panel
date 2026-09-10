from rest_framework import serializers

from apps.bank_statements.models import BankStatementImport, BankTransaction


class BankTransactionSerializer(serializers.ModelSerializer):
    client_title = serializers.CharField(source="client.title", read_only=True)

    class Meta:
        model = BankTransaction
        fields = [
            "id", "statement", "client", "client_title",
            "transaction_date", "description", "direction", "amount", "balance_after",
            "account_code", "status", "source", "suggested_by_ai", "raw_row_index", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "statement", "source", "suggested_by_ai", "raw_row_index", "created_at", "updated_at"]


class BankStatementImportSerializer(serializers.ModelSerializer):
    client_title = serializers.CharField(source="client.title", read_only=True)
    transactions = BankTransactionSerializer(many=True, read_only=True)
    transaction_count = serializers.SerializerMethodField()

    class Meta:
        model = BankStatementImport
        fields = [
            "id", "client", "client_title",
            "bank_name", "bank_account_code", "account_label", "period_label",
            "source_format", "file", "status", "row_count", "parsed_count",
            "error_message", "notes", "transactions", "transaction_count",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "row_count", "parsed_count", "error_message",
            "transactions", "transaction_count", "created_at", "updated_at",
        ]

    def get_transaction_count(self, obj) -> int:
        return obj.transactions.count() if obj.pk else 0


class BankStatementImportListSerializer(BankStatementImportSerializer):
    """Liste görünümünde `transactions` alanını (potansiyel yüzlerce satır)
    dışarıda bırakan hafif sürüm -- detay görünümünde tam serializer kullanılır."""

    class Meta(BankStatementImportSerializer.Meta):
        fields = [f for f in BankStatementImportSerializer.Meta.fields if f != "transactions"]
