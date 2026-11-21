(() => {
  const status = document.getElementById("connection-status");
  if (!status) return;

  const retryDelays = [5000, 10000, 20000, 30000];
  const recoveryMessageDuration = 5000;
  const probeTimeout = 4000;
  let previousState = "unknown";
  let consecutiveFailures = 0;
  let retryTimer = null;
  let recoveryTimer = null;
  let probeController = null;

  const show = (state, message) => {
    previousState = state;
    status.textContent = message;
    status.dataset.state = state;
    status.hidden = false;
  };

  const hide = () => {
    status.hidden = true;
    delete status.dataset.state;
  };

  const checkService = async () => {
    if (!navigator.onLine) return false;

    const controller = new AbortController();
    probeController = controller;
    const timeout = window.setTimeout(() => controller.abort(), probeTimeout);
    try {
      const response = await fetch("/healthz", {
        method: "GET",
        mode: "same-origin",
        credentials: "omit",
        cache: "no-store",
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) return false;
      const result = await response.json();
      return result.status === "ok";
    } catch (_error) {
      return false;
    } finally {
      window.clearTimeout(timeout);
      if (probeController === controller) probeController = null;
    }
  };

  const scheduleRetry = () => {
    if (!navigator.onLine || retryTimer !== null) return;
    const delay = retryDelays[Math.min(consecutiveFailures, retryDelays.length - 1)];
    consecutiveFailures += 1;
    retryTimer = window.setTimeout(() => {
      retryTimer = null;
      checkAvailability();
    }, delay);
  };

  async function checkAvailability() {
    if (!navigator.onLine) {
      show("offline", "No hay conexión de red. Jobs necesita conexión y no podemos garantizar que se guarden los cambios.");
      return;
    }

    const available = await checkService();
    if (!available) {
      show("unavailable", "No podemos contactar Jobs. Tu conexión de red puede seguir activa; no podemos garantizar que se guarden los cambios.");
      scheduleRetry();
      return;
    }

    consecutiveFailures = 0;
    if (retryTimer !== null) {
      window.clearTimeout(retryTimer);
      retryTimer = null;
    }
    if (recoveryTimer !== null) window.clearTimeout(recoveryTimer);

    if (previousState === "offline" || previousState === "unavailable") {
      show("recovered", "Se recuperó el acceso a Jobs. Verifica cualquier operación que no alcanzó confirmación antes de repetirla.");
      recoveryTimer = window.setTimeout(() => {
        recoveryTimer = null;
        hide();
      }, recoveryMessageDuration);
    } else {
      hide();
    }
  }

  window.addEventListener("offline", () => {
    if (retryTimer !== null) {
      window.clearTimeout(retryTimer);
      retryTimer = null;
    }
    if (recoveryTimer !== null) {
      window.clearTimeout(recoveryTimer);
      recoveryTimer = null;
    }
    probeController?.abort();
    show("offline", "No hay conexión de red. Jobs necesita conexión y no podemos garantizar que se guarden los cambios.");
  });

  window.addEventListener("online", () => {
    if (retryTimer !== null) {
      window.clearTimeout(retryTimer);
      retryTimer = null;
    }
    consecutiveFailures = 0;
    checkAvailability();
  });

  checkAvailability();
})();
