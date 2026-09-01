import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("mali_musavir_panel")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Zamanlanmis gorevler: beyanname/vade hatirlatmalari ve gecikmis tahsilat kontrolu.
# Prod'da django-celery-beat admin uzerinden de yonetilebilir; burada kod-tabanli
# varsayilan bir plan tanimlanir.
app.conf.beat_schedule = {
    "generate-declaration-instances-daily": {
        "task": "apps.declarations.tasks.generate_upcoming_declaration_instances",
        "schedule": crontab(hour=2, minute=0),
    },
    "send-declaration-reminders-daily": {
        "task": "apps.notifications.tasks.send_declaration_due_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    "flag-overdue-invoices-daily": {
        "task": "apps.notifications.tasks.flag_overdue_invoices",
        "schedule": crontab(hour=8, minute=15),
    },
    "send-legal-notification-reminders-daily": {
        "task": "apps.notifications.tasks.send_legal_notification_reminders",
        "schedule": crontab(hour=8, minute=30),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
