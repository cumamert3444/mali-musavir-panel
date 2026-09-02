"""Cari hesap ekstresi / tahakkuk gönderim servisi (e-posta + WhatsApp).

Rakip ürünlerdeki (Tek Hamle) 'onaylanan tahakkuk fişlerini WhatsApp/
e-postayla toplu gönderme' özelliğinin karşılığı.

DÜRÜST KAPSAM SINIRI:
- **E-posta**: GERÇEK gönderim yapar -- `settings.EMAIL_HOST` yapılandırılmışsa
  SMTP ile, yapılandırılmamışsa Django'nun konsol backend'i ile (sadece log,
  geliştirme ortamı için) gönderilir.
- **WhatsApp**: Meta/Twilio WhatsApp Business API'leri; telefon numarası
  doğrulaması ve onaylı mesaj şablonu gerektirir. Bu sürümde gerçek bir
  sağlayıcıya bağlı DEĞİLDİR -- `settings.WHATSAPP_PROVIDER_API_KEY`
  boşsa (varsayılan) `DispatchError` fırlatılır ve kullanıcıya net bir
  Türkçe hata döner; sahte bir "gönderildi" yanıtı ASLA üretilmez.
  Sağlayıcı bağlandığında `_send_via_whatsapp()` genişletilmelidir.
"""
from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from apps.invoicing.services import compute_client_statement
from apps.notifications.models import Notification
from apps.notifications.statement_pdf import generate_statement_pdf


class DispatchError(Exception):
    """Gönderim yapılamadığında (yapılandırma eksik, alıcı bilgisi yok vb.)
    kullanıcıya gösterilecek net bir mesajla fırlatılır."""


def _send_via_email(*, office, client, pdf_bytes: bytes, subject: str, message: str):
    if not client.email:
        raise DispatchError(f"{client.title} için kayıtlı bir e-posta adresi yok. Önce müşteri kartına e-posta ekleyin.")

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[client.email],
    )
    email.attach(f"ekstre-{client.id}.pdf", pdf_bytes, "application/pdf")
    email.send(fail_silently=False)


def _send_via_whatsapp(*, office, client, pdf_bytes: bytes, subject: str, message: str):
    api_key = getattr(settings, "WHATSAPP_PROVIDER_API_KEY", "")
    if not api_key:
        raise DispatchError(
            "WhatsApp entegrasyonu henüz yapılandırılmamış (WHATSAPP_PROVIDER_API_KEY tanımlı değil). "
            "Şimdilik e-posta ile gönderebilirsiniz; bir WhatsApp Business API sağlayıcısı (Meta/Twilio) "
            "bağlandığında bu kanal otomatik olarak aktif olacaktır."
        )
    if not client.phone:
        raise DispatchError(f"{client.title} için kayıtlı bir telefon numarası yok.")
    # NOT: Gercek saglayici entegrasyonu burada implemente edilecek (backlog).
    # Ornek: Meta Cloud API / Twilio WhatsApp Business API cagrisi.
    raise DispatchError(
        "WhatsApp API anahtarı tanımlı ama sağlayıcı entegrasyonu (Meta/Twilio çağrısı) henüz "
        "bağlanmadı -- bu, geliştirme ekibinin sağlayıcı hesabıyla tamamlaması gereken bir adımdır."
    )


DISPATCHERS = {
    Notification.Channel.EMAIL: _send_via_email,
    Notification.Channel.WHATSAPP: _send_via_whatsapp,
}


def dispatch_client_statement(*, request, client, channel: str, note: str = "") -> Notification:
    """Bir müşterinin cari hesap ekstresini PDF olarak üretir ve seçilen
    kanaldan gönderir. Başarılı da olsa başarısız da olsa bir `Notification`
    kaydı oluşturur (denetim/geçmiş için) ve döner. Başarısızlıkta
    `Notification.send_error` doludur VE `DispatchError` fırlatılır."""
    if channel not in DISPATCHERS:
        raise DispatchError(f"Geçersiz gönderim kanalı: {channel}")

    office = request.office
    statement = compute_client_statement(client)
    subject = f"{office.name} - {client.title} Cari Hesap Ekstresi"
    message = note or (
        f"Sayın {client.title} yetkilisi,\n\nGüncel cari hesap ekstreniz ekte yer almaktadır.\n\n"
        f"İyi çalışmalar dileriz.\n{office.name}"
    )

    notification = Notification.objects.create(
        office=office,
        recipient=request.user,
        channel=channel,
        category=Notification.Category.GENERAL,
        title=subject,
        body=message,
        related_object_type="Client",
        related_object_id=str(client.id),
    )

    try:
        pdf_bytes = generate_statement_pdf(office=office, client=client, statement=statement, note=note)
        DISPATCHERS[channel](office=office, client=client, pdf_bytes=pdf_bytes, subject=subject, message=message)
    except DispatchError as exc:
        notification.send_error = str(exc)
        notification.save(update_fields=["send_error"])
        raise
    except Exception as exc:  # noqa: BLE001 -- beklenmeyen SMTP/altyapı hatalarını da kaydet
        notification.send_error = f"Beklenmeyen hata: {exc}"
        notification.save(update_fields=["send_error"])
        raise DispatchError(f"Gönderim sırasında beklenmeyen bir hata oluştu: {exc}") from exc

    notification.sent_at = timezone.now()
    notification.save(update_fields=["sent_at"])
    return notification
