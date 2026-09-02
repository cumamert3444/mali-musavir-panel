// api.js — Django REST API (JWT) ile iletişim katmanı.
// Aynı origin üzerinden servis edildiği için baz URL boş bırakılabilir;
// window.__API_BASE__ ile lokal geliştirmede farklı bir adrese yönlendirilebilir.

const API_BASE = window.__API_BASE__ || "";

const TOKEN_KEY = "mmp_access_token";
const REFRESH_KEY = "mmp_refresh_token";
const OFFICE_KEY = "mmp_active_office_id";

export const tokenStore = {
  getAccess: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  setTokens: (access, refresh) => {
    if (access) localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
  getActiveOffice: () => localStorage.getItem(OFFICE_KEY),
  setActiveOffice: (officeId) => {
    if (officeId == null) localStorage.removeItem(OFFICE_KEY);
    else localStorage.setItem(OFFICE_KEY, String(officeId));
  },
};

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

let refreshPromise = null;

async function doRefresh() {
  const refresh = tokenStore.getRefresh();
  if (!refresh) throw new ApiError("Oturum bulunamadı", 401, null);
  const res = await fetch(`${API_BASE}/api/v1/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    tokenStore.clear();
    throw new ApiError("Oturum süresi doldu", 401, null);
  }
  const data = await res.json();
  tokenStore.setTokens(data.access, null);
  return data.access;
}

/**
 * Ana istek fonksiyonu. path örn: "/api/v1/clients/"
 * opts: { method, body, params, auth (default true), rawResponse }
 */
export async function apiRequest(path, opts = {}) {
  const { method = "GET", body, params, auth = true, isForm = false } = opts;

  let url = `${API_BASE}${path}`;
  if (params && Object.keys(params).length) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") qs.set(k, v);
    });
    const qsStr = qs.toString();
    if (qsStr) url += (url.includes("?") ? "&" : "?") + qsStr;
  }

  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";

  const activeOffice = tokenStore.getActiveOffice();
  if (activeOffice) headers["X-Office-Id"] = activeOffice;

  const doFetch = async () => {
    if (auth) {
      const access = tokenStore.getAccess();
      if (access) headers["Authorization"] = `Bearer ${access}`;
    }
    return fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  };

  let res = await doFetch();

  if (res.status === 401 && auth && tokenStore.getRefresh()) {
    try {
      if (!refreshPromise) refreshPromise = doRefresh().finally(() => (refreshPromise = null));
      await refreshPromise;
      res = await doFetch();
    } catch (e) {
      tokenStore.clear();
      window.location.hash = "";
      window.__mmpRouter && window.__mmpRouter.navigate("/login");
      throw e;
    }
  }

  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (e) {
      data = text;
    }
  }

  if (!res.ok) {
    const message = extractErrorMessage(data) || `İstek başarısız (${res.status})`;
    throw new ApiError(message, res.status, data);
  }

  return data;
}

export function extractErrorMessage(data) {
  if (!data) return null;
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  // DRF validation error: {field: [msg, ...]} ya da genel hata listesi
  const parts = [];
  for (const [key, val] of Object.entries(data)) {
    const msg = Array.isArray(val) ? val.join(" ") : String(val);
    parts.push(key === "non_field_errors" ? msg : `${key}: ${msg}`);
  }
  return parts.join(" · ") || null;
}

export const api = {
  get: (path, params) => apiRequest(path, { method: "GET", params }),
  post: (path, body) => apiRequest(path, { method: "POST", body }),
  patch: (path, body) => apiRequest(path, { method: "PATCH", body }),
  put: (path, body) => apiRequest(path, { method: "PUT", body }),
  del: (path) => apiRequest(path, { method: "DELETE" }),
};

export async function login(email, password) {
  const res = await fetch(`${API_BASE}/api/v1/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new ApiError(extractErrorMessage(data) || "E-posta veya şifre hatalı.", res.status, data);
  }
  tokenStore.setTokens(data.access, data.refresh);
  return data;
}

export function logout() {
  tokenStore.clear();
  tokenStore.setActiveOffice(null);
}

export function isAuthenticated() {
  return !!tokenStore.getAccess();
}
