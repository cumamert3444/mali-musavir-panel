"""Bildirim gonderim katmani.

Su an icin gercek SMS/WhatsApp saglayici entegrasyonu yok -- fonksiyonlar
kayit olusturur ve (varsa) e-postayi Django'nun e-posta backend'i ile
gonderir; SMS/WhatsApp icin ayrilan yer, ileride bir saglayici (Netgsm,
Twilio, vb.) baglanacagi acikca yoruma yazilmis TODO'lar ile isaretlendi.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


def notify(
    *,
    office,
    recipient,
    title: str,
    body: str = "",
    category: str = Notification.Category.GENERAL,
    channel: str = Notification.Channel.IN_APP,
    related_object_type: str = "",
    related_object_id: str = "",
) -> Notification:
    notification = Notification.objects.create(
        office=office,
        recipient=recipient,
        channel=channel,
        category=category,
        title=title,
        body=body,
        related_object_type=related_object_type,
        related_object_id=str(related_object_id) if related_object_id else "",
    )

    if channel == Notification.Channel.EMAIL:
        _send_email(notification)
    elif channel == Notification.Channel.SMS:
        _send_sms(notification)
    elif channel == Notification.Channel.WHATSAPP:
        _send_whatsapp(notification)
    # IN_APP icin ekstra bir gonderim adimi yok; panelde /notifications/ ile okunur.

    return notification


def _send_email(notification: Notification) -> None:
    from django.utils import timezone

    try:
        send_mail(
            subject=notification.title,
            message=notification.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        notification.sent_at = timezone.now()
        notification.save(update_fields=["sent_at"])
    except Exception as exc:  # pragma: no cover - saglayici hatasi
        logger.exception("E-posta bildirimi gonderilemedi (notification=%s)", notification.id)
        notification.send_error = str(exc)
        notification.save(update_fields=["send_error"])


def _send_sms(notification: Notification) -> None:
    # TODO: Netgsm/Twilio vb. bir SMS saglayicisi burada cagrilacak.
    # settings.SMS_PROVIDER_API_KEY bos oldugu surece sadece loglanir.
    if not settings.SMS_PROVIDER_API_KEY:
        logger.info("[SMS-STUB] %s -> %s: %s", notification.recipient, notification.title, notification.body)
        return
    logger.warning("SMS saglayicisi henuz entegre edilmedi.")


def _send_whatsapp(notification: Notification) -> None:
    # TODO: WhatsApp Business API entegrasyonu burada cagrilacak.
    if not settings.WHATSAPP_PROVIDER_API_KEY:
        logger.info("[WHATSAPP-STUB] %s -> %s: %s", notification.recipient, notification.title, notification.body)
        return
    logger.warning("WhatsApp saglayicisi henuz entegre edilmedi.")
