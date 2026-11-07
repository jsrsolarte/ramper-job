# Design

## Context

El proyecto no tiene código existente. El stack elegido es Python con Django, PostgreSQL y Celery con Redis. La primera fuente será elempleo.com Colombia y se consultará mediante scraping de páginas públicas. La configuración y operación de OmniRoute quedan a cargo del administrador.

## Goals / Non-Goals

**Goals:**
- Separar autenticación, perfiles, ingesta de vacantes, análisis de IA y consulta del dashboard.
- Mantener privados los datos de cada cuenta y permitir que el administrador gestione cuentas.
- Procesar la búsqueda de forma asíncrona para que el dashboard no dependa de la disponibilidad inmediata de la fuente o del modelo.
- Mantener intercambiables la fuente de vacantes y el servicio de IA.
- Permitir evolucionar fuentes, funcionalidades y criterios de análisis de forma incremental, con configuración versionada y editable desde la administración.

**Non-Goals:**
- Separar la primera versión en microservicios o construir un frontend SPA independiente.
- Elegir un proveedor de alojamiento específico antes de definir el entorno de despliegue.
- Instalar, desplegar, administrar proveedores o decidir el modelo dentro de OmniRoute.
- Postular automáticamente a empleos o habilitar auto-registro.
- Generar en esta fase CV personalizados para ATS; esa capacidad futura deberá crear una copia y preservar el CV base.

## Decisions

### Monolito modular con Django

La primera versión será una aplicación Django en Python, organizada en módulos de cuentas y perfiles, fuentes de vacantes, compatibilidad, configuración de análisis y dashboard. Django servirá la interfaz con plantillas del servidor y usará su sistema de autenticación y permisos; su panel administrativo permitirá crear y desactivar cuentas y administrar la configuración versionada del análisis. Se elige un monolito modular para mantener un solo proyecto desplegable y aprovechar las funciones integradas de Django. Una API separada con un frontend JavaScript independiente agrega servicios y contratos que el alcance actual no necesita.

### PostgreSQL para datos y aislamiento

PostgreSQL guardará cuentas, perfiles, vacantes normalizadas y análisis. Cada perfil y resultado tendrá una relación con su cuenta; las consultas del dashboard y del procesamiento deben aplicar ese propietario. Los CV se guardarán en almacenamiento privado persistente y la aplicación conservará su ubicación y metadatos en PostgreSQL. Se prefiere una base relacional para mantener relaciones y restricciones claras frente a una base documental como única fuente de verdad.

### Celery y Redis para tareas asíncronas

La aplicación web enviará a Celery las tareas de actualización de vacantes y análisis por perfil. Redis será el broker de tareas; Celery Beat programará la frecuencia configurable. El proceso web, el worker y el scheduler usarán el mismo código Django y PostgreSQL. Se elige procesamiento asíncrono porque la lectura de páginas y las solicitudes al modelo pueden tardar o fallar; ejecutarlas dentro de una petición web haría que el dashboard dependiera de esos servicios.

### Separar la ingesta de fuentes del análisis

Cada fuente se integra como un conector Python con un contrato común para consultar publicaciones, normalizarlas y registrar la URL de origen. El conector inicial usa un cliente HTTP y BeautifulSoup para extraer páginas públicas de elempleo.com, sin requerir una API. Si el contenido se renderiza únicamente en el navegador, se evaluará Playwright para esa fuente. Si una página requiere autenticación o no puede consultarse, el conector la omite y señala que no está disponible. Las publicaciones normalizadas pasan a Celery para deduplicarlas y solicitar análisis por perfil. Agregar una fuente nueva requiere implementar y configurar otro conector sin cambiar el flujo compartido de análisis y presentación.

Alternativas consideradas: depender de una API o acoplar el análisis directamente al HTML de elempleo.com. Se elige scraping público porque permite empezar por la fuente seleccionada sin una integración de API. Mantener el conector separado aísla cambios de página del procesamiento de vacantes.

### Usar OmniRoute detrás de un adaptador de análisis

La aplicación envía el contexto necesario del CV, criterios y vacante al endpoint de OmniRoute configurado por el administrador. Un adaptador traduce la solicitud y valida una respuesta estructurada con descripción organizada, puntaje, razones y brechas. Los prompts y parámetros de coincidencia se administran mediante una interfaz, se guardan como versiones inmutables y cada análisis registra las versiones aplicadas. Una modificación se usa en nuevos análisis; el administrador puede solicitar reprocesar resultados para aplicar la configuración vigente. Los secretos de acceso se suministran por configuración segura y no se incluyen en el código ni en registros. La implementación confirma el contrato compatible que exponga la instancia configurada.

Alternativas consideradas: integrar cada proveedor/modelo directamente o acoplar todo el dominio al protocolo de OmniRoute. La integración directa duplicaría configuración que el administrador manejará en OmniRoute; el adaptador permite cambiar el endpoint o el contrato sin cambiar las reglas del dashboard.

### Aislar los datos por cuenta

Cada perfil, CV, criterio y análisis lleva una relación explícita con su cuenta. La capa de acceso filtra por la cuenta autenticada en todas las consultas; el rol administrador puede crear y desactivar cuentas. Los CV se guardan en almacenamiento privado y no se escriben en logs.

Alternativa considerada: guardar los CV en un repositorio compartido y aplicar filtros solo en la interfaz. Se descarta porque cualquier error de interfaz podría exponer información de otra persona.

### Mantener versiones de perfil y configuración de análisis

Los cambios al CV o a los criterios crean una nueva versión vigente del perfil para análisis posteriores. Los resultados conservan la referencia a la versión de perfil, prompt y parámetros usados, de modo que puedan entenderse y reproducirse. La edición no altera retroactivamente análisis previos; el administrador puede volver a procesar vacantes para generar resultados con las versiones actuales.

Alternativa considerada: sobrescribir perfil y configuración y perder el contexto de resultados previos. Se descarta porque dificultaría explicar cambios de puntaje y comparar ajustes.

### Guardar el análisis como un resultado legible y verificable

Cada análisis vincula perfil, vacante, puntaje, razones, brechas y descripción organizada por IA. El contenido original se conserva solo para procesar la vacante y no se presenta como descripción del dashboard; se conserva el enlace a la publicación original. Una respuesta incompleta o inválida no se muestra como una coincidencia confiable y queda pendiente de análisis.

Alternativa considerada: guardar y mostrar la respuesta de texto libre del modelo. Se descarta porque impide ordenar resultados consistentemente y facilita presentar respuestas parciales como datos completos.

## Risks / Trade-offs

- [elempleo.com puede cambiar sus páginas o no estar disponible] → Consultar páginas públicas a una frecuencia moderada, usar límites de solicitudes y pausar el conector ante errores repetidos.
- [Las publicaciones pueden ser incompletas, repetidas o quedar desactualizadas] → Deduplicar por identificador o URL canónica, preservar campos desconocidos y volver a consultar la fuente en cada ciclo.
- [El modelo puede puntuar mal o inventar detalles] → Exigir respuesta estructurada, mostrar razones y brechas, y no presentar resultados inválidos como análisis terminado.
- [El servicio de IA o la fuente pueden estar caídos] → Procesar en segundo plano y dejar el resultado pendiente para reintento, sin bloquear el dashboard.
- [Los CV contienen datos personales] → Aplicar aislamiento por cuenta, minimizar el contexto enviado al análisis y excluir CV y credenciales de los logs.
- [Un ajuste global de prompt o parámetros puede cambiar los resultados para todos] → Conservar versiones, registrar qué versión produjo cada análisis y permitir reprocesamiento explícito.

## Migration Plan

No hay datos ni usuarios existentes que migrar. Desplegar la aplicación Django, PostgreSQL, Redis y los procesos de Celery; crear cuentas administradas, cargar perfiles y ejecutar la primera ingesta y análisis. Para revertir una fuente, deshabilitar su conector y conservar los resultados existentes con el enlace de origen; para detener análisis, pausar el procesamiento y mantener el dashboard de solo lectura.

## Open Questions

- La frecuencia de actualización puede ajustarse después de observar el uso; el primer despliegue tendrá una cadencia configurable.
- Los perfiles comenzarán con criterios flexibles en texto; los filtros estructurados adicionales podrán definirse a partir del uso.
- Los conectores futuros implementarán el contrato común de fuente; la generación de CV personalizados para ATS se definirá en un cambio posterior y conservará el CV base.
