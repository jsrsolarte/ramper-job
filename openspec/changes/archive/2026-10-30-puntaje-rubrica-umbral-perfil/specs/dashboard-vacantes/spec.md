# Spec Delta

## MODIFIED Requirements

### Requirement: Vacantes ordenadas por compatibilidad
El dashboard SHALL mostrar las vacantes analizadas de la persona que alcanzan el puntaje mínimo configurado en su perfil, ordenadas desde el puntaje de compatibilidad más alto al más bajo.

#### Scenario: Hay varias vacantes analizadas
- **WHEN** la persona abre su dashboard y tiene varias vacantes analizadas que alcanzan el mínimo
- **THEN** el sistema las muestra en orden descendente de puntaje

#### Scenario: Vacante por debajo del mínimo
- **WHEN** una vacante tiene un puntaje inferior al mínimo configurado en el perfil
- **THEN** el sistema la excluye de los resultados del dashboard

#### Scenario: Se filtran resultados paginados
- **WHEN** la lista de vacantes se divide en páginas
- **THEN** el sistema aplica primero el mínimo de puntaje y después ordena y pagina las vacantes que lo alcanzan

#### Scenario: Puntaje mínimo igual a cero
- **WHEN** el perfil tiene un mínimo de 0
- **THEN** el sistema no excluye vacantes por su puntaje
