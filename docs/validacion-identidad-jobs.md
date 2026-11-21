# Validación local de identidad Jobs

Fecha: 20 de noviembre de 2026. Las revisiones visuales registradas corresponden al árbol local de desarrollo; validar también esta integración separada sobre staging. Entorno sintético temporal: Python 3.12, Django 5.2.19 y PostgreSQL 17 en localhost; dependencias resueltas dentro de los rangos de `pyproject.toml`, no desde `uv.lock`. Sin trabajadores, Beat ni datos reales. La configuración temporal deshabilitó el correo externo y usó broker en memoria; las pruebas Python bloquearon conexiones de socket no locales.

- Suite Django: 383 pruebas aprobadas después de corregir la extracción del enlace en las pruebas de invitación.
- Tras ajustar las estrellas se repitieron 54 pruebas de panel, seguimiento e instalación: todas aprobadas.
- `collectstatic`: 150 archivos y sus recursos procesados; fuentes e iconos aparecen en el manifiesto de estáticos.
- Los recursos Jobs copiados coinciden con los SHA-256 del manifiesto de marca. El manifiesto conserva `id`, `start_url` y `scope` en `/`; declara Jobs y PNG 192/512. Las pruebas automatizadas verifican entrega pública, MIME, dimensiones, sesión y privacidad.
- Navegador integrado en escritorio y ventana de 390 × 844: revisados ingreso, panel, recorrido, perfil, centro administrativo y lista de usuarios de Django admin con cuentas ficticias. Se comprobó el uso de Sora en títulos, Inter en cuerpo, foco visible en ingreso y ausencia de desbordamiento horizontal del documento en perfil y administración móviles. La tabla administrativa conserva desplazamiento horizontal propio.
- Corregido contraste en Django admin: se evita mezclar su tema oscuro con las superficies claras de Jobs; esta administración utiliza tema claro. Añadidos acentos azules y cian a navegación, fondos y tarjetas.
- Con tres vacantes ficticias se revisaron tarjetas y estados de organización completa, pendiente y fallida; se expandió el análisis y se cambió un seguimiento a Aplicada. La vista móvil de 390 px conservó el contenido sin desbordamiento horizontal del documento y expuso el estado seleccionado al lector de pantalla.
- Las estrellas llenas y vacías se oscurecieron al detectar contraste insuficiente: sobre los fondos comprobados las llenas alcanzan al menos 3,89:1 y las vacías 3,38:1.
- Contrastes calculados de referencia: blanco sobre `#2D6CDF` 4,86:1; `#2D6CDF` sobre `#F6F7FB` 4,54:1; `#50647B` sobre blanco 6,09:1; blanco sobre `#12263F` 15,28:1. No constituyen una auditoría completa de todos los estados y superficies.

## Barrido adicional de accesibilidad

- En el navegador integrado se revisaron ingreso, panel con vacantes, perfil, centro y parámetros administrativos y lista de usuarios de Django admin. Se inspeccionaron nombres accesibles de controles de la lista, foco de teclado y estado actual de navegación; el enlace enfocado mostró un contorno sólido de 3 px y la pestaña actual expone `aria-current`.
- El análisis de texto visible sobre fondos sólidos detectó contadores de navegación a 4,37:1 y texto de ruta administrativa a 2,32:1. Se corrigieron: el contador ahora alcanza 6,95:1 y el texto blanco de la ruta 4,86:1; el enlace de navegación administrativa resaltado alcanza 6,78:1. Se repitió la inspección en las pantallas afectadas sin nuevos casos detectados por ese método.
- El análisis no evalúa degradados, transparencias, todos los estados interactivos ni sustituye una auditoría completa WCAG. Se mantienen abiertas las tareas de revisión completa. Las cuatro pruebas PWA se repitieron y aprobaron.

## Revisión ampliada

- En una copia de configuración temporal se cargó axe-core 4.10.3, sin incorporarlo a la aplicación. Se revisaron los criterios automatizables etiquetados WCAG 2/2.1 A y AA y WCAG 2.2 AA en escritorio y a 320 px: ingreso y error de ingreso, vacantes y recorrido con datos ficticios, perfil, análisis, pendientes, centro administrativo, usuarios, creación de cuenta, parámetros, observabilidad, estadísticas, registro manual y lista de usuarios de Django admin. En los estados inspeccionados la última ejecución no informó infracciones. La herramienta no verifica por sí sola todos los criterios de accesibilidad.
- Se corrigieron el contraste del texto sobre el degradado del ingreso, los bordes de campos y botones secundarios (3,85:1 y 3,51:1 respectivamente sobre los fondos medidos), el contorno de foco de los campos y las áreas táctiles de la lista administrativa. Se verificó el contorno del formulario con teclado.
- Las tablas administrativas desplazables ahora reciben foco y admiten flechas, Inicio y Fin. Se comprobó en una tabla a 320 px que la flecha derecha desplaza 80 px y que Inicio y Fin alcanzan ambos extremos.
- Tras los cambios se ejecutaron 88 pruebas Django de panel, perfiles, usuarios e instalación, todas aprobadas, y `collectstatic` terminó correctamente. El analizador y su instrumentación se limitaron a `/tmp`.

## Validación con versiones fijadas

- La copia candidata separada, basada en staging `cdd5e041ecc4065747a0a6911a26604497f83629`, pasó 377 pruebas Django y `collectstatic` con Python 3.12 y el `uv.lock` del proyecto.
- El árbol local de desarrollo, que contiene además cambios de otras funcionalidades, pasó 383 pruebas con el mismo `uv.lock`.

- La copia candidata basada en staging se revisó en el navegador integrado con datos ficticios: ingreso y panel pasaron axe-core en escritorio; el panel pasó a 320 px sin desbordamiento horizontal del documento.

## Instalación en Android (prueba local)

- En Android, Chrome 157.0.8103.78 ofreció instalar Jobs; la persona usuaria confirmó nombre, icono, apertura independiente, navegación y cierre de sesión. Con Wi‑Fi, datos móviles y USB desconectados confirmó error de conexión sin contenido privado anterior.
- Se canceló el diálogo de instalación y el sitio siguió disponible. En un segundo origen local se instaló el manifiesto anterior como «Ramper» y se abrió de manera independiente. Tras servir el manifiesto Jobs en ese mismo origen, la actualización de nombre/icono y la ausencia de duplicados aún no están confirmadas: se observó una respuesta condicional 304 en la primera recarga y el nombre anterior seguía visible. No se considera aprobada esa prueba.
- Chrome trata los cambios de nombre e icono como cambios de identidad que la persona puede revisar o rechazar; véase [Chrome for Developers](https://developer.chrome.com/blog/improvements-to-web-app-updates). La prueba debe registrar la decisión y el resultado en lugar de asumir una actualización inmediata.

## Confirmación de escritorio y caché del manifiesto

- La persona usuaria confirmó que probó manualmente en Chrome de escritorio la instalación de Jobs, su apertura en ventana independiente, la navegación y el comportamiento sin conexión. El Chrome Flatpak instalado en el equipo figura como 158.0.8127.36; no se confirmó la versión utilizada en la prueba.
- Para evitar reutilizar una respuesta condicional antigua, el enlace al manifiesto incorpora `?v=jobs-1`; el `id`, `start_url` y `scope` siguen siendo `/`. Las cuatro pruebas PWA del candidato pasaron después de este cambio. Falta observar la actualización de identidad de la instalación anterior y comprobar ausencia de duplicados.

## Validación posterior en staging

- La persona usuaria confirmó que una instalación de staging existente antes del cambio se actualizó a Jobs sin duplicados.
- La persona usuaria probó TalkBack en Android y confirmó que anuncia correctamente la navegación, los botones y los estados. No se registró una auditoría exhaustiva de todos los estados dinámicos ni una certificación de conformidad WCAG.
- La versión de Chrome usada en la prueba de escritorio y los detalles de la decisión de actualización en staging no fueron registrados.
