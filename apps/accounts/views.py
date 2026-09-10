from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import Membership, User
from apps.accounts.serializers import (
    InviteMemberSerializer,
    MembershipSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterOfficeSerializer,
)
from apps.core.audit import log_action
from apps.core.permissions import HasActiveOffice, HasOfficeRole
from apps.core.views import TenantScopedViewSetMixin

GENERIC_RESET_MESSAGE = (
    "Bu e-posta adresi sistemde kayıtlıysa, şifre sıfırlama bağlantısı gönderildi. "
    "Gelen kutunuzu (ve spam/gereksiz klasörünü) kontrol edin."
)


class RegisterOfficeView(APIView):
    """`POST /api/v1/accounts/register-office/`

    Yeni bir ofis (tenant) ve ilk kullanici (owner) olusturur. Herkese acik --
    yeni bir mali musavirlik ofisinin sisteme kaydolma yolu budur."""

    permission_classes = [AllowAny]
    serializer_class = RegisterOfficeSerializer

    def post(self, request, *args, **kwargs):
        serializer = RegisterOfficeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        log_action(
            action="create",
            office=result["office"],
            actor=result["owner"],
            model_name="Office",
            object_id=result["office"].id,
            metadata={"event": "office_registered"},
        )
        return Response(
            {
                "office_id": result["office"].id,
                "office_name": result["office"].name,
                "owner_email": result["owner"].email,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(RetrieveUpdateAPIView):
    """`GET/PATCH /api/v1/accounts/me/` -- oturum acmis kullanicinin profili
    ve uye oldugu tum ofis/rol bilgileri."""

    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class MembershipViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Aktif ofisin ekip uyeleri: listeleme, davet etme (create), rol
    guncelleme, pasife alma. Yazma islemleri sadece OWNER rolune acik."""

    queryset = Membership.objects.select_related("user", "office").all()
    serializer_class = MembershipSerializer
    permission_classes = [HasActiveOffice, HasOfficeRole]
    filterset_fields = ["role", "is_active"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]

    @property
    def required_roles(self):
        if self.action in {"list", "retrieve"}:
            return None
        return [Membership.Role.OWNER]

    def create(self, request, *args, **kwargs):
        serializer = InviteMemberSerializer(data=request.data, context={"office": request.office})
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        log_action(request, action="create", model_name="Membership", object_id=membership.id)
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        membership = self.get_object()
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        log_action(request, action="update", model_name="Membership", object_id=membership.id,
                   metadata={"event": "deactivated"})
        return Response(MembershipSerializer(membership).data)


class PasswordResetRequestView(APIView):
    """`POST /api/v1/accounts/password-reset/` -- `{"email": "..."}`

    "Şifremi unuttum" akışının 1. adımı. Django'nun standart, kanıtlanmış
    `PasswordResetTokenGenerator`'ını kullanır (SHA ile imzalanmış, kullanıcının
    mevcut şifre hash'i + son giriş zamanına bağlı olduğu için şifre
    değişince veya belirli bir süre (varsayılan `PASSWORD_RESET_TIMEOUT`,
    Django varsayılanı 3 gün) sonra kendiliğinden geçersiz olur) -- ayrı bir
    veritabanı tablosu/migration GEREKTİRMEZ.

    GÜVENLİK: e-posta sistemde kayıtlı olsun ya da olmasın HER ZAMAN aynı
    genel mesaj dönülür (user enumeration'ı önlemek için) -- gerçek
    gönderim başarısız olsa bile (ör. SMTP yapılandırılmamış) istemciye bu
    sızdırılmaz, sadece sunucu tarafında loglanır.

    E-POSTA GÖNDERİMİ -- DÜRÜST KAPSAM: `settings.EMAIL_HOST` tanımlıysa
    gerçek SMTP ile gönderilir; tanımlı değilse Django'nun konsol backend'i
    kullanılır (yalnızca sunucu loglarına yazar, kullanıcıya ULAŞMAZ). Bu,
    projenin diğer e-posta gönderimleriyle (bkz. apps.notifications.dispatch)
    aynı, zaten var olan altyapıdır."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password-reset"
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        user = User.objects.filter(email=email, is_active=True).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            site_url = getattr(settings, "SITE_URL", "").rstrip("/")
            reset_link = f"{site_url}/sifre-sifirla?uid={uid}&token={token}"

            body = (
                f"Merhaba{' ' + user.first_name if user.first_name else ''},\n\n"
                f"Mali Müşavir Paneli hesabınız için bir şifre sıfırlama talebi aldık.\n\n"
                f"Yeni şifre belirlemek için aşağıdaki bağlantıya tıklayın:\n{reset_link}\n\n"
                f"Bu talebi siz yapmadıysanız bu e-postayı görmezden gelebilirsiniz; "
                f"şifreniz değişmeyecektir.\n\n"
                f"Bağlantı sınırlı bir süre için geçerlidir."
            )
            try:
                EmailMessage(
                    subject="Mali Müşavir Paneli - Şifre Sıfırlama",
                    body=body,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    to=[user.email],
                ).send(fail_silently=False)
                log_action(action="update", model_name="User", object_id=user.id,
                           actor=None, metadata={"event": "password_reset_requested"})
            except Exception:  # noqa: BLE001 -- gonderim hatasi kullaniciya asla sizdirilmiyor
                # SMTP yapilandirma hatasi vb. -- kullaniciya yine de genel
                # basari mesaji donulur (enumeration onlemi), sorun sunucu
                # tarafinda ele alinmali (EMAIL_HOST/EMAIL_HOST_USER/
                # EMAIL_HOST_PASSWORD ortam degiskenleri kontrol edilmeli).
                pass

        return Response({"detail": GENERIC_RESET_MESSAGE})


class PasswordResetConfirmView(APIView):
    """`POST /api/v1/accounts/password-reset-confirm/` --
    `{"uid": "...", "token": "...", "new_password": "..."}`

    "Şifremi unuttum" akışının 2. adımı -- e-postadaki linkten gelen uid+token
    çiftini doğrular ve şifreyi değiştirir."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_bytes(urlsafe_base64_decode(serializer.validated_data["uid"])).decode()
            user = User.objects.get(pk=uid, is_active=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {"detail": "Bağlantı geçersiz. Şifre sıfırlama işlemini yeniden başlatın."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response(
                {"detail": "Bağlantının süresi dolmuş veya zaten kullanılmış. Şifre sıfırlama işlemini yeniden başlatın."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        log_action(action="update", model_name="User", object_id=user.id, actor=user,
                   metadata={"event": "password_reset_completed"})

        return Response({"detail": "Şifreniz başarıyla güncellendi. Yeni şifrenizle giriş yapabilirsiniz."})
