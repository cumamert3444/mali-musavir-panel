"""Cari hesap ekstresi hesaplama mantığı.

`apps.invoicing.views.ClientAccountStatementView` (panel ekranı) ve
`apps.notifications.dispatch` (e-posta/WhatsApp ile ekstre gönderimi) aynı
hesaplamayı paylaşır -- iş mantığı burada tek yerde tutulur.
"""
from __future__ import annotations

from apps.clients.models import Client
from apps.invoicing.models import ServiceInvoice


def compute_client_statement(client: Client) -> dict:
    invoices = ServiceInvoice.objects.filter(client=client).exclude(
        status=ServiceInvoice.Status.CANCELED
    ).prefetch_related("lines", "payments")

    entries = []
    for invoice in invoices:
        entries.append({
            "date": invoice.issue_date,
            "type": "invoice",
            "reference": invoice.invoice_number,
            "description": invoice.period_label or "Hizmet faturasi",
            "debit": invoice.total_amount,
            "credit": 0,
        })
        for payment in invoice.payments.all():
            entries.append({
                "date": payment.paid_at,
                "type": "payment",
                "reference": invoice.invoice_number,
                "description": f"Tahsilat ({payment.get_method_display()})",
                "debit": 0,
                "credit": payment.amount,
            })

    entries.sort(key=lambda e: (e["date"], e["type"] == "payment"))

    running_balance = 0
    for entry in entries:
        running_balance += entry["debit"] - entry["credit"]
        entry["balance"] = running_balance

    total_invoiced = sum((inv.total_amount for inv in invoices), start=0)
    total_paid = sum((inv.paid_amount for inv in invoices), start=0)

    return {
        "client": client,
        "entries": entries,
        "summary": {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "balance_due": total_invoiced - total_paid,
        },
    }
