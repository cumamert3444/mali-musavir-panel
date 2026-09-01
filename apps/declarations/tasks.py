import logging

from celery import shared_task

from apps.declarations.services import generate_upcoming_declaration_instances

logger = logging.getLogger(__name__)


@shared_task(name="apps.declarations.tasks.generate_upcoming_declaration_instances")
def generate_upcoming_declaration_instances_task(months_ahead: int = 2):
    total = generate_upcoming_declaration_instances(months_ahead=months_ahead)
    logger.info("Beyanname donem uretimi tamamlandi: %s kayit olusturuldu/dogrulandi.", total)
    return total
