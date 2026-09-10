from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import Membership, User
from apps.tenants.models import Office, Subscription, SubscriptionPlan


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "phone", "is_active", "date_joined"]
        read_only_fields = ["id", "is_active", "date_joined"]


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    office_name = serializers.CharField(source="office.name", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "office", "office_name", "role", "is_active", "created_at"]
        read_only_fields = ["id", "office", "created_at"]


class MeSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "memberships", "is_staff", "is_superuser"]
        read_only_fields = ["id", "email", "memberships", "is_staff", "is_superuser"]


class InviteMemberSerializer(serializers.Serializer):
    """Mevcut bir ofise yeni bir kullanici davet eder / uye ekler.

    Kullanici e-postasi sistemde yoksa gecici sifre ile olusturulur
    (ileride e-posta ile davet linki gonderimi eklenebilir)."""

    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(choices=Membership.Role.choices, default=Membership.Role.BOOKKEEPER)

    def create(self, validated_data):
        office = self.context["office"]
        email = validated_data["email"].lower().strip()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": validated_data.get("first_name", ""),
                "last_name": validated_data.get("last_name", ""),
            },
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])

        membership, _ = Membership.objects.update_or_create(
            user=user,
            office=office,
            defaults={"role": validated_data["role"], "is_active": True},
        )
        return membership


class RegisterOfficeSerializer(serializers.Serializer):
    """Yeni bir mali musavirlik ofisinin (tenant) ve sahibinin (owner) tek
    istekte olusturuldugu kayit akisi -- 'yeni ofis olustur' formu."""

    office_name = serializers.CharField(max_length=200)
    tax_number = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    owner_email = serializers.EmailField()
    owner_first_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    owner_last_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    owner_password = serializers.CharField(write_only=True, min_length=8)

    def validate_owner_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu e-posta ile kayitli bir kullanici zaten var.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        office = Office.objects.create(
            name=validated_data["office_name"],
            tax_number=validated_data.get("tax_number", ""),
        )

        trial_plan, _ = SubscriptionPlan.objects.get_or_create(
            code="deneme",
            defaults={"name": "Deneme Paketi", "max_users": 3, "max_clients": 25, "price_monthly": 0},
        )
        Subscription.objects.create(office=office, plan=trial_plan, status=Subscription.Status.TRIALING)

        owner = User.objects.create_user(
            email=validated_data["owner_email"],
            password=validated_data["owner_password"],
            first_name=validated_data.get("owner_first_name", ""),
            last_name=validated_data.get("owner_last_name", ""),
        )
        Membership.objects.create(user=owner, office=office, role=Membership.Role.OWNER)

        return {"office": office, "owner": owner}


class PasswordResetRequestSerializer(serializers.Serializer):
    """`POST /api/v1/accounts/password-reset/` girdisi -- sadece e-posta.

    GÜVENLİK NOTU: bu serializer/view, e-posta sistemde kayıtlı olsun ya da
    olmasın HER ZAMAN aynı genel başarı mesajını döner (bkz. views.py) --
    aksi halde "bu e-posta kayıtlı mı?" sorgulanabilir hale gelir (user
    enumeration)."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """`POST /api/v1/accounts/password-reset-confirm/` girdisi -- e-postayla
    gelen link'teki uid+token çiftiyle yeni şifreyi doğrular ve uygular."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
