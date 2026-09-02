// toast.js — kısa ömürlü bildirim mesajları.
import { escapeHtml } from "./format.js";

let stack = null;

function ensureStack() {
  if (!stack) {
    stack = document.createElement("div");
    stack.className = "toast-stack";
    document.body.appendChild(stack);
  }
  return stack;
}

export function toast(message, type = "default") {
  const el = document.createElement("div");
  el.className = "toast" + (type === "error" ? " toast-error" : type === "success" ? " toast-success" : "");
  el.innerHTML = escapeHtml(message);
  ensureStack().appendChild(el);
  setTimeout(() => {
    el.style.transition = "opacity 0.25s";
    el.style.opacity = "0";
    setTimeout(() => el.remove(), 250);
  }, 3200);
}

export function toastError(err) {
  toast(err && err.message ? err.message : "Bir hata oluştu.", "error");
}
