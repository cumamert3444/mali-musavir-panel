// format.js — para, tarih ve durum rozeti biçimlendirme yardımcıları.

export function money(value) {
  const n = Number(value || 0);
  return n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " ₺";
}

export function dateTR(value) {
  if (!value) return "—";
  const d = new Date(value.length === 10 ? value + "T00:00:00" : value);
  if (isNaN(d)) return value;
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function datetimeTR(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d)) return value;
  return d.toLocaleString("tr-TR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function daysUntil(dateStr) {
  if (!dateStr) return null;
  const target = new Date(dateStr.length === 10 ? dateStr + "T00:00:00" : dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target - today) / 86400000);
}

export function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const STATUS_BADGES = {
  // Client
  prospect: ["Potansiyel", "gray"],
  active: ["Aktif", "green"],
  passive: ["Pasif", "amber"],
  former: ["Eski Müşteri", "red"],
  // Task
  todo: ["Yapılacak", "gray"],
  in_progress: ["Devam Ediyor", "blue"],
  review: ["Kontrol Bekliyor", "amber"],
  done: ["Tamamlandı", "green"],
  // Declaration
  pending: ["Bekliyor", "gray"],
  submitted: ["Beyan Edildi", "blue"],
  paid: ["Ödendi", "green"],
  overdue: ["Gecikti", "red"],
  not_applicable: ["Geçersiz", "gray"],
  // Invoice
  draft: ["Taslak", "gray"],
  sent: ["Gönderildi", "blue"],
  partially_paid: ["Kısmen Ödendi", "amber"],
  canceled: ["İptal", "red"],
  // Priority
  low: ["Düşük", "gray"],
  normal: ["Normal", "blue"],
  high: ["Yüksek", "amber"],
  urgent: ["Acil", "red"],
};

export function statusBadge(code) {
  const [label, color] = STATUS_BADGES[code] || [code || "—", "gray"];
  return `<span class="badge badge-${color}">${escapeHtml(label)}</span>`;
}

export function legalTypeLabel(code) {
  const map = {
    sahis: "Şahıs İşletmesi",
    ltd: "Limited Şirket",
    as: "Anonim Şirket",
    adi_ortaklik: "Adi Ortaklık",
    kooperatif: "Kooperatif",
    dernek_vakif: "Dernek / Vakıf",
    serbest_meslek: "Serbest Meslek Erbabı",
    diger: "Diğer",
  };
  return map[code] || code;
}
