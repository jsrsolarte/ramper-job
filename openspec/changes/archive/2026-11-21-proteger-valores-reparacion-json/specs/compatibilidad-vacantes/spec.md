# Spec Delta

## ADDED Requirements

### Requirement: Preservar literales durante la comprobación de reparaciones
El sistema SHALL verificar que una reparación JSON conserva las claves y los valores originales sin alterar el contenido de cadenas, incluso en estructuras anidadas. Si no puede demostrarlo, SHALL rechazar la reparación.

#### Scenario: Puntuación dentro de una cadena
- **WHEN** la respuesta original contiene `{"evidence": "texto, } y más",}` y la reparación cambia la evidencia a `texto} y más`
- **THEN** el sistema rechaza la reparación y no guarda el resultado

#### Scenario: Solo se corrige una coma fuera de la cadena
- **WHEN** la respuesta anterior se repara conservando exactamente el valor `texto, } y más`
- **THEN** el sistema puede aceptar la reparación tras comprobar equivalencia y aplicar las validaciones existentes

#### Scenario: Cadenas y escapes ambiguos
- **WHEN** la respuesta contiene comillas escapadas, barras inversas, secuencias Unicode, delimitadores o estructuras anidadas y la equivalencia no puede demostrarse
- **THEN** el sistema rechaza la reparación sin alterar ni inferir valores

#### Scenario: Se altera una clave o valor anidado
- **WHEN** la reparación añade, elimina o modifica una clave o un valor en cualquier nivel
- **THEN** el sistema rechaza la reparación y conserva la recuperación existente
