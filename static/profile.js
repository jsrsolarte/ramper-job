document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("textarea[data-chip-editor]").forEach((textarea) => {
    const wrapper = document.createElement("div");
    wrapper.className = "chip-editor";
    const list = document.createElement("ul");
    list.className = "editable-list";
    const entry = document.createElement("div");
    entry.className = "chip-entry";
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = textarea.dataset.chipEditor === "locations" ? "Ej. Bogotá, Medellín" : "Ej. Analista de procesos";
    const add = document.createElement("button");
    add.type = "button";
    add.className = "chip-add";
    add.textContent = "Agregar";
    const label = textarea.parentElement.querySelector(`label[for="${textarea.id}"]`);
    if (label) label.htmlFor = `${textarea.id}-entry`;
    input.id = `${textarea.id}-entry`;
    input.setAttribute("aria-label", textarea.dataset.chipEditor === "locations" ? "Agregar ubicación" : "Agregar frase de búsqueda");
    entry.append(input, add);
    wrapper.append(list, entry);
    textarea.insertAdjacentElement("afterend", wrapper);
    textarea.hidden = true;

    let values = textarea.value.trim().startsWith("[")
      ? JSON.parse(textarea.value)
      : textarea.value.split(/\r?\n/).map((value) => value.trim()).filter(Boolean);
    if (!Array.isArray(values)) values = [];

    const render = () => {
      list.replaceChildren();
      values.forEach((value, index) => {
        const item = document.createElement("li");
        item.className = "editable-list-item";
        const text = document.createElement("span");
        text.textContent = value;
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "list-remove";
        remove.textContent = "Quitar";
        remove.setAttribute("aria-label", `Quitar ${value}`);
        remove.addEventListener("click", () => {
          values.splice(index, 1);
          render();
        });
        item.append(text, remove);
        list.append(item);
      });
      textarea.value = JSON.stringify(values);
    };
    const addValue = () => {
      const value = input.value.trim().replace(/\s+/g, " ");
      if (value && !values.some((existing) => existing.toLocaleLowerCase() === value.toLocaleLowerCase())) {
        values.push(value);
        render();
      }
      input.value = "";
      input.focus();
    };
    add.addEventListener("click", addValue);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        addValue();
      }
    });
    render();
  });
});
