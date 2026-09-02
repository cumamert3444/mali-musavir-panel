// main.js — uygulama giriş noktası: router kurulumu + kimlik doğrulama koruması.
import { Router } from "./router.js";
import { isAuthenticated } from "./api.js";
import { loadMe } from "./state.js";
import { renderLogin } from "./pages/login.js";
import { renderRegister } from "./pages/register.js";
import { renderDashboard } from "./pages/dashboard.js";
import { renderClients } from "./pages/clients.js";
import { renderClientDetail } from "./pages/clientDetail.js";
import { renderInvoices } from "./pages/invoices.js";
import { renderInvoiceDetail } from "./pages/invoiceDetail.js";
import { renderTasks } from "./pages/tasks.js";
import { renderDeclarations } from "./pages/declarations.js";
import { renderTeam } from "./pages/team.js";
import { renderSettings } from "./pages/settings.js";

const PUBLIC_PATHS = ["/login", "/register"];

async function boot() {
  const app = document.getElementById("app");
  const router = new Router(app);
  window.__mmpRouter = router;

  router.setBeforeEach(async (path) => {
    const isPublic = PUBLIC_PATHS.includes(path);
    if (!isAuthenticated()) {
      if (!isPublic) {
        router.navigate("/login", { replace: true });
        return false;
      }
      return true;
    }
    // Girişli kullanıcı: /me bilgisi henüz yüklenmediyse yükle.
    try {
      const { state } = await import("./state.js");
      if (!state.me) await loadMe();
    } catch (e) {
      const { logout } = await import("./api.js");
      logout();
      if (!isPublic) {
        router.navigate("/login", { replace: true });
        return false;
      }
      return true;
    }
    if (isPublic) {
      router.navigate("/", { replace: true });
      return false;
    }
    return true;
  });

  router
    .add("/login", renderLogin)
    .add("/register", renderRegister)
    .add("/", renderDashboard)
    .add("/clients", renderClients)
    .add("/clients/:id", renderClientDetail)
    .add("/invoices", renderInvoices)
    .add("/invoices/:id", renderInvoiceDetail)
    .add("/tasks", renderTasks)
    .add("/declarations", renderDeclarations)
    .add("/team", renderTeam)
    .add("/settings", renderSettings)
    .setNotFound((el) => {
      el.innerHTML = `
        <div class="auth-shell">
          <div class="auth-card" style="text-align:center;">
            <h1 style="margin-top:0;">404</h1>
            <p class="text-muted">Aradığınız sayfa bulunamadı.</p>
            <a href="/" data-link class="btn btn-primary">Panele Dön</a>
          </div>
        </div>
      `;
    });

  router.start();
}

boot();
