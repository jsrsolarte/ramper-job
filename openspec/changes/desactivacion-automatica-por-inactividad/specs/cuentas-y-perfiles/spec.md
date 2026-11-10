# Spec Delta

## ADDED Requirements

### Requirement: Desactivar cuentas de aspirantes tras inactividad
El sistema SHALL desactivar automáticamente una cuenta de aspirante cuando complete siete días consecutivos sin actividad autenticada en la aplicación.

#### Scenario: Una cuenta supera el plazo de inactividad
- **WHEN** una cuenta de aspirante no registra actividad autenticada durante siete días consecutivos
- **THEN** el proceso periódico desactiva la cuenta, conserva su historial y datos, y registra que la desactivación fue automática por inactividad

#### Scenario: Una cuenta tiene actividad reciente
- **WHEN** una persona autenticada usa la aplicación antes de completar siete días de inactividad
- **THEN** el sistema actualiza su última actividad y no la desactiva por el plazo anterior

#### Scenario: Una cuenta recién creada aún no ha iniciado sesión
- **WHEN** la cuenta de aspirante no ha registrado actividad desde su creación o activación
- **THEN** el plazo de siete días se cuenta desde la fecha de creación o última activación de la cuenta

#### Scenario: La cuenta administradora está inactiva
- **WHEN** la cuenta de administración no registra actividad durante siete días
- **THEN** este proceso no la desactiva

#### Scenario: Una tarea de fondo realiza trabajo
- **WHEN** un proceso automático de la plataforma se ejecuta sin interacción de la persona usuaria
- **THEN** esa ejecución no cuenta como actividad de la cuenta de aspirante

### Requirement: Reactivar una cuenta desactivada automáticamente
El sistema SHALL permitir a la persona administradora reactivar una cuenta desactivada por inactividad sin eliminar ni reconstruir sus datos.

#### Scenario: Administración reactiva la cuenta
- **WHEN** la persona administradora activa desde la consola una cuenta desactivada automáticamente
- **THEN** el sistema restaura el acceso, conserva la información asociada y reinicia el cómputo de inactividad desde la reactivación
