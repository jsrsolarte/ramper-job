# Cuentas y perfiles Specification

## Purpose

Permite que cada familiar use una cuenta administrada para mantener su información de búsqueda laboral y consultar únicamente sus propios resultados.

## Requirements

### Requirement: Enrolar aspirantes mediante invitaciones
El sistema SHALL permitir que la persona administradora invite aspirantes con enlaces individuales de un solo uso, manteniendo cerrado el auto-registro público sin invitación válida.

#### Scenario: Administrador genera una invitación
- **WHEN** la persona administradora crea una invitación e indica el correo de la persona destinataria
- **THEN** el sistema genera un enlace único válido durante siete días, asociado a ese correo, y todavía no crea una cuenta

#### Scenario: Administrador comparte el enlace
- **WHEN** se genera una invitación correctamente
- **THEN** el sistema muestra el enlace una sola vez para que la administración lo copie y lo envíe por su canal habitual, sin enviar un correo automáticamente

#### Scenario: Invitado completa su cuenta
- **WHEN** la persona destinataria abre una invitación vigente y proporciona un usuario y contraseña válidos
- **THEN** el sistema crea una cuenta individual activa asociada al correo de la invitación y consume el enlace

#### Scenario: Invitación inválida, vencida, revocada o utilizada
- **WHEN** una persona intenta aceptar una invitación que no existe, venció, fue revocada o ya se utilizó
- **THEN** el sistema no crea la cuenta y ofrece solicitar una nueva invitación a la administración

#### Scenario: El formulario de invitación tiene errores
- **WHEN** una persona envía un usuario repetido o una contraseña inválida usando una invitación todavía vigente
- **THEN** el sistema muestra los errores y conserva la invitación disponible hasta su vencimiento o aceptación exitosa

#### Scenario: La persona intenta auto-registrarse con invitación
- **WHEN** una persona intenta crear una cuenta sin una invitación válida
- **THEN** el sistema no permite crear la cuenta

#### Scenario: Administrador revoca o reemplaza una invitación
- **WHEN** la persona administradora revoca una invitación pendiente o genera un reemplazo
- **THEN** el enlace revocado o reemplazado deja de permitir el registro

#### Scenario: Administrador desactiva una cuenta
- **WHEN** la persona administradora desactiva la cuenta de un aspirante
- **THEN** el sistema revoca su acceso sin eliminar su historial ni sus datos asociados

#### Scenario: Administrador reactiva una cuenta
- **WHEN** la persona administradora reactiva una cuenta previamente desactivada
- **THEN** el sistema permite que esa persona vuelva a iniciar sesión y conserva su información existente

### Requirement: Cuentas administradas
El sistema SHALL permitir que la única persona administradora cree, desactive y reactive cuentas de familiares, sin habilitar el auto-registro público.

#### Scenario: Administrador crea una cuenta
- **WHEN** la persona administradora registra una cuenta para un familiar
- **THEN** el sistema crea el acceso individual y permite que esa persona inicie sesión

#### Scenario: Persona intenta auto-registrarse
- **WHEN** una persona sin cuenta intenta registrarse desde el acceso público
- **THEN** el sistema no permite crear una cuenta

#### Scenario: Administrador desactiva una cuenta
- **WHEN** la persona administradora desactiva la cuenta de un familiar
- **THEN** el sistema revoca su acceso sin eliminar su historial ni sus datos asociados

#### Scenario: Administrador reactiva una cuenta
- **WHEN** la persona administradora reactiva una cuenta previamente desactivada
- **THEN** el sistema permite que esa persona vuelva a iniciar sesión y conserva su información existente

### Requirement: Aislamiento de información por cuenta
El sistema SHALL mostrar a cada familiar solo sus propios CV, preferencias y vacantes analizadas.

#### Scenario: Persona consulta su dashboard
- **WHEN** una persona autenticada abre su dashboard
- **THEN** el sistema muestra únicamente su información y resultados

#### Scenario: Persona intenta consultar información ajena
- **WHEN** una persona autenticada solicita información asociada a otra cuenta
- **THEN** el sistema deniega el acceso y no revela esa información

### Requirement: CV y preferencias de búsqueda
El sistema SHALL permitir a cada persona cargar o actualizar su CV y definir preferencias que orienten sus búsquedas de vacantes.

#### Scenario: Persona actualiza su perfil
- **WHEN** la persona guarda un CV o cambia sus preferencias
- **THEN** el sistema conserva la revisión vigente para las siguientes búsquedas y análisis

#### Scenario: Se actualiza un perfil ya analizado
- **WHEN** la persona modifica su CV o sus preferencias
- **THEN** los análisis existentes conservan la referencia a la revisión con que se generaron y los análisis posteriores usan la revisión vigente

### Requirement: Descarga privada del CV
El sistema SHALL permitir la descarga del CV únicamente a su propietario autenticado.

#### Scenario: El propietario descarga su CV
- **WHEN** el aspirante autenticado solicita el archivo vigente de su perfil
- **THEN** el sistema entrega el archivo asociado a ese perfil

#### Scenario: Otra cuenta solicita el archivo
- **WHEN** una cuenta distinta o una persona no autenticada solicita el CV
- **THEN** el sistema no revela ni entrega el archivo

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
