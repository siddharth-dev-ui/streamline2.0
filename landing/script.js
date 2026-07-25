(() => {
  const root = document.documentElement;
  const nav = document.getElementById("nav");
  const themeToggle = document.getElementById("themeToggle");
  const menuToggle = document.getElementById("menuToggle");
  const mobileMenu = document.getElementById("mobileMenu");
  const year = document.getElementById("year");

  const stored = localStorage.getItem("streamline-landing-theme");
  const preferred = stored || "dark";
  root.setAttribute("data-theme", preferred);

  // Streamlit embeds iframe content where scroll IO / CSS animations often fail.
  // Opacity animations with fill-mode:both can leave text permanently invisible.
  if (window.STREAMLIT_EMBED) {
    root.classList.add("streamlit-embed");
    document.body?.classList.add("streamlit-embed");
    const unlock = () => {
      document.querySelectorAll(".reveal").forEach((el) => {
        el.classList.add("visible");
        el.style.opacity = "1";
        el.style.transform = "none";
        el.style.animation = "none";
      });
      document
        .querySelectorAll(".brand-mark, .hero-sub, .hero-cta, .chat-bubble, .rec-item, .eyebrow")
        .forEach((el) => {
          el.style.opacity = "1";
          el.style.transform = "none";
          el.style.animation = "none";
        });
    };
    unlock();
    requestAnimationFrame(unlock);
  }

  if (year) year.textContent = String(new Date().getFullYear());

  themeToggle?.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("streamline-landing-theme", next);
  });

  const onScroll = () => {
    if (!nav) return;
    nav.classList.toggle("scrolled", window.scrollY > 12);

    // Subtle hero atmosphere parallax (skipped in embeds / reduced motion)
    if (
      !window.STREAMLIT_EMBED &&
      !window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      const y = Math.min(window.scrollY, 420);
      document.querySelectorAll(".hero-orb").forEach((orb, i) => {
        const factor = (i + 1) * 0.012;
        orb.style.translate = `0 ${y * factor}px`;
      });
    }
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  menuToggle?.addEventListener("click", () => {
    const open = mobileMenu?.hasAttribute("hidden") ?? true;
    if (!mobileMenu || !menuToggle) return;
    if (open) {
      mobileMenu.hidden = false;
      mobileMenu.classList.add("open");
      menuToggle.setAttribute("aria-expanded", "true");
    } else {
      mobileMenu.classList.remove("open");
      mobileMenu.hidden = true;
      menuToggle.setAttribute("aria-expanded", "false");
    }
  });

  mobileMenu?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      mobileMenu.classList.remove("open");
      mobileMenu.hidden = true;
      menuToggle?.setAttribute("aria-expanded", "false");
    });
  });

  // Resolve app links for static server, Streamlit local, and Streamlit Cloud
  const appBase = (() => {
    const { protocol, hostname, port } = window.location;
    if (window.STREAMLIT_EMBED) return "";
    if (protocol === "file:") return "http://localhost:8501";
    if (port === "8501") return "";
    if (hostname.endsWith("streamlit.app")) return "";
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return port === "8080" ? "http://localhost:8501" : "";
    }
    return "";
  })();

  document.querySelectorAll('a[href^="../"], a[href*="app=1"]').forEach((anchor) => {
    if (anchor.hasAttribute("data-enter-app")) return;
    const href = anchor.getAttribute("href") || "";
    if (window.STREAMLIT_EMBED || appBase === "") {
      // Hash target avoids flashing the iframe if navigation is sandboxed.
      anchor.setAttribute("href", "#enter-app");
      anchor.setAttribute("data-enter-app", "1");
      return;
    }
    if (appBase.startsWith("http")) {
      const path = href.replace(/^\.\./, "") || "/?app=1";
      anchor.setAttribute("href", `${appBase}${path.startsWith("/") ? path : `/${path}`}`);
    }
  });

  if (window.STREAMLIT_EMBED) {
    const enterFromEmbed = (event) => {
      if (window.streamlineEnterApp) {
        window.streamlineEnterApp(event);
        return;
      }
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      try {
        window.parent.postMessage({ type: "streamline-enter-app" }, "*");
      } catch (err) {}
      try {
        const parentDoc = window.parent.document;
        let link = parentDoc.getElementById("streamline-enter-app-link");
        const url = new URL(window.parent.location.href);
        url.searchParams.set("app", "1");
        url.searchParams.delete("landing");
        if (!link) {
          link = parentDoc.createElement("a");
          link.id = "streamline-enter-app-link";
          link.style.display = "none";
          parentDoc.body.appendChild(link);
        }
        link.setAttribute("href", url.toString());
        link.click();
      } catch (err) {}
    };

    document.querySelectorAll("[data-enter-app]").forEach((el) => {
      el.addEventListener("click", enterFromEmbed);
    });
    window.streamlineEnterApp = window.streamlineEnterApp || enterFromEmbed;
  }

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );

  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

  // Failsafe: if nothing revealed after a moment (common in Streamlit iframes), show all.
  setTimeout(() => {
    const revealed = document.querySelectorAll(".reveal.visible").length;
    const total = document.querySelectorAll(".reveal").length;
    if (window.STREAMLIT_EMBED || (total > 0 && revealed === 0)) {
      document.documentElement.classList.add("streamlit-embed");
      document.body?.classList.add("streamlit-embed");
      document.querySelectorAll(".reveal").forEach((el) => el.classList.add("visible"));
    }
  }, 600);

  // —— Live demo recommendation ——
  const demoForm = document.getElementById("demoForm");
  const demoTicker = document.getElementById("demoTicker");
  const demoSubmit = document.getElementById("demoSubmit");
  const demoStatus = document.getElementById("demoStatus");
  const chatThread = document.getElementById("chatThread");

  const escapeHtml = (value) =>
    String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");

  const renderRecommendation = (data) => {
    if (!chatThread) return;
    chatThread.innerHTML = `
      <div class="chat-bubble chat-user">
        <span class="chat-label">You</span>
        <p>${escapeHtml(data.query || `Should I buy ${data.ticker}?`)}</p>
      </div>
      <div class="chat-bubble chat-ai">
        <span class="chat-label">AI · ${escapeHtml(data.company || data.ticker)}</span>
        <div class="rec-header">
          <div>
            <span class="rec-kicker">Recommendation</span>
            <strong class="rec-verdict">${escapeHtml(data.recommendation)}</strong>
          </div>
          <div class="rec-confidence">
            <span>Confidence</span>
            <strong>${escapeHtml(String(data.confidence))}%</strong>
            <div class="confidence-bar"><i style="--w: ${Number(data.confidence) || 0}%"></i></div>
          </div>
        </div>
        <div class="rec-grid">
          <div class="rec-item">
            <span class="rec-item-label">Technical Analysis</span>
            <strong>${escapeHtml(data.technical_label)}</strong>
            <p>${escapeHtml(data.technical_detail)}</p>
          </div>
          <div class="rec-item">
            <span class="rec-item-label">Fundamental Analysis</span>
            <strong>${escapeHtml(data.fundamental_label)}</strong>
            <p>${escapeHtml(data.fundamental_detail)}</p>
          </div>
          <div class="rec-item rec-item-full">
            <span class="rec-item-label">Risk</span>
            <strong>${escapeHtml(data.risk_label)}</strong>
            <p>Why it matters: ${escapeHtml(data.risk_detail)}</p>
          </div>
        </div>
        <p class="demo-hint">${escapeHtml(data.disclaimer || "Live demo using market data. Educational only — not financial advice.")}</p>
      </div>
    `;
  };

  const setDemoLoading = (loading, message = "") => {
    if (demoSubmit) {
      demoSubmit.disabled = loading;
      demoSubmit.textContent = loading ? "Analyzing…" : "Analyze";
    }
    if (demoTicker) demoTicker.disabled = loading;
    if (demoStatus) {
      demoStatus.textContent = message;
      demoStatus.classList.toggle("is-error", Boolean(message) && !loading && message !== "Fetching live market data…");
    }
  };

  demoForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = (demoTicker?.value || "").trim();
    if (!query) return;

    setDemoLoading(true, "Fetching live market data…");
    if (chatThread) {
      chatThread.innerHTML = `
        <div class="chat-bubble chat-user">
          <span class="chat-label">You</span>
          <p>Should I buy ${escapeHtml(query.toUpperCase())}?</p>
        </div>
        <div class="chat-bubble chat-ai chat-loading">
          <span class="chat-label">AI</span>
          <p>Reading prices, trends, and fundamentals…</p>
        </div>
      `;
    }

    try {
      // Prefer local landing demo server; on Streamlit Cloud there is no :8080 API.
      const onDemoServer =
        window.location.port === "8080" ||
        window.location.port === "80" ||
        /landing/i.test(window.location.pathname);
      const apiBase = onDemoServer && !window.STREAMLIT_EMBED ? "" : null;

      if (apiBase === null) {
        throw new Error(
          "Live demo API isn’t available inside Streamlit Cloud. Click Enter Streamline to use the full app."
        );
      }

      const response = await fetch(
        `${apiBase}/api/recommend?q=${encodeURIComponent(query)}`
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Request failed");
      }
      renderRecommendation(data);
      setDemoLoading(false, data.price != null ? `Live price ≈ $${Number(data.price).toFixed(2)}` : "");
      demoTicker.value = data.ticker || query.toUpperCase();
    } catch (err) {
      setDemoLoading(false, err.message || "Something went wrong.");
      if (chatThread) {
        const cloudHint = window.STREAMLIT_EMBED
          ? `<p class="demo-hint"><a href="?app=1" data-enter-app="1" onclick="window.streamlineEnterApp && window.streamlineEnterApp(event)">Enter Streamline</a> to run full analysis.</p>`
          : `<p class="demo-hint">Make sure the landing demo server is running (<code>python landing/server.py</code>), then try again.</p>`;
        chatThread.innerHTML = `
          <div class="chat-bubble chat-user">
            <span class="chat-label">You</span>
            <p>Should I buy ${escapeHtml(query.toUpperCase())}?</p>
          </div>
          <div class="chat-bubble chat-ai">
            <span class="chat-label">AI</span>
            <p class="demo-error">${escapeHtml(err.message || "Unable to analyze that ticker right now.")}</p>
            ${cloudHint}
          </div>
        `;
      }
    }
  });
})();
