"""Cari hesap ekstresi / tahakkuk özetini PDF olarak üretir.

Rakip ürünlerdeki (Tek Hamle) 'onaylanan tahakkuk fişlerini/borç
pusulalarını PDF olarak müşteriye gönderme' özelliğinin PDF üretim kısmı.
`apps.notifications.dispatch` bu PDF'i e-posta ekine koyar.
"""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

PRIMARY_HEX = "#2563eb"
DARK_HEX = "#0f172a"


def _money(value) -> str:
    try:
        return f"{float(value):,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(value)


def generate_statement_pdf(*, office, client, statement: dict, note: str = "") -> bytes:
    """`statement`, `apps.invoicing.services.compute_client_statement()`
    çıktısıyla aynı şekildedir (entries + summary). PDF byte içeriğini
    döner (dosyaya yazmaz, doğrudan e-posta ekine veya HTTP yanıtına
    verilebilir)."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"Cari Hesap Ekstresi - {client.title}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("StatementTitle", parent=styles["Title"], textColor=colors.HexColor(DARK_HEX), fontSize=18)
    office_style = ParagraphStyle("OfficeName", parent=styles["Normal"], textColor=colors.HexColor(PRIMARY_HEX), fontSize=11, spaceAfter=2)
    normal = styles["Normal"]

    story = [
        Paragraph(office.name or "Mali Müşavirlik Ofisi", office_style),
        Paragraph("Cari Hesap Ekstresi", title_style),
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Müşteri:</b> {client.title}", normal),
    ]
    if client.tax_number:
        story.append(Paragraph(f"<b>Vergi No:</b> {client.tax_number}", normal))
    story.append(Spacer(1, 6 * mm))

    summary = statement["summary"]
    summary_table = Table(
        [
            ["Toplam Faturalanan", "Toplam Tahsil Edilen", "Bakiye"],
            [_money(summary["total_invoiced"]), _money(summary["total_paid"]), _money(summary["balance_due"])],
        ],
        colWidths=[55 * mm, 55 * mm, 55 * mm],
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(DARK_HEX)),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8 * mm))

    if note:
        story.append(Paragraph(note, normal))
        story.append(Spacer(1, 6 * mm))

    rows = [["Tarih", "Tür", "Referans", "Açıklama", "Borç", "Alacak", "Bakiye"]]
    for entry in statement["entries"]:
        date_val = entry["date"]
        date_str = date_val.isoformat() if hasattr(date_val, "isoformat") else str(date_val)
        rows.append([
            date_str,
            "Fatura" if entry["type"] == "invoice" else "Tahsilat",
            entry["reference"],
            entry["description"],
            _money(entry["debit"]) if entry["debit"] else "-",
            _money(entry["credit"]) if entry["credit"] else "-",
            _money(entry["balance"]),
        ])

    if len(rows) == 1:
        story.append(Paragraph("Bu dönemde hareket bulunmuyor.", normal))
    else:
        entries_table = Table(rows, colWidths=[20 * mm, 18 * mm, 24 * mm, 45 * mm, 22 * mm, 22 * mm, 24 * mm], repeatRows=1)
        entries_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_HEX)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(entries_table)

    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "Bu ekstre Müşavir Asistanı paneli üzerinden otomatik oluşturulmuştur ve resmi bir tahsilat/tahakkuk "
        "fişi yerine geçmez.",
        ParagraphStyle("Footer", parent=normal, fontSize=7.5, textColor=colors.HexColor("#94a3b8")),
    ))

    doc.build(story)
    return buffer.getvalue()
