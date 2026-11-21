# Spec Delta

## Purpose

Permite reconocer recomendaciones nuevas dentro de Ramper Job y recibir, por decisión propia, un resumen diario discreto en dispositivos compatibles.

## ADDED Requirements

### Requirement: Identificar recomendaciones nuevas
El sistema SHALL contar por perfil las vacantes únicas que hayan entrado por primera vez en Recomendaciones después de habilitar esta capacidad y sigan visibles en ese estado, sin aplicar filtros temporales de pantalla.

#### Scenario: Una recomendación queda disponible
- **WHEN** una vacante se incorpora por primera vez a Recomendaciones para un perfil
- **THEN** se considera nueva para ese perfil y aparece en su indicador

#### Scenario: Una vacante no es una recomendación visible
- **WHEN** una vacante está descartada, archivada, en otra etapa o no cumple las condiciones vigentes de visibilidad
- **THEN** no se cuenta en el indicador ni en el resumen mientras permanezca fuera de Recomendaciones

#### Scenario: Se repite una búsqueda o análisis
- **WHEN** una vacante ya contabilizada vuelve a encontrarse o analizarse para el mismo perfil
- **THEN** no se vuelve a considerar nueva por ese hecho

#### Scenario: Se habilita la funcionalidad
- **WHEN** se habilita por primera vez para una cuenta existente
- **THEN** las recomendaciones anteriores no se anuncian como recién llegadas y las nuevas posteriores sí se registran

### Requirement: Mostrar y reconocer novedades
La aplicación SHALL mostrar un indicador discreto y accesible con el número de recomendaciones nuevas del perfil y permitir marcarlas como revisadas mediante una acción explícita.

#### Scenario: Hay novedades
- **WHEN** la persona abre la aplicación y tiene recomendaciones nuevas
- **THEN** ve el número de novedades y puede abrir Recomendaciones

#### Scenario: Se marcan como revisadas
- **WHEN** la persona elige marcar las novedades como revisadas
- **THEN** el indicador deja de contarlas, sin cambiar su estado de seguimiento, y conserva las que lleguen después de esa acción

#### Scenario: No hay novedades
- **WHEN** no hay recomendaciones nuevas para el perfil
- **THEN** no se muestra una alerta de novedades

### Requirement: Activar el resumen diario voluntariamente
El sistema SHALL mantener el resumen desactivado por defecto y permitir activarlo o desactivarlo por dispositivo desde una opción identificable.

#### Scenario: La persona activa el resumen
- **WHEN** la persona solicita activarlo en un dispositivo compatible
- **THEN** el navegador solicita permiso y la aplicación informa si quedó activado

#### Scenario: La persona rechaza o bloquea el permiso
- **WHEN** se rechaza el permiso o el navegador no permite notificaciones
- **THEN** el resumen no se activa, se explica el estado y el indicador interno sigue disponible

#### Scenario: La persona desactiva el resumen
- **WHEN** desactiva el resumen para un dispositivo
- **THEN** no se programan nuevos avisos para ese dispositivo y el indicador interno continúa funcionando

### Requirement: Limitar el resumen diario
El sistema SHALL intentar como máximo un resumen por día calendario y dispositivo habilitado, a las 9:00 de America/Bogota, solo si hay recomendaciones llegadas desde el corte anterior o la activación del dispositivo que sigan nuevas y sin revisar.

#### Scenario: Hay novedades al corte
- **WHEN** llega el corte diario y hay recomendaciones nuevas sin revisar
- **THEN** se intenta un único aviso agrupado para cada dispositivo habilitado con un texto genérico que invita a abrir Ramper Job

#### Scenario: No hay novedades al corte
- **WHEN** llega el corte diario sin recomendaciones nuevas sin revisar
- **THEN** no se envía ningún aviso

#### Scenario: El planificador se reinicia o repite el trabajo
- **WHEN** se procesa más de una vez el mismo día para el mismo dispositivo
- **THEN** no se inicia un segundo envío de ese resumen

#### Scenario: La persona ya revisó las novedades
- **WHEN** se marcan las novedades como revisadas antes del corte y no llegan otras
- **THEN** no se envía un resumen por esas novedades

#### Scenario: No llegan novedades adicionales
- **WHEN** al corte solo quedan novedades de días anteriores
- **THEN** no se repite el aviso por ellas aunque sigan sin revisar

### Requirement: Proteger el contenido y el acceso
El aviso del dispositivo SHALL evitar nombres, cargos, empresas, detalles de vacantes y otros datos personales; al abrirlo SHALL usar el acceso autenticado habitual.

#### Scenario: Se pulsa el resumen
- **WHEN** la persona abre la notificación
- **THEN** llega a Recomendaciones o al inicio de sesión si su sesión no es válida

#### Scenario: Se cierra sesión o cambia de cuenta
- **WHEN** la persona cierra sesión o cambia de cuenta en un dispositivo
- **THEN** el dispositivo deja de recibir resúmenes de la cuenta anterior hasta que esa cuenta vuelva a activarlos

#### Scenario: La cuenta se desactiva
- **WHEN** una cuenta deja de estar activa
- **THEN** no se envían nuevos resúmenes para esa cuenta

### Requirement: Comunicar los límites de entrega
El sistema SHALL informar que el resumen depende del permiso, del navegador y del dispositivo y que no garantiza la entrega; SHALL solicitar una presentación silenciosa cuando la plataforma lo permita.

#### Scenario: El servicio push no entrega el aviso
- **WHEN** el navegador o dispositivo no recibe una notificación enviada
- **THEN** las novedades permanecen disponibles en el indicador de la aplicación y no se afirma que fueron leídas
