// main.js — uygulama giriş noktası: router kurulumu + kimlik doğrulama koruması.
import { Router } from "./router.js";
import { isAuthenticated } from "./api.js";
import { loadMe } from "./state.js";
import { renderLanding } from "./pages/landing.js";
import { renderLogin } from "./pages/login.js";
import { renderRegister } from "./pages/register.js";
import { renderDashboard } from "./pages/dashboard.js";
import { renderAdmin } from "./pages/admin.js";
import { renderClients } from "./pages/clients.js";
import { renderClientDetail } from "./pages/clientDetail.js";
import { renderInvoices } from "./pages/invoices.js";
import { renderInvoiceDetail } from "./pages/invoiceDetail.js";
import { renderTasks } from "./pages/tasks.js";
import { renderDeclarations } from "./pages/declarations.js";
import { renderTaxDebts } from "./pages/taxDebts.js";
import { renderPosReports } from "./pages/posReports.js";
import { renderDocuments } from "./pages/documents.js";
import { renderLegalNotices } from "./pages/legalNotices.js";
import { renderTeam } from "./pages/team.js";
import { renderSettings } from "./pages/settings.js";
import { renderPrivacyPolicy, renderKvkk } from "./pages/legal.js";
import { renderThankYou, renderStatus } from "./pages/misc.js";
import { mountContactWidgets, unmountContactWidgets } from "./contactWidgets.js";

// "/" ve diger pazarlama/hukuki sayfalar herkese acik (giris yapmis olsa
// da olmasa da erisilebilir). "/login" ve "/register" ise SADECE giris
// yapmamis kullanicilar icindir -- girisli kullanici bunlara giderse
// /dashboard'a yonlendirilir. Diger her rota (varsayilan) kimlik
// dogrulama gerektirir.
const ALWAYS_PUBLIC_PATHS = ["/", "/gizlilik-politikasi", "/kvkk", "/tesekkurler", "/durum"];
const AUTH_ONLY_PATHS = ["/login", "/register"];
const SUPERADMIN_PATHS = ["/admin"];

async function boot() {
  const app = document.getElementById("app");
  const router = new Router(app);
  window.__mmpRouter = router;

  router.setBeforeEach(async (path) => {
    const isAlwaysPublic = ALWAYS_PUBLIC_PATHS.includes(path);
    const isAuthOnly = AUTH_ONLY_PATHS.includes(path);

    // Herkese açık pazarlama/hukuki sayfalarda WhatsApp kabarcık butonu +
    // mobil iletişim çubuğu görünür; girişli uygulama ekranlarında gizlenir.
    if (isAlwaysPublic || isAuthOnly) mountContactWidgets();
    else unmountContactWidgets();

    if (!isAuthenticated()) {
      if (isAlwaysPublic || isAuthOnly) return true;
      router.navigate("/login", { replace: true });
      return false;
    }
    // Girişli kullanıcı: /me bilgisi henüz yüklenmediyse yükle.
    try {
      const { state } = await import("./state.js");
      if (!state.me) await loadMe();
      if (SUPERADMIN_PATHS.includes(path) && !state.me?.is_superuser) {
        router.navigate("/dashboard", { replace: true });
        return false;
      }
    } catch (e) {
      const { logout } = await import("./api.js");
      logout();
      if (isAlwaysPublic || isAuthOnly) return true;
      router.navigate("/login", { replace: true });
      return false;
    }
    if (isAuthOnly) {
      router.navigate("/dashboard", { replace: true });
      return false;
    }
    return true;
  });

  router
    .add("/", renderLanding)
    .add("/login", renderLogin)
    .add("/register", renderRegister)
    .add("/dashboard", renderDashboard)
    .add("/admin", renderAdmin)
    .add("/clients", renderClients)
    .add("/clients/:id", renderClientDetail)
    .add("/invoices", renderInvoices)
    .add("/invoices/:id", renderInvoiceDetail)
    .add("/tasks", renderTasks)
    .add("/declarations", renderDeclarations)
    .add("/tax-debts", renderTaxDebts)
    .add("/pos-reports", renderPosReports)
    .add("/documents", renderDocuments)
    .add("/legal-notices", renderLegalNotices)
    .add("/team", renderTeam)
    .add("/settings", renderSettings)
    .add("/gizlilik-politikasi", renderPrivacyPolicy)
    .add("/kvkk", renderKvkk)
    .add("/tesekkurler", renderThankYou)
    .add("/durum", renderStatus)
    .setNotFound((el) => {
      document.title = "Sayfa Bulunamadı — Müşavir Asistanı";
      el.innerHTML = `
        <div class="auth-shell">
          <div class="auth-card" style="text-align:center;max-width:440px;">
            <div class="logo-badge" style="margin:0 auto 18px;width:64px;height:64px;font-size:24px;">404</div>
            <h1 style="margin:0 0 10px;">Sayfa Bulunamadı</h1>
            <p class="text-muted">Aradığınız sayfa taşınmış veya hiç var olmamış olabilir.</p>
            <p class="text-sm text-muted"><span id="notfound-countdown">5</span> saniye içinde ana sayfaya yönlendirileceksiniz.</p>
            <a href="/" data-link class="btn btn-primary">Hemen Ana Sayfaya Dön</a>
          </div>
        </div>
      `;
      let seconds = 5;
      const counterEl = el.querySelector("#notfound-countdown");
      const timer = setInterval(() => {
        seconds -= 1;
        if (counterEl) counterEl.textContent = String(Math.max(seconds, 0));
        if (seconds <= 0) {
          clearInterval(timer);
          if (window.location.pathname !== "/") router.navigate("/", { replace: true });
        }
      }, 1000);
    });

  router.start();
}

boot();
