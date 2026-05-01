document.addEventListener("DOMContentLoaded", () => {
  const siteHeader = document.querySelector(".site-header");
  const menuToggle = document.querySelector(".menu-toggle");
  const headerPanel = document.querySelector(".header-panel");

  if (siteHeader && menuToggle && headerPanel) {
    const closeMenu = () => {
      siteHeader.classList.remove("menu-open");
      menuToggle.setAttribute("aria-expanded", "false");
    };

    menuToggle.addEventListener("click", () => {
      const isOpen = siteHeader.classList.toggle("menu-open");
      menuToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    headerPanel.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 720) {
          closeMenu();
        }
      });
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 720) {
        closeMenu();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeMenu();
      }
    });
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  };

  const captureLead = (form, data) => {
    if (!form.dataset.leadUrl) return Promise.resolve();
    const payload = new FormData();
    ["name", "phone", "city", "service", "details"].forEach((key) => {
      payload.set(key, data.get(key) || "");
    });
    payload.set("page_url", window.location.href);
    return fetch(form.dataset.leadUrl, {
      method: "POST",
      body: payload,
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      keepalive: true,
    }).catch(() => {});
  };

  const trackConversion = (eventType, label = "", extra = {}) => {
    const trackUrl = document.body.dataset.trackUrl || document.querySelector("[data-track-url]")?.dataset.trackUrl;
    if (!trackUrl) return Promise.resolve();
    const payload = new FormData();
    payload.set("event_type", eventType);
    payload.set("label", label);
    payload.set("page_url", window.location.href);
    Object.entries(extra).forEach(([key, value]) => payload.set(key, value || ""));
    return fetch(trackUrl, {
      method: "POST",
      body: payload,
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      keepalive: true,
    }).catch(() => {});
  };

  document.querySelectorAll(".quote-form[data-whatsapp]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(form);
      const lines = [
        "مرحبًا، أريد عرض سعر",
        `الاسم: ${data.get("name") || "-"}`,
        `المدينة: ${data.get("city") || "-"}`,
        `الخدمة: ${data.get("service") || "-"}`,
        `التفاصيل: ${data.get("details") || "-"}`,
      ];
      await captureLead(form, data);
      await trackConversion("whatsapp", "quote-form", { city: data.get("city"), service: data.get("service") });
      const url = `${form.dataset.whatsapp}?text=${encodeURIComponent(lines.join("\n"))}`;
      window.open(url, "_blank", "noopener");
    });
  });

  document.querySelectorAll(".conversion-mini-form[data-whatsapp]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(form);
      const city = data.get("city") || "-";
      const service = data.get("service") || "طلب خدمة";
      const message = [
        "مرحبًا، أريد عرض سعر سريع",
        `المدينة: ${city}`,
        `الخدمة: ${service}`,
        `الصفحة: ${window.location.href}`,
      ].join("\n");
      await captureLead(form, data);
      await trackConversion("whatsapp", "quick-bar", { city: data.get("city"), service: data.get("service") });
      window.open(`${form.dataset.whatsapp}?text=${encodeURIComponent(message)}`, "_blank", "noopener");
    });
  });

  document.querySelectorAll('a[href^="https://wa.me"]').forEach((link) => {
    link.addEventListener("click", () => trackConversion("whatsapp", link.textContent.trim()));
  });

  document.querySelectorAll('a[href^="tel:"]').forEach((link) => {
    link.addEventListener("click", () => trackConversion("call", link.textContent.trim()));
  });

  document.querySelectorAll("[data-cost-calculator]").forEach((form) => {
    const levelFactor = { basic: 0.85, standard: 1, premium: 1.35 };
    const minTarget = document.querySelector("[data-calc-min]");
    const maxTarget = document.querySelector("[data-calc-max]");
    const format = (value) => Math.round(value).toLocaleString("ar-SA");
    const update = () => {
      const data = new FormData(form);
      const area = Math.max(10, Number(data.get("area") || 100));
      const factor = levelFactor[data.get("level")] || 1;
      const minRate = Number(form.dataset.minRate || 180);
      const maxRate = Number(form.dataset.maxRate || 360);
      if (minTarget) minTarget.textContent = format(area * minRate * factor);
      if (maxTarget) maxTarget.textContent = format(area * maxRate * factor);
    };
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    form.addEventListener("submit", async () => {
      await trackConversion("calculator", "cost-calculator", {
        city: new FormData(form).get("city"),
        service: new FormData(form).get("service"),
      });
    });
    update();
  });

  const exitModal = document.querySelector("[data-exit-modal]");
  if (exitModal && !sessionStorage.getItem("exitIntentShown")) {
    const openExitModal = () => {
      sessionStorage.setItem("exitIntentShown", "1");
      exitModal.hidden = false;
      trackConversion("exit_intent", "shown");
    };
    document.addEventListener("mouseleave", (event) => {
      if (event.clientY <= 0 && !sessionStorage.getItem("exitIntentShown")) {
        openExitModal();
      }
    });
    setTimeout(() => {
      if (window.innerWidth <= 720 && !sessionStorage.getItem("exitIntentShown") && window.scrollY > 600) {
        openExitModal();
      }
    }, 18000);
    exitModal.querySelectorAll("[data-exit-close]").forEach((element) => {
      element.addEventListener("click", () => {
        exitModal.hidden = true;
      });
    });
  }

  document.querySelectorAll("[data-copy-link]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copyLink);
        button.textContent = "تم النسخ";
      } catch (error) {
        button.textContent = "تعذر النسخ";
      }
    });
  });

  const readingTarget = document.querySelector("[data-reading-target]");
  if (readingTarget && readingTarget.dataset.trackUrl) {
    const start = Date.now();
    const progressBar = document.querySelector("[data-reading-progress-bar]");

    const updateProgress = () => {
      if (!progressBar) return;
      const rect = readingTarget.getBoundingClientRect();
      const total = Math.max(1, readingTarget.offsetHeight - window.innerHeight);
      const consumed = Math.min(total, Math.max(0, window.scrollY - (readingTarget.offsetTop || 0)));
      const progress = Math.max(0, Math.min(100, (consumed / total) * 100));
      progressBar.style.width = `${progress}%`;
    };

    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
    updateProgress();

    window.addEventListener("beforeunload", () => {
      const seconds = Math.round((Date.now() - start) / 1000);
      if (seconds > 3) {
        fetch(`${readingTarget.dataset.trackUrl}?seconds=${seconds}`, { keepalive: true });
      }
    });
  }

  document.querySelectorAll("[data-before-after]").forEach((widget) => {
    const range = widget.querySelector("[data-before-range]");
    const layer = widget.querySelector("[data-before-layer]");
    const divider = widget.querySelector("[data-before-divider]");
    if (!range || !layer || !divider) return;

    const updateBeforeAfter = () => {
      const value = `${range.value}%`;
      layer.style.width = value;
      divider.style.insetInlineStart = value;
    };

    range.addEventListener("input", updateBeforeAfter);
    updateBeforeAfter();
  });
});
