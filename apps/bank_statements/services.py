"""Banka ekstresi dosyalarini (Excel/CSV/PDF) yapilandirilmis islem
satirlarina ayristiran servis fonksiyonlari.

DURUST KAPSAM NOTU (bkz. apps.bank_statements.models modul docstring'i):
Bu modul bankadan indirilen bir dosyayi OKUR ve OLABILDIGINCE dogru
ayristirmaya calisir -- gercek zamanli bir banka API'sine baglanmaz.
Turkiye'deki bankalarin ekstre disa aktarma formatlari (Excel kolon
basliklari, PDF sayfa duzeni) bankadan bankaya COK farklidir; bu yuzden
asagidaki fonksiyonlar mumkun oldugunca genis bir Turkce baslik/format
eslestirmesi dener ama HER ekstreyi %100 dogru ayristiracagini garanti
ETMEZ. Ayristirilamayan satirlar `errors` listesinde raporlanir ve hicbir
satir bu fonksiyonlardan otomatik "onayli" olarak cikmaz (bkz. views.py
-- tum satirlar BankTransaction.Status.DRAFT ile olusturulur).

Her `parse_*` fonksiyonu ayni sozlesmeyi paylasir:
    parse_xxx(file) -> (rows: list[dict], errors: list[str])
`rows` icindeki her sozluk su anahtarlari icerir (hepsi opsiyonel,
bulunamayanlar None/bos birakilir):
    transaction_date (datetime.date | None)
    description (str)
    amount (Decimal)
    direction ("credit" | "debit")
    balance_after (Decimal | None)
    raw_row_index (int)
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# --- Turkce/Ingilizce baslik es anlamlilari -------------------------------

DATE_HEADERS = {"tarih", "islem tarihi", "valor", "valor tarihi", "date", "islemtarihi", "tarihi"}
DESC_HEADERS = {
    "aciklama", "açıklama", "islem aciklamasi", "işlem açıklaması", "description",
    "detay", "aciklamasi", "islem", "hareket aciklamasi",
}
AMOUNT_HEADERS = {"tutar", "işlem tutarı", "islem tutari", "amount"}
DEBIT_HEADERS = {"borc", "borç", "cikis", "çıkış", "debit", "borç tutarı", "borc tutari"}
CREDIT_HEADERS = {"alacak", "giris", "giriş", "credit", "alacak tutarı", "alacak tutari"}
BALANCE_HEADERS = {"bakiye", "kalan bakiye", "balance"}

_TR_MAP = str.maketrans("çğıöşüİ", "cgiosui")


def _normalize_header(value) -> str:
    text = str(value or "").strip().lower().translate(_TR_MAP)
    return re.sub(r"\s+", " ", text).strip()


def _match_column(headers: list[str], candidates: set[str]) -> int | None:
    normalized = [_normalize_header(h) for h in headers]
    for idx, header in enumerate(normalized):
        if header in candidates:
            return idx
    # kismi eslesme (ör. "işlem tarihi (valör)")
    for idx, header in enumerate(normalized):
        if any(cand in header for cand in candidates):
            return idx
    return None


def _parse_amount(value) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    text = str(value).strip()
    if not text:
        return None
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    text = text.replace("TL", "").replace("₺", "").strip()
    if text.startswith("-"):
        negative = True
        text = text[1:].strip()
    # Turkce format: binlik "." ondalik "," -> "1.234,56"
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        amount = Decimal(text)
    except InvalidOperation:
        return None
    return -amount if negative else amount


_DATE_FORMATS = ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%y", "%d/%m/%y"]


def _parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    text = text.split(" ")[0]  # "01.08.2026 14:32:00" -> "01.08.2026"
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _row_from_fields(*, transaction_date, description, debit, credit, single_amount, balance, row_index) -> dict | None:
    """Ayri borc/alacak kolonlari VEYA tek tutar kolonu ile satir uretir."""
    direction = None
    amount = None
    if debit is not None or credit is not None:
        if debit and debit != 0:
            direction, amount = "debit", abs(debit)
        elif credit and credit != 0:
            direction, amount = "credit", abs(credit)
    elif single_amount is not None:
        if single_amount < 0:
            direction, amount = "debit", abs(single_amount)
        else:
            direction, amount = "credit", single_amount

    if amount is None or amount == 0:
        return None

    return {
        "transaction_date": transaction_date,
        "description": (description or "").strip()[:500],
        "amount": amount,
        "direction": direction,
        "balance_after": balance,
        "raw_row_index": row_index,
    }


# --- Excel (.xlsx) ---------------------------------------------------------

def parse_excel(file) -> tuple[list[dict], list[str]]:
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover
        return [], [f"openpyxl kutuphanesi yuklu degil: {exc}"]

    rows: list[dict] = []
    errors: list[str] = []
    try:
        workbook = openpyxl.load_workbook(file, data_only=True, read_only=True)
        sheet = workbook.active
        sheet_rows = sheet.iter_rows(values_only=True)
        try:
            header_row = next(sheet_rows)
        except StopIteration:
            return [], ["Dosyada satır bulunamadı."]
        headers = [str(h or "") for h in header_row]

        date_idx = _match_column(headers, DATE_HEADERS)
        desc_idx = _match_column(headers, DESC_HEADERS)
        amount_idx = _match_column(headers, AMOUNT_HEADERS)
        debit_idx = _match_column(headers, DEBIT_HEADERS)
        credit_idx = _match_column(headers, CREDIT_HEADERS)
        balance_idx = _match_column(headers, BALANCE_HEADERS)

        if date_idx is None or (amount_idx is None and debit_idx is None and credit_idx is None):
            errors.append(
                "Beklenen kolon başlıkları bulunamadı (Tarih / Tutar veya Borç-Alacak). "
                "İlk satırın başlık satırı olduğundan emin olun."
            )
            return [], errors

        for row_index, raw_row in enumerate(sheet_rows, start=2):
            try:
                tx_date = _parse_date(raw_row[date_idx]) if date_idx is not None and date_idx < len(raw_row) else None
                description = raw_row[desc_idx] if desc_idx is not None and desc_idx < len(raw_row) else ""
                debit = _parse_amount(raw_row[debit_idx]) if debit_idx is not None and debit_idx < len(raw_row) else None
                credit = _parse_amount(raw_row[credit_idx]) if credit_idx is not None and credit_idx < len(raw_row) else None
                single_amount = _parse_amount(raw_row[amount_idx]) if amount_idx is not None and amount_idx < len(raw_row) else None
                balance = _parse_amount(raw_row[balance_idx]) if balance_idx is not None and balance_idx < len(raw_row) else None

                if all(cell in (None, "") for cell in raw_row):
                    continue

                row = _row_from_fields(
                    transaction_date=tx_date, description=description, debit=debit,
                    credit=credit, single_amount=single_amount, balance=balance, row_index=row_index,
                )
                if row is None:
                    errors.append(f"Satır {row_index}: tutar okunamadı, atlandı.")
                    continue
                rows.append(row)
            except Exception as exc:  # noqa: BLE001 -- tek satirin hatasi tum dosyayi durdurmasin
                errors.append(f"Satır {row_index}: {exc}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Excel dosyası okunamadı: {exc}")
        return [], errors

    return rows, errors


# --- CSV --------------------------------------------------------------------

def parse_csv(file) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    try:
        raw = file.read()
        text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1254")  # bazı Türk bankası dökümleri Latin-5/Windows-1254
        except Exception as exc:  # noqa: BLE001
            return [], [f"Dosya metne çevrilemedi: {exc}"]

    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";" if sample.count(";") > sample.count(",") else ","

    reader = csv.reader(io.StringIO(text), dialect)
    try:
        header_row = next(reader)
    except StopIteration:
        return [], ["Dosyada satır bulunamadı."]

    date_idx = _match_column(header_row, DATE_HEADERS)
    desc_idx = _match_column(header_row, DESC_HEADERS)
    amount_idx = _match_column(header_row, AMOUNT_HEADERS)
    debit_idx = _match_column(header_row, DEBIT_HEADERS)
    credit_idx = _match_column(header_row, CREDIT_HEADERS)
    balance_idx = _match_column(header_row, BALANCE_HEADERS)

    if date_idx is None or (amount_idx is None and debit_idx is None and credit_idx is None):
        return [], [
            "Beklenen kolon başlıkları bulunamadı (Tarih / Tutar veya Borç-Alacak). "
            "İlk satırın başlık satırı olduğundan emin olun."
        ]

    for row_index, raw_row in enumerate(reader, start=2):
        if not raw_row or all(not (c or "").strip() for c in raw_row):
            continue
        try:
            def cell(idx):
                return raw_row[idx] if idx is not None and idx < len(raw_row) else None

            row = _row_from_fields(
                transaction_date=_parse_date(cell(date_idx)),
                description=cell(desc_idx),
                debit=_parse_amount(cell(debit_idx)),
                credit=_parse_amount(cell(credit_idx)),
                single_amount=_parse_amount(cell(amount_idx)),
                balance=_parse_amount(cell(balance_idx)),
                row_index=row_index,
            )
            if row is None:
                errors.append(f"Satır {row_index}: tutar okunamadı, atlandı.")
                continue
            rows.append(row)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Satır {row_index}: {exc}")

    return rows, errors


# --- PDF (best-effort) -------------------------------------------------------

_PDF_LINE_RE = re.compile(
    r"(?P<date>\d{2}[./]\d{2}[./]\d{2,4})\s+"
    r"(?P<desc>.+?)\s+"
    r"(?P<amount>-?\(?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})\)?)\s*"
    r"(?P<balance>-?\(?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})\)?)?$"
)


def parse_pdf(file) -> tuple[list[dict], list[str]]:
    """PDF banka ekstrelerini metin bazlı, satır-desenine dayalı (regex)
    olarak ayrıştırmayı DENER. Bu, tablo yapısını gerçek anlamda anlayan
    bir çözüm DEĞİLDİR -- her bankanın PDF düzeni farklı olduğu için en iyi
    çaba (best-effort) esasına dayanır. Ayrıştırılamayan satırlar `errors`
    listesine "atlandı" olarak eklenir; dosya hiç ayrıştırılamazsa boş
    liste + tek bir açıklayıcı hata döner."""
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover
        return [], [f"pdfplumber kütüphanesi yüklü değil: {exc}"]

    rows: list[dict] = []
    errors: list[str] = []
    row_index = 0
    try:
        with pdfplumber.open(file) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                for line in text.splitlines():
                    row_index += 1
                    line = line.strip()
                    if not line:
                        continue
                    match = _PDF_LINE_RE.match(line)
                    if not match:
                        continue
                    tx_date = _parse_date(match.group("date"))
                    amount = _parse_amount(match.group("amount"))
                    balance = _parse_amount(match.group("balance")) if match.group("balance") else None
                    if amount is None:
                        continue
                    direction = "debit" if amount < 0 else "credit"
                    rows.append({
                        "transaction_date": tx_date,
                        "description": match.group("desc").strip()[:500],
                        "amount": abs(amount),
                        "direction": direction,
                        "balance_after": balance,
                        "raw_row_index": row_index,
                    })
    except Exception as exc:  # noqa: BLE001
        errors.append(f"PDF dosyası okunamadı: {exc}")
        return [], errors

    if not rows:
        errors.append(
            "PDF içinden hiçbir işlem satırı otomatik olarak tanınamadı -- bu "
            "bankanın ekstre düzeni bu ayrıştırıcının desteklediği kalıpla "
            "eşleşmiyor olabilir. Excel/CSV dökümü varsa onu kullanmanız "
            "önerilir; yoksa satırları elle girebilirsiniz."
        )
    return rows, errors


def parse_statement_file(source_format: str, file) -> tuple[list[dict], list[str]]:
    """`BankStatementImport.SourceFormat` degerine gore dogru parser'i cagirir."""
    if source_format == "excel":
        return parse_excel(file)
    if source_format == "csv":
        return parse_csv(file)
    if source_format == "pdf":
        return parse_pdf(file)
    return [], [f"Bilinmeyen dosya formatı: {source_format}"]
