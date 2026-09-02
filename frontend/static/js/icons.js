// icons.js — sade, tek renkli çizgi ikon seti (inline SVG, dış bağımlılık yok).

const wrap = (paths, viewBox = "0 0 24 24") =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;

export const icons = {
  dashboard: wrap('<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>'),
  clients: wrap('<circle cx="9" cy="7" r="3.2"/><path d="M2.5 20c0-3.6 2.9-6.2 6.5-6.2s6.5 2.6 6.5 6.2"/><circle cx="17.5" cy="8" r="2.6"/><path d="M15.5 13.5c2.9.3 5 2.6 5 6.5"/>'),
  invoice: wrap('<path d="M6 2.5h9l3 3V21a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 21z"/><path d="M15 2.5V6h3.5"/><path d="M9 12h6M9 15.5h6M9 8.5h3"/>'),
  task: wrap('<rect x="3.5" y="4" width="17" height="16.5" rx="2"/><path d="M8 2.5v3M16 2.5v3M3.5 9.5h17"/><path d="M8 13.5l2 2 4-4.2"/>'),
  declaration: wrap('<path d="M6 2.5h9l3 3V21a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 21z"/><path d="M15 2.5V6h3.5"/><path d="m9 13 1.8 1.8L14.5 11"/>'),
  team: wrap('<circle cx="8" cy="8" r="3"/><circle cx="17" cy="9" r="2.4"/><path d="M2.5 20c0-3.3 2.5-5.6 5.5-5.6s5.5 2.3 5.5 5.6"/><path d="M15.5 14.7c2.4.4 4 2.4 4 5.3"/>'),
  settings: wrap('<circle cx="12" cy="12" r="3"/><path d="M19.4 13.5a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.9 2.9l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V20a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.9-2.9l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H4a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.6-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.9-2.9l.1.1a1.7 1.7 0 0 0 1.9.3H10a1.7 1.7 0 0 0 1-1.6V4a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.9 2.9l-.1.1a1.7 1.7 0 0 0-.3 1.9V10a1.7 1.7 0 0 0 1.6 1H20a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.6 1z"/>'),
  logout: wrap('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>'),
  menu: wrap('<path d="M3.5 6h17M3.5 12h17M3.5 18h17"/>'),
  plus: wrap('<path d="M12 5v14M5 12h14"/>'),
  search: wrap('<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>'),
  back: wrap('<path d="m15 18-6-6 6-6"/>'),
  building: wrap('<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 7.5h1.5M8 11h1.5M8 14.5h1.5M14.5 7.5H16M14.5 11H16M14.5 14.5H16M10 21v-3.5h4V21"/>'),
  key: wrap('<circle cx="8" cy="15.5" r="4"/><path d="m10.9 12.6 8.6-8.6M15.5 5l2 2M18.5 2l2 2"/>'),
  alert: wrap('<path d="M12 3 2 20h20z"/><path d="M12 9.5v4.5M12 17h.01"/>'),
  bank: wrap('<path d="M3 10 12 4l9 6"/><path d="M4.5 10v9M9 10v9M15 10v9M19.5 10v9M2.5 21.5h19"/>'),
  document: wrap('<path d="M6 2.5h9l3 3V21a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 21z"/><path d="M15 2.5V6h3.5"/><path d="M9 11h6M9 14.5h6M9 17.5h4"/>'),
  ai: wrap('<path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/><circle cx="12" cy="12" r="3"/>'),
  chart: wrap('<path d="M3 20.5h18"/><path d="m4 16 5-5.5 4 3 6.5-7.5"/><path d="M15 6h4.5v4.5"/>'),
  scan: wrap('<path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16"/><path d="M4 12h16"/>'),
  shield: wrap('<path d="M12 2.5 4.5 5.5v6c0 5 3.2 7.8 7.5 9.5 4.3-1.7 7.5-4.5 7.5-9.5v-6z"/><path d="m9 12 2 2 4-4.2"/>'),
  chat: wrap('<path d="M3.5 12.5c0-5 4-8.5 8.7-8.5 4.9 0 8.8 3.4 8.8 8s-3.9 8-8.8 8c-1.1 0-2.2-.2-3.2-.5L4 20.5l1.3-3.8c-1.1-1.2-1.8-2.6-1.8-4.2z"/>'),
  crown: wrap('<path d="m3 8 3.5 3L12 5l5.5 6L21 8l-1.5 10h-15z"/>'),
  bell: wrap('<path d="M6 10a6 6 0 0 1 12 0c0 4 1.5 5.5 1.5 5.5h-15S6 14 6 10z"/><path d="M10 19a2 2 0 0 0 4 0"/>'),
};
