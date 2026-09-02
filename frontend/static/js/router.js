// router.js — History API tabanlı minimal istemci-taraflı yönlendirici.

export class Router {
  constructor(rootEl) {
    this.rootEl = rootEl;
    this.routes = []; // {pattern: RegExp, keys: [], render: fn}
    this.notFound = null;
    this.beforeEach = null;
    window.addEventListener("popstate", () => this._render());
    document.addEventListener("click", (e) => {
      const a = e.target.closest("a[data-link]");
      if (!a) return;
      const href = a.getAttribute("href");
      if (!href || href.startsWith("http") || a.target === "_blank") return;
      e.preventDefault();
      this.navigate(href);
    });
  }

  add(path, render) {
    const keys = [];
    const pattern = new RegExp(
      "^" +
        path
          .replace(/\/+$/, "")
          .split("/")
          .map((seg) => {
            if (seg.startsWith(":")) {
              keys.push(seg.slice(1));
              return "([^/]+)";
            }
            return seg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
          })
          .join("/") +
        "/?$"
    );
    this.routes.push({ pattern, keys, render });
    return this;
  }

  setNotFound(render) {
    this.notFound = render;
    return this;
  }

  setBeforeEach(fn) {
    this.beforeEach = fn;
    return this;
  }

  navigate(path, { replace = false } = {}) {
    if (replace) window.history.replaceState({}, "", path);
    else window.history.pushState({}, "", path);
    this._render();
  }

  start() {
    this._render();
  }

  async _render() {
    const path = window.location.pathname || "/";
    if (this.beforeEach) {
      const allowed = await this.beforeEach(path);
      if (allowed === false) return;
    }
    for (const route of this.routes) {
      const m = path.replace(/\/+$/, "") || "/";
      const match = (m === "" ? "/" : m).match(route.pattern);
      if (match) {
        const params = {};
        route.keys.forEach((k, i) => (params[k] = decodeURIComponent(match[i + 1])));
        this._current = route;
        await route.render(this.rootEl, params);
        this._highlightNav(path);
        return;
      }
    }
    if (this.notFound) {
      await this.notFound(this.rootEl);
    }
  }

  _highlightNav(path) {
    document.querySelectorAll(".sidebar-nav a[data-nav]").forEach((a) => {
      const base = a.getAttribute("data-nav");
      const active = base === "/" ? path === "/" : path.startsWith(base);
      a.classList.toggle("active", active);
    });
  }
}
