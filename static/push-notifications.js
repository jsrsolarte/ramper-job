(() => {
  const csrfToken = () => document.querySelector("#push-csrf [name=csrfmiddlewaretoken]")?.value
    || document.querySelector("[data-push-logout] [name=csrfmiddlewaretoken]")?.value
    || "";

  const postJson = (url, body) => fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
    body: JSON.stringify(body),
  });

  const readExistingSubscription = async () => {
    if (!("serviceWorker" in navigator)) return null;
    const registration = await navigator.serviceWorker.getRegistration("/");
    return registration ? registration.pushManager.getSubscription() : null;
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-push-preferences]").forEach((panel) => {
      const enable = panel.querySelector("[data-push-enable]");
      const disable = panel.querySelector("[data-push-disable]");
      const status = panel.querySelector("[data-push-status]");
      const supported = "Notification" in window
        && "serviceWorker" in navigator
        && "PushManager" in window;
      const configured = panel.dataset.enabled === "true" && Boolean(panel.dataset.publicKey);

      if (!supported) {
        enable.disabled = true;
        status.textContent = "Este navegador no ofrece notificaciones push. El indicador dentro de la aplicación sigue disponible.";
        return;
      }
      if (!configured) {
        enable.disabled = true;
        status.textContent = "El resumen diario todavía no está configurado en este entorno. El indicador dentro de la aplicación sigue disponible.";
      }

      const showActive = (active) => {
        enable.hidden = active;
        disable.hidden = !active;
        if (active) {
          status.textContent = configured
            ? "El resumen diario está activado en este dispositivo. La entrega depende del navegador y el sistema."
            : "Este dispositivo conserva una suscripción, pero el entorno no tiene el envío configurado. Puedes desactivarla aquí.";
        }
      };

      readExistingSubscription().then(async (subscription) => {
        if (!subscription) return;
        const response = await postJson(panel.dataset.statusUrl, { endpoint: subscription.endpoint });
        if (response.ok) showActive(Boolean((await response.json()).active));
      }).catch(() => {});

      enable.addEventListener("click", async () => {
        if (!configured || enable.disabled) return;
        enable.disabled = true;
        try {
          let permission = Notification.permission;
          if (permission === "default") permission = await Notification.requestPermission();
          if (permission !== "granted") {
            status.textContent = permission === "denied"
              ? "El permiso está denegado en este navegador. Puedes seguir viendo novedades dentro de la aplicación."
              : "No se concedió el permiso. Puedes seguir viendo novedades dentro de la aplicación.";
            return;
          }
          const registration = await navigator.serviceWorker.register(panel.dataset.workerUrl, {
            scope: "/",
            updateViaCache: "none",
          });
          const existing = await registration.pushManager.getSubscription();
          const subscription = existing || await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: decodeBase64Url(panel.dataset.publicKey),
          });
          const response = await postJson(panel.dataset.subscriptionUrl, {
            subscription: subscription.toJSON(),
          });
          if (!response.ok) throw new Error("No se pudo registrar este dispositivo.");
          showActive(true);
        } catch (_error) {
          status.textContent = "No se pudo activar el resumen en este momento. El indicador dentro de la aplicación sigue disponible.";
        } finally {
          enable.disabled = false;
        }
      });

      disable.addEventListener("click", async () => {
        disable.disabled = true;
        try {
          const subscription = await readExistingSubscription();
          if (subscription) {
            const response = await postJson(panel.dataset.subscriptionUrl, {
              action: "unsubscribe",
              endpoint: subscription.endpoint,
            });
            if (!response.ok) throw new Error("No se pudo actualizar el servidor.");
            await subscription.unsubscribe();
          }
          showActive(false);
          status.textContent = "El resumen diario está desactivado en este dispositivo. El indicador dentro de la aplicación sigue disponible.";
        } catch (_error) {
          status.textContent = "No se pudo confirmar la desactivación. Vuelve a intentarlo cuando tengas conexión.";
        } finally {
          disable.disabled = false;
        }
      });
    });

    document.querySelectorAll("form[data-push-logout]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        if (form.dataset.pushReady === "true") return;
        event.preventDefault();
        readExistingSubscription().then((subscription) => {
          const endpointField = form.querySelector("[data-push-logout-endpoint]");
          if (subscription && endpointField) endpointField.value = subscription.endpoint;
        }).catch(() => {}).finally(() => {
          form.dataset.pushReady = "true";
          form.submit();
        });
      });
    });
  });

  function decodeBase64Url(value) {
    const padded = value.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(value.length / 4) * 4, "=");
    return Uint8Array.from(atob(padded), (character) => character.charCodeAt(0));
  }
})();
