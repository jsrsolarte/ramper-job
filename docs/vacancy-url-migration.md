# Migración a identidad por URL de vacantes

La migración `jobs.0009_vacancy_url_identity_and_detail_state` normaliza host, esquema y barra final, y excluye parámetros y fragmentos. Solo consolida registros con la misma fuente y la misma URL normalizada.

Al consolidar, mantiene todas las filas de análisis y las reasigna al registro sobreviviente; combina descubrimientos por perfil conservando el primer hallazgo y el umbral capturado; conserva el seguimiento más reciente por perfil; reasigna organizaciones y envíos manuales. Las organizaciones duplicadas con la misma configuración y huella conservan la completada más reciente y trasladan sus referencias de análisis.

Los registros históricos que solo coincidían por identificador externo o huella de título/empresa/ubicación no se separan: no existe información fiable para reconstruir cuál era su identidad antes de la consolidación previa. Sus `alternate_urls` permanecen como evidencia histórica, pero no se convierten automáticamente en alias. Se requiere revisión humana antes de atribuir esas URL a otra ficha.

El estado de ficha histórica queda `unknown` salvo que tenga el marcador explícito `raw_data.details_fetch.status = confirmed`; no se infiere éxito de la presencia de una descripción. El siguiente encuentro vuelve a solicitar los detalles desconocidos.
