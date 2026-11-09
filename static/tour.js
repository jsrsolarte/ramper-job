document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.querySelector("#guided-tour");
  if (!dialog) return;

  const offer = document.querySelector("#tour-offer");
  const title = document.querySelector("#tour-title");
  const description = document.querySelector("#tour-description");
  const progressLabel = document.querySelector("#tour-progress");
  const previousButton = dialog.querySelector('[data-tour-action="previous"]');
  const nextButton = dialog.querySelector('[data-tour-action="next"]');
  const csrfToken = document.querySelector("#tour-csrf [name=csrfmiddlewaretoken]")?.value || "";
  let highlightedElement = null;
  let returnFocus = null;
  let activeState = null;

  const removeHighlight = () => {
    highlightedElement?.classList.remove("tour-highlight");
    highlightedElement = null;
  };

  const hideDialog = (restoreFocus = false) => {
    dialog.hidden = true;
    removeHighlight();
    if (restoreFocus && returnFocus?.isConnected) returnFocus.focus();
  };

  const findTarget = (step) => {
    const target = document.querySelector(`[data-tour="${step.target}"]`);
    if (target && target.getClientRects().length) return target;
    if (step.fallback_target) {
      const fallback = document.querySelector(`[data-tour="${step.fallback_target}"]`);
      if (fallback && fallback.getClientRects().length) return fallback;
    }
    return null;
  };

  const showStep = (state) => {
    const step = state.step;
    if (!step) {
      hideDialog(true);
      return;
    }
    if (window.location.pathname !== new URL(step.url, window.location.origin).pathname) {
      window.location.assign(step.url);
      return;
    }

    offer.hidden = true;
    removeHighlight();
    const target = findTarget(step);
    if (target) {
      highlightedElement = target;
      target.classList.add("tour-highlight");
      target.scrollIntoView({
        behavior: "instant",
        block: "center",
      });
    }

    title.textContent = step.title;
    description.textContent = step.text;
    progressLabel.textContent = `Paso ${state.step_index} de ${state.step_count}`;
    previousButton.disabled = state.step_index <= 1;
    nextButton.textContent = state.step_index >= state.step_count ? "Terminar" : "Siguiente";
    dialog.style.removeProperty("top");
    dialog.style.removeProperty("bottom");
    dialog.hidden = false;
    if (target) {
      const targetRect = target.getBoundingClientRect();
      const dialogHeight = dialog.offsetHeight;
      const margin = 16;
      const roomBelow = window.innerHeight - targetRect.bottom - margin;
      const roomAbove = targetRect.top - margin;
      let top;
      if (roomBelow >= dialogHeight) {
        top = targetRect.bottom + margin;
      } else if (roomAbove >= dialogHeight) {
        top = targetRect.top - dialogHeight - margin;
      } else {
        top = Math.max(margin, Math.min(window.innerHeight - dialogHeight - margin, targetRect.top - dialogHeight - margin));
      }
      dialog.style.top = `${top}px`;
      dialog.style.bottom = "auto";
    }
    nextButton.focus();
  };

  const postAction = async (action) => {
    const body = new URLSearchParams({ action });
    const response = await fetch(dialog.dataset.actionUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body,
    });
    const state = await response.json();
    if (!response.ok) throw new Error(state.error || "No se pudo guardar el recorrido.");
    activeState = state;
    return state;
  };

  const perform = async (action) => {
    try {
      const state = await postAction(action);
      if (action === "close") {
        hideDialog(true);
        offer.hidden = true;
      } else if (state.status === "in_progress" && state.step) {
        showStep(state);
      } else {
        hideDialog(action === "skip" || state.status === "completed");
        offer.hidden = true;
      }
    } catch (_error) {
      progressLabel.textContent = "No se pudo guardar el recorrido. Inténtalo de nuevo.";
      progressLabel.setAttribute("role", "alert");
    }
  };

  offer.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tour-offer-action]");
    if (!button) return;
    const action = button.dataset.tourOfferAction;
    if (action === "dismiss") {
      sessionStorage.setItem("ramperTourOfferDismissed", "1");
      offer.hidden = true;
      (document.querySelector("[data-tour-reopen]") || document.querySelector(".brand"))?.focus();
      return;
    }
    returnFocus = document.querySelector("[data-tour-reopen]") || button;
    if (action === "skip") perform("skip");
    else perform("start");
  });

  dialog.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tour-action]");
    if (button && !button.disabled) perform(button.dataset.tourAction);
  });

  document.addEventListener("click", (event) => {
    const step = activeState?.step;
    const link = event.target.closest("a[data-tour]");
    if (!step || !link || link.dataset.tour !== step.target) return;
    if (!["open_profile", "return_to_vacancies"].includes(step.id)) return;
    event.preventDefault();
    perform("next");
  });

  document.querySelector("[data-tour-reopen]")?.addEventListener("click", (event) => {
    returnFocus = event.currentTarget;
    perform("reopen");
  });

  dialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      perform("close");
    }
  });

  fetch(dialog.dataset.stateUrl, { credentials: "same-origin", headers: { Accept: "application/json" } })
    .then((response) => {
      if (!response.ok) throw new Error("No se pudo consultar el recorrido.");
      return response.json();
    })
    .then((state) => {
      activeState = state;
      if (state.status === "in_progress" && state.step) {
        showStep(state);
      } else if (state.offer && sessionStorage.getItem("ramperTourOfferDismissed") !== "1") {
        offer.hidden = false;
      }
    })
    .catch(() => {
      offer.hidden = true;
    });
});
