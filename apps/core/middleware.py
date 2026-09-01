import uuid

from django.utils.deprecation import MiddlewareMixin

from apps.core.tenant import resolve_office


class TenantMiddleware(MiddlewareMixin):
    """
    Her isteğe `request.office` özniteliğini ekler.

    Session/Django-admin veya X-API-Key ile gelen istekler için ofis burada
    çözülür. JWT ile kimliği doğrulanan DRF istekleri için kullanıcı bu
    aşamada henüz bilinmediğinden `request.office` burada None kalabilir;
    bu durumda `apps.core.views.TenantScopedViewSetMixin.initial()` DRF
    kimlik doğrulamasından sonra aynı çözümlemeyi tekrar dener.
    """

    def process_request(self, request):
        request.office = resolve_office(request)


class AuditLogMiddleware(MiddlewareMixin):
    """Yazma amaçlı (GET/HEAD/OPTIONS dışı) istekler için hafif bir istek
    kimliği üretir; asıl denetim kaydı ilgili view/servis katmanında
    apps.core.audit.log_action() ile oluşturulur. Bu middleware sadece
    request.request_id ve request.client_ip gibi ortak alanları hazırlar."""

    def process_request(self, request):
        request.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.client_ip = self._get_client_ip(request)

    @staticmethod
    def _get_client_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
