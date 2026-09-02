// modal.js — basit, tek örnekli modal yardımcıları.

export function openModal({ title, bodyHtml, footerHtml = "", onMount, onClose }) {
  closeModal();
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "mmp-modal-overlay";
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h2>${title}</h2>
        <button class="modal-close" type="button" aria-label="Kapat">&times;</button>
      </div>
      <div class="modal-body">${bodyHtml}</div>
      ${footerHtml ? `<div class="modal-footer">${footerHtml}</div>` : ""}
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener("mousedown", (e) => {
    if (e.target === overlay) closeModal();
  });
  overlay.querySelector(".modal-close").addEventListener("click", () => closeModal());
  document.addEventListener("keydown", escListener);
  if (onClose) overlay._onClose = onClose;
  if (onMount) onMount(overlay.querySelector(".modal"));
  return overlay;
}

function escListener(e) {
  if (e.key === "Escape") closeModal();
}

export function closeModal() {
  const existing = document.getElementById("mmp-modal-overlay");
  if (existing) {
    if (existing._onClose) existing._onClose();
    existing.remove();
  }
  document.removeEventListener("keydown", escListener);
}

export function confirmDialog(message) {
  return new Promise((resolve) => {
    openModal({
      title: "Onay Gerekiyor",
      bodyHtml: `<p style="margin:0;">${message}</p>`,
      footerHtml: `
        <button class="btn btn-secondary" data-act="cancel">Vazgeç</button>
        <button class="btn btn-danger" data-act="ok">Evet, Onaylıyorum</button>
      `,
      onMount: (modal) => {
        modal.querySelector('[data-act="cancel"]').addEventListener("click", () => {
          closeModal();
          resolve(false);
        });
        modal.querySelector('[data-act="ok"]').addEventListener("click", () => {
          closeModal();
          resolve(true);
        });
      },
    });
  });
}
