// state.js — oturum boyunca bellekte tutulan basit uygulama durumu.
import { api, tokenStore } from "./api.js";

export const state = {
  me: null, // {id, email, first_name, last_name, memberships: [...]}
  office: null, // aktif Office detayı (OfficeSerializer)
};

export async function loadMe() {
  state.me = await api.get("/api/v1/accounts/me/");
  const memberships = (state.me.memberships || []).filter((m) => m.is_active);
  let activeId = tokenStore.getActiveOffice();
  if (!activeId || !memberships.some((m) => String(m.office) === String(activeId))) {
    if (memberships.length) {
      activeId = memberships[0].office;
      tokenStore.setActiveOffice(activeId);
    }
  }
  if (activeId) {
    try {
      state.office = await api.get("/api/v1/tenants/my-office/");
    } catch (e) {
      state.office = null;
    }
  }
  return state.me;
}

export function activeMembership() {
  if (!state.me) return null;
  const activeId = tokenStore.getActiveOffice();
  return (state.me.memberships || []).find((m) => String(m.office) === String(activeId)) || null;
}

export function isOwner() {
  const m = activeMembership();
  return !!m && m.role === "owner";
}

export function roleLabel(role) {
  const map = { owner: "Ofis Sahibi", accountant: "Mali Müşavir", bookkeeper: "Muhasebeci", intern: "Stajyer" };
  return map[role] || role;
}

export async function switchOffice(officeId) {
  tokenStore.setActiveOffice(officeId);
  state.office = await api.get("/api/v1/tenants/my-office/");
}
