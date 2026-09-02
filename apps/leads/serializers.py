from rest_framework import serializers

from apps.leads.models import DemoRequest


class DemoRequestCreateSerializer(serializers.ModelSerializer):
    """Herkese açık form gönderimi için -- sadece dolduran kişinin
    girebileceği alanlar yazılabilir; durum/tarih sunucu tarafından atanır."""

    class Meta:
        model = DemoRequest
        fields = ["full_name", "office_name", "email", "phone", "message", "source_path"]


class DemoRequestAdminSerializer(serializers.ModelSerializer):
    """Süper admin panelinde tam görünüm + durum güncelleme için."""

    class Meta:
        model = DemoRequest
        fields = ["id", "full_name", "office_name", "email", "phone", "message", "status", "source_path", "created_at"]
        read_only_fields = ["id", "full_name", "office_name", "email", "phone", "message", "source_path", "created_at"]
