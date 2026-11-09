from django.urls import reverse


TOUR_VERSION = 3

TOUR_STEPS = (
    {
        "id": "open_profile",
        "title": "Empieza por Mi perfil",
        "text": "Antes de explorar las vacantes, configura tu búsqueda y carga tu hoja de vida. Selecciona Mi perfil para comenzar.",
        "url_name": "dashboard:home",
        "target": "profile-nav",
        "fallback_target": "dashboard-content",
    },
    {
        "id": "cv",
        "title": "Tu hoja de vida",
        "text": "Carga aquí la versión vigente de tu CV. La usamos como base para encontrar y comparar oportunidades; avanzar por esta guía no cambia ni carga archivos por ti.",
        "url_name": "profiles:edit",
        "target": "cv",
    },
    {
        "id": "phrases",
        "title": "Frases de búsqueda",
        "text": "Agrega cargos o áreas que te interesan. La IA también puede proponer frases relacionadas con la experiencia de tu CV; tú decides qué criterios guardar.",
        "url_name": "profiles:edit",
        "target": "phrases",
    },
    {
        "id": "locations",
        "title": "Dónde quieres trabajar",
        "text": "Incluye las ciudades o zonas donde aceptarías una oportunidad. Puedes elegir varias ubicaciones cercanas y ajustar la lista cuando cambien tus preferencias.",
        "url_name": "profiles:edit",
        "target": "locations",
    },
    {
        "id": "remote",
        "title": "Trabajo remoto",
        "text": "Activa esta opción si también quieres considerar vacantes remotas. Esta preferencia se evalúa junto con las ubicaciones que guardaste.",
        "url_name": "profiles:edit",
        "target": "remote",
    },
    {
        "id": "threshold",
        "title": "Descarte automático por puntaje",
        "text": "Este umbral se aplica a vacantes nuevas: las que puntúan por debajo pasan a Descartadas. Cero desactiva la regla. Cambiarlo no modifica vacantes ya encontradas; el filtro de estrellas del dashboard solo cambia lo que ves.",
        "url_name": "profiles:edit",
        "target": "threshold",
    },
    {
        "id": "return_to_vacancies",
        "title": "Vuelve a Recomendaciones",
        "text": "Ya viste cómo configurar tu búsqueda. Usa este enlace para volver a Recomendaciones y seguir con el recorrido de las vacantes.",
        "url_name": "profiles:edit",
        "target": "back-to-dashboard",
    },
    {
        "id": "stars",
        "title": "Filtra recomendaciones por estrellas",
        "text": "En Recomendaciones puedes filtrar por un mínimo de estrellas y ver las vacantes con ese puntaje o más. Este filtro no cambia el umbral de tu perfil ni el estado de ninguna vacante.",
        "url_name": "dashboard:home",
        "target": "score-filter",
        "fallback_target": "dashboard-content",
    },
    {
        "id": "details",
        "title": "Revisa el análisis de compatibilidad",
        "text": "Abre los detalles de una tarjeta para consultar por qué coincide y qué aspectos conviene revisar antes de decidir si continúas con una vacante.",
        "url_name": "dashboard:home",
        "target": "vacancy-details",
        "fallback_target": "dashboard-content",
    },
    {
        "id": "follow_up",
        "title": "Organiza tu seguimiento",
        "text": "Las pestañas separan Recomendaciones, Aplicadas, En proceso, Entrevista, Finalizadas y Descartadas. Mover una vacante entre estados organiza tu seguimiento personal.",
        "url_name": "dashboard:home",
        "target": "follow-up-tabs",
        "fallback_target": "dashboard-content",
    },
    {
        "id": "pending",
        "title": "Vacantes por analizar",
        "text": "En la pestaña Por analizar aparecen las vacantes encontradas para tu perfil mientras termina su análisis. Cuando esté listo, el resultado puede aparecer en Recomendaciones si cumple tu umbral.",
        "url_name": "dashboard:pending",
        "target": "pending-tab",
        "fallback_target": "dashboard-content",
    },
)


def is_tour_eligible(user):
    return bool(user.is_authenticated and not user.is_staff and not user.is_superuser)


def step_by_id(step_id):
    return next((step for step in TOUR_STEPS if step["id"] == step_id), None)


def step_payload(step_id):
    step = step_by_id(step_id)
    if step is None:
        return None
    return {
        "id": step["id"],
        "title": step["title"],
        "text": step["text"],
        "url": reverse(step["url_name"]),
        "target": step["target"],
        "fallback_target": step.get("fallback_target", ""),
    }
