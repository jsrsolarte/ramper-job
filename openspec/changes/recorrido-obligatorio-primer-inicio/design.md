# Design

## Context

El recorrido ya persiste por cuenta su versión, paso y estado, se ofrece a aspirantes, permite omitirlo y volver a abrirlo. El encabezado de las vistas autenticadas ya contiene la acción «Ver guía». El recorrido atraviesa el dashboard y Mi perfil.

## Goals / Non-Goals

**Goals:**
- Exigir el recorrido solo durante la primera experiencia de cuentas aspirantes.
- Evitar que versiones futuras del contenido vuelvan a bloquear cuentas que ya pasaron el primer acceso.
- Mantener una repetición voluntaria siempre disponible desde el encabezado.

**Non-Goals:**
- Cambiar los pasos o explicaciones del recorrido.
- Aplicar la obligatoriedad a cuentas administradoras o a aspirantes que ya usaban la plataforma.
- Bloquear el inicio o cierre de sesión.

## Decisions

### Separar el estado de primer acceso de la versión del recorrido

Guardar un marcador de cumplimiento obligatorio separado de la versión y del paso del recorrido. En la migración, las cuentas aspirantes con un inicio de sesión anterior se consideran existentes y no quedan bloqueadas; las cuentas sin inicio de sesión previo quedan pendientes de completar el recorrido. Las nuevas cuentas aspirantes también comienzan pendientes. Así, actualizar textos o pasos no vuelve obligatorio el recorrido para todos.

**Alternativa considerada:** usar únicamente la ausencia de progreso para decidir si el recorrido es obligatorio. Se descarta porque cuentas antiguas sin progreso quedarían bloqueadas aunque ya hubieran usado la aplicación.

### Mantener un modo obligatorio y otro voluntario

En el primer acceso, iniciar el recorrido automáticamente y permitir únicamente la navegación guiada necesaria para llegar a los elementos del perfil y del dashboard. Ocultar omitir/cerrar mientras sea obligatorio; salir de la sesión conserva el paso y no elimina la barrera. Al completar, registrar el cumplimiento y habilitar la aplicación. La opción del encabezado inicia una reproducción voluntaria que puede cerrarse u omitirse sin bloquear el uso.

**Alternativa considerada:** mostrar el recorrido como un modal que se puede cerrar y dejar el resto de la aplicación disponible. Se descarta porque no garantiza que la persona reciba la orientación inicial solicitada.

### Mantener el botón de guía en el encabezado compartido

Conservar «Ver guía» en el encabezado común de todas las vistas de aspirante, incluyendo dashboard y perfil. La reproducción voluntaria comienza desde el primer paso y no modifica preferencias, CV ni estados.

**Alternativa considerada:** mostrar el botón solo en el dashboard. Se descarta porque el recorrido también explica Mi perfil y puede reabrirse desde cualquier vista.

## Risks / Trade-offs

- [Una cuenta puede abandonar la guía y pensar que quedó bloqueada] → Indicar claramente que puede cerrar sesión y continuar luego; guardar el paso actual.
- [Un recorrido obligatorio puede verse interrumpido por navegación entre páginas] → Permitir las rutas requeridas por los pasos y mantener el estado al cambiar de dashboard a perfil.
- [Una actualización de pasos podría volver a imponer el recorrido] → Mantener el marcador de cumplimiento separado de la versión de contenido.

## Migration Plan

1. Añadir el marcador de cumplimiento obligatorio y clasificar cuentas existentes con inicio de sesión previo como ya habilitadas.
2. Hacer que cuentas aspirantes nuevas o sin inicio de sesión previo comiencen el recorrido automáticamente y no puedan omitirlo.
3. Al completar, habilitar el acceso normal y conservar el botón del encabezado para reproducciones voluntarias.
4. Verificar primer acceso, reanudación, finalización, cuentas existentes, cuentas administrativas y repetición voluntaria.
