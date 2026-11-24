// An immutable page channel prevents cookies or another tab from silently
// switching simulated requests into live calls (or vice versa).
(() => {
  const live = document.body.dataset.live === "true";
  const channel = live ? "live" : "demo";
  const banner = document.querySelector(".demo-banner");
  if (banner) new ResizeObserver(() => {
    document.body.style.setProperty("--deployment-banner-height", `${banner.getBoundingClientRect().height}px`);
  }).observe(banner);
  const paths = new Set(["/generate", "/discover", "/ask", "/pdf", "/investment/pdf", "/finance"]);
  const fetchOriginal = window.fetch.bind(window);
  window.fetch = async (input, options = {}) => {
    const url = new URL(typeof input === "string" ? input : input.url, location.href);
    if (url.origin !== location.origin || !paths.has(url.pathname)) return fetchOriginal(input, options);
    const headers = new Headers(options.headers || (input instanceof Request ? input.headers : undefined));
    headers.set("X-Khotwa-Channel", channel);
    try {
      const response = await fetchOriginal(input, { ...options, headers });
      if (live && ["/generate", "/discover", "/ask"].includes(url.pathname)) {
        const status = document.getElementById("delivery-status");
        status.dataset.en = response.ok
          ? "Live Groq response received. Guidance is unverified; built-in examples remain examples."
          : "Live AI request failed or access expired. No simulated AI response was substituted. Local fallback guidance, if shown, is not live AI.";
        status.dataset.ar = response.ok
          ? "تم استلام رد حي من Groq. الإرشاد غير متحقق، وتبقى الأمثلة المدمجة أمثلة."
          : "فشل الطلب الحي أو انتهى الوصول. لم يُستبدل برد ذكاء اصطناعي محاكى. الإرشاد المحلي البديل، إن ظهر، ليس ذكاء اصطناعيا حيا.";
        status.textContent = status.dataset[document.documentElement.lang === "ar" ? "ar" : "en"];
        try {
          const value = await response.clone().json();
          const calls = value._deployment_metrics?.provider_calls || [];
          document.getElementById("live-metrics").textContent = calls.length
            ? calls.map((c) => `${c.kind}: HTTP ${c.http_status ?? "unknown"}; finish ${c.finish_reason ?? "unknown"}; ${c.completion_tokens ?? "?"} completion tokens; ${c.duration_ms} ms`).join(" · ")
            : "No provider request was completed for this response. / لم يكتمل طلب للمزود لهذا الرد.";
        } catch { /* Diagnostics cannot replace or break the actual response. */ }
      }
      return response;
    } catch (error) {
      if (live) {
        const status = document.getElementById("delivery-status");
        status.dataset.en = "Live AI connection failed. No simulated AI response was substituted.";
        status.dataset.ar = "فشل اتصال الذكاء الاصطناعي الحي. لم يُستبدل برد محاكى.";
        status.textContent = status.dataset[document.documentElement.lang === "ar" ? "ar" : "en"];
      }
      throw error;
    }
  };
})();
