// Currency presentation only; the server's Decimal strings remain authoritative.
function formatAED(value) {
  let number = Number(value);
  if (Math.abs(number) < 0.005) number = 0;
  const formatted =
    new Intl.NumberFormat("en-AE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(number) + " AED";
  // Isolate Latin currency runs so RTL does not move a minus sign to the end.
  return lang === "ar" ? "\u2066" + formatted + "\u2069" : formatted;
}

function localizedStatus(id, en, ar) {
  const node = document.getElementById(id);
  if (!node) return;
  node.dataset.statusEn = en;
  node.dataset.statusAr = ar;
  node.textContent = lang === "ar" ? ar : en;
}
function relocalizeStatuses() {
  document.querySelectorAll("[data-status-en]").forEach((node) => {
    node.textContent =
      lang === "ar" ? node.dataset.statusAr : node.dataset.statusEn;
  });
}
