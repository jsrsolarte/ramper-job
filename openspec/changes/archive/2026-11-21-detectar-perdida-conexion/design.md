# Design

## Context

La interfaz usa páginas y formularios Django, con algunas acciones JavaScript. Una respuesta de red fallida puede ocurrir después de que el servidor haya aplicado el cambio. `instalar-aplicacion-chrome` excluye funcionamiento sin conexión y conserva la experiencia del navegador; este cambio añade un aviso cuando la página ya está cargada.

## Goals / Non-Goals

**Goals:**
- Distinguir ausencia de red de imposibilidad de contactar el servicio y evitar promesas falsas sobre guardados.

**Non-Goals:**
- Caché de información privada, envío diferido, reintentos automáticos de escrituras o disponibilidad sin red.
- Garantizar que una página que nunca cargó pueda mostrar interfaz propia.

## Decisions

- En la plantilla común, usar eventos del navegador como señal inicial y una comprobación de mismo origen, ligera, sin caché, con tiempo límite. `navigator.onLine` por sí solo no demuestra que el servidor responda; una comprobación fallida tampoco demuestra que el usuario no tenga internet. Usar un endpoint público sin redirecciones ni información sensible, verificando el contrato real antes de reutilizar uno existente.
- Al detectar recuperación de red, comprobar el servicio y repetir con intervalo limitado mientras esté inaccesible, sin consultas continuas en estado normal. Aviso textual persistente y región accesible; mensaje breve de recuperación sin reiniciar la página. Las comprobaciones solo verifican acceso, no ejecutan tareas externas.
- No interceptar ciegamente todos los formularios ni alterar semántica de subida de archivos. Para las operaciones JavaScript existentes, manejar fallos sin respuesta como resultado incierto, sin repetir escrituras. En navegación o envío convencional que abandona la página, el navegador puede mostrar un error y no se promete conservar contenido: revisar y documentar cobertura concreta de flujos al implementar.
- La comprobación y el aviso global no interceptan los POST convencionales de perfil, seguimiento de vacantes, invitaciones ni administración. Mientras la misma pantalla siga abierta, el aviso no modifica sus campos; si un envío navega fuera y la respuesta no llega, el contenido puede no conservarse y la persona debe verificar el resultado antes de enviar otra vez. Las subidas de archivos mantienen su flujo normal.
- Conservar los campos solo mientras permanezca abierta la pantalla, sin persistencia local. La persona decide cuándo revisar y reintentar; no se sugiere que el estado confirmado se haya revertido.

## Risks / Trade-offs

- [Un servidor responde a la comprobación pero otra operación falla] → Tratar fallos de operaciones por separado y no garantizar disponibilidad absoluta.
- [La señal de red o un fallo transitorio produce avisos] → Usar mensajes diferenciados y comprobaciones limitadas, con pruebas de transición.
- [Un formulario convencional puede perderse al navegar] → No prometer preservación tras navegación y probar los flujos críticos.

## Migration Plan

Agregar la interfaz y comprobación sin migraciones de datos; revertir el cliente y la ruta nueva si corresponde. Probar localmente con datos sintéticos y seguir las autorizaciones habituales antes de despliegues.
