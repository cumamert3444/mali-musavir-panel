import datetime as dt
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.declarations.models import DeclarationInstance
from apps.invoicing.models import ServiceInvoice
from apps.legal_notices.models import LegalNotification
from apps.notifications.models import Notification
from apps.notifications.services import notify

logger = logging.getLogger(__name__)


def _recipients_for_client(client):
    """Musteriye atanmis kullanicilar; hic atama yoksa ofis sahipleri."""
    from apps.accounts.models import Membership

    assigned_user_ids = list(client.assignments.values_list("user_id", flat=True))
    if assigned_user_ids:
        from apps.accounts.models import User

        return User.objects.filter(id__in=assigned_user_ids, is_active=True)

    return [
        m.user
        for m in Membership.objects.filter(office=client.office, role=Membership.Role.OWNER, is_active=True)
        .select_related("user")
    ]


@shared_task(name="apps.notifications.tasks.send_declaration_due_reminders")
def send_declaration_due_reminders():
    today = timezone.localdate()
    reminder_days = getattr(settings, "DECLARATION_REMINDER_DAYS_BEFORE", [7, 3, 1, 0])
    target_dates = {today + dt.timedelta(days=d) for d in reminder_days}

    queryset = (
        DeclarationInstance.objects.filter(due_date__in=target_dates)
        .exclude(
            status__in=[
                DeclarationInstance.Status.SUBMITTED,
                DeclarationInstance.Status.PAID,
                DeclarationInstance.Status.NOT_APPLICABLE,
            ]
        )
        .select_related("client", "declaration_type", "office")
    )

    sent = 0
    for instance in queryset:
        days_left = (instance.due_date - today).days
        title = f"{instance.declaration_type.name} vadesi yaklasiyor: {instance.client.title}"
        body = (
            f"{instance.client.title} icin {instance.declaration_type.name} ({instance.period_label}) "
            f"son teslim tarihi {instance.due_date:%d.%m.%Y} "
            f"({'bugun' if days_left == 0 else f'{days_left} gun kaldi'})."
        )
        for recipient in _recipients_for_client(instance.client):
            notify(
                office=instance.office,
                recipient=recipient,
                title=title,
                body=body,
                category=Notification.Category.DECLARATION_DUE,
                channel=Notification.Channel.IN_APP,
                related_object_type="DeclarationInstance",
                related_object_id=instance.id,
            )
            sent += 1

        if instance.due_date < today and instance.status == DeclarationInstance.Status.PENDING:
            instance.status = DeclarationInstance.Status.OVERDUE
            instance.save(update_fields=["status"])

    logger.info("Beyanname hatirlatmalari gonderildi: %s bildirim.", sent)
    return sent


@shared_task(name="apps.notifications.tasks.flag_overdue_invoices")
def flag_overdue_invoices():
    from apps.accounts.models import Membership

    today = timezone.localdate()
    queryset = ServiceInvoice.objects.filter(
        due_date__lt=today,
        status__in=[ServiceInvoice.Status.SENT, ServiceInvoice.Status.PARTIALLY_PAID],
    ).select_related("client", "office")

    flagged = 0
    for invoice in queryset:
        invoice.status = ServiceInvoice.Status.OVERDUE
        invoice.save(update_fields=["status"])
        flagged += 1

        owners = [
            m.user
            for m in Membership.objects.filter(
                office=invoice.office, role=Membership.Role.OWNER, is_active=True
            ).select_related("user")
        ]
        for owner in owners:
            notify(
                office=invoice.office,
                recipient=owner,
                title=f"Gecikmis tahsilat: {invoice.client.title}",
                body=f"{invoice.invoice_number} numarali fatura ({invoice.balance_due} TL bakiye) vadesi gecti.",
                category=Notification.Category.INVOICE_OVERDUE,
                channel=Notification.Channel.IN_APP,
                related_object_type="ServiceInvoice",
                related_object_id=invoice.id,
            )

    logger.info("Gecikmis fatura isaretlendi: %s adet.", flagged)
    return flagged


@shared_task(name="apps.notifications.tasks.send_legal_notification_reminders")
def send_legal_notification_reminders():
    """e-Tebligat / resmi bildirim cevap suresi yaklasanlar icin hatirlatma.

    Hattat Musavir'in one cikardigi 'e-Tebligat otomatik takip' ozelliginin
    karsiligi -- gercek PTT/GIB e-Tebligat entegrasyonu olmadigindan, bu
    gorev sadece sistemde ELLE kayitli LegalNotification kayitlarini kontrol
    eder (bkz. apps.legal_notices).
    """
    from apps.accounts.models import Membership

    today = timezone.localdate()
    reminder_days = getattr(settings, "DECLARATION_REMINDER_DAYS_BEFORE", [7, 3, 1, 0])
    target_dates = {today + dt.timedelta(days=d) for d in reminder_days}

    queryset = (
        LegalNotification.objects.filter(response_due_date__in=target_dates)
        .exclude(status__in=[LegalNotification.Status.RESPONDED, LegalNotification.Status.NOT_APPLICABLE])
        .select_related("client", "office", "assigned_to")
    )

    sent = 0
    for notification_obj in queryset:
        days_left = (notification_obj.response_due_date - today).days
        title = f"Tebligat cevap suresi yaklasiyor: {notification_obj.title}"
        body = (
            f"{notification_obj.get_source_display()} kaynakli '{notification_obj.title}' tebligatinin "
            f"cevap/itiraz suresi {notification_obj.response_due_date:%d.%m.%Y} "
            f"({'bugun' if days_left == 0 else f'{days_left} gun kaldi'})."
        )

        recipients = []
        if notification_obj.assigned_to and notification_obj.assigned_to.is_active:
            recipients = [notification_obj.assigned_to]
        else:
            recipients = [
                m.user
                for m in Membership.objects.filter(
                    office=notification_obj.office, role=Membership.Role.OWNER, is_active=True
                ).select_related("user")
            ]

        for recipient in recipients:
            notify(
                office=notification_obj.office,
                recipient=recipient,
                title=title,
                body=body,
                category=Notification.Category.LEGAL_NOTIFICATION,
                channel=Notification.Channel.IN_APP,
                related_object_type="LegalNotification",
                related_object_id=notification_obj.id,
            )
            sent += 1

        if notification_obj.response_due_date < today and notification_obj.status == LegalNotification.Status.NEW:
            notification_obj.status = LegalNotification.Status.EXPIRED
            notification_obj.save(update_fields=["status"])

    logger.info("e-Tebligat hatirlatmalari gonderildi: %s bildirim.", sent)
    return sent
