# Tasks

## 1. Fundamentos del producto

- [x] 1.1 Crear el proyecto Django y su configuración local para PostgreSQL; verificar que la aplicación inicia y conecta con la base de datos.
- [x] 1.2 Configurar autenticación y administración manual de cuentas con Django Admin, sin auto-registro; verificar que el administrador crea una cuenta y que una persona sin cuenta no puede registrarse.
- [x] 1.3 Implementar perfiles y criterios flexibles en texto con datos asociados a la cuenta y guardar CV en almacenamiento privado persistente; permitir actualizar ambos y conservar versiones usadas por análisis previos.

## 2. Ingesta de vacantes

- [x] 2.1 Definir un contrato común de conectores e implementar el conector Python HTTP/BeautifulSoup para páginas públicas de elempleo.com Colombia; verificar que extrae vacantes y omite páginas que requieren autenticación o no están disponibles.
- [x] 2.2 Normalizar vacantes en PostgreSQL y conservar el enlace de origen y los campos disponibles; verificar que los datos incompletos se guardan sin inventar valores.
- [x] 2.3 Implementar deduplicación y actualización configurable con Celery Beat y Redis; verificar que una vacante repetida actualiza la existente y que la tarea se ejecuta según la configuración.

## 3. Análisis de compatibilidad

- [x] 3.1 Implementar el adaptador al endpoint de OmniRoute con URL, modelo y credenciales suministrados por configuración; verificar que un worker Celery solicita un análisis al modelo configurado.
- [x] 3.2 Generar y validar una respuesta estructurada con descripción organizada, puntaje de 0 a 100, razones y requisitos faltantes; verificar que una respuesta completa se guarda y una respuesta inválida no se marca como terminada.
- [x] 3.3 Procesar análisis en Celery por cada perfil y manejar indisponibilidad del modelo; verificar que un error deja el análisis pendiente y no bloquea la consulta del dashboard.
- [x] 3.4 Implementar administración de prompts y parámetros de coincidencia con historial de versiones; cada análisis debe guardar las versiones de perfil, prompt y parámetros utilizadas, y permitir reprocesar vacantes con la configuración vigente.

## 4. Dashboard de vacantes

- [x] 4.1 Implementar el dashboard con plantillas Django para mostrar vacantes ordenadas por puntaje, descripción organizada, razones y brechas; verificar que cada familiar solo ve sus resultados y el orden es descendente.
- [x] 4.2 Enlazar cada vacante con su publicación original; verificar que el enlace abre la fuente y que la aplicación no envía postulaciones.
