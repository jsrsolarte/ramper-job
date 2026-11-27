(() => {
  const panel = document.querySelector("[data-refresh-schedule]");
  if (!panel) return;

  const scheduleSummary = panel.querySelector("[data-refresh-schedule-summary]");
  const workSummary = panel.querySelector("[data-refresh-work-summary]");
  const lastStart = panel.querySelector("[data-refresh-last-start]");
  const dateFormatter = new Intl.DateTimeFormat("es-CO", {
    dateStyle: "full",
    timeStyle: "short",
    timeZone: "America/Bogota",
  });

  const appendTime = (container, isoValue, prefix) => {
    if (prefix) container.append(document.createTextNode(prefix));
    const date = new Date(isoValue);
    if (Number.isNaN(date.getTime())) return;
    const time = document.createElement("time");
    time.dateTime = date.toISOString();
    time.textContent = `${dateFormatter.format(date)} (hora local)`;
    container.append(time);
  };

  const renderSchedule = (status) => {
    scheduleSummary.replaceChildren();
    if (status.status === "paused") {
      scheduleSummary.textContent = "Las búsquedas automáticas están pausadas.";
      return;
    }
    if (status.status === "overdue" && status.next_at) {
      const strong = document.createElement("strong");
      strong.textContent = panel.dataset.administrator === "true"
        ? "Ciclo automático retrasado. "
        : "La búsqueda automática está retrasada. ";
      scheduleSummary.append(strong);
      appendTime(scheduleSummary, status.next_at, "Hora estimada vencida: ");
      return;
    }
    if (status.quiet_window) {
      scheduleSummary.textContent = panel.dataset.administrator === "true"
        ? "Pausa horaria activa. El trabajo automático se conserva y se reanuda al terminar la ventana."
        : "La pausa horaria está activa. Las búsquedas automáticas se reanudarán al terminar la ventana.";
      if (status.next_at) appendTime(scheduleSummary, status.next_at, " Próximo ciclo estimado: ");
      return;
    }
    if (status.next_at) {
      const prefix = panel.dataset.administrator === "true"
        ? "Próximo ciclo estimado: "
        : "Próxima búsqueda automática estimada: ";
      appendTime(scheduleSummary, status.next_at, prefix);
      return;
    }
    scheduleSummary.textContent = "El horario de la próxima búsqueda automática todavía no está disponible.";
  };

  const renderWork = (state) => {
    const applicant = panel.dataset.administrator !== "true";
    const labels = applicant
      ? {
          active: "Hay trabajo de búsqueda en curso, confirmado por su actividad reciente.",
          queued: "Hay trabajo de búsqueda pendiente o en cola.",
          uncertain: "Hay trabajo registrado, pero no se puede confirmar que siga en curso.",
          idle: "No hay una búsqueda en curso confirmada.",
          unavailable: "El estado del trabajo todavía no está disponible.",
        }
      : {
          active: "Búsqueda en curso con actividad confirmada.",
          queued: "Trabajo pendiente o en cola.",
          uncertain: "Hay trabajo registrado, pero su actividad es incierta.",
          idle: "No hay una búsqueda en curso confirmada.",
          unavailable: "El estado del trabajo todavía no está disponible.",
        };
    workSummary.textContent = labels[state] || labels.unavailable;
  };

  const renderLastStart = (value) => {
    if (!lastStart) return;
    lastStart.replaceChildren();
    if (value) appendTime(lastStart, value, "Último inicio registrado: ");
    else lastStart.textContent = "Todavía no hay un inicio de ciclo registrado.";
  };

  const refresh = async () => {
    try {
      const response = await fetch(panel.dataset.statusUrl, {
        credentials: "same-origin",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("status");
      const status = await response.json();
      renderSchedule(status);
      renderWork(status.work_state);
      renderLastStart(status.last_started_at);
    } catch (_error) {
      scheduleSummary.textContent = "No pudimos actualizar el estado; la información mostrada puede estar desactualizada.";
      workSummary.textContent = "El estado del trabajo no está actualizado.";
      if (lastStart) lastStart.textContent = "El último inicio no se pudo actualizar.";
    }
  };

  window.setInterval(refresh, 60_000);
})();
