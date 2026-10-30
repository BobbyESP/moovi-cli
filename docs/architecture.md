# Arquitectura

Documento de alto nivel. El manual de usuario está en [`README.md`](../README.md).

## Objetivo

`moovi` es una CLI de solo lectura sobre la API de servicios web de Moodle. La arquitectura separa la interfaz (CLI) de los casos de uso, del dominio y del acceso a red, para que una futura GUI pueda reutilizar la lógica sin tocar el cliente HTTP.

## Capas

```
cli ──► logic ──► domain
 │        ▲
 │        │ (implementan puertos)
 └──► infra        network ──► domain + ports
```

| Capa | Responsabilidad | Puede importar |
|---|---|---|
| `domain` | Modelos, value objects, errores e invariantes. Sin I/O. | Solo stdlib. |
| `logic` | Casos de uso, sesión autenticada y puertos. | `domain`, `logic`. |
| `network` | Cliente REST de Moodle, mapeo de respuestas y errores. | `domain`, `logic`, stdlib. |
| `infra` | Configuración (`.env`) y persistencia del token. | `domain`, `logic`, stdlib. |
| `cli` | `argparse`, renderizado y composition root. | Todo. |

La regla se comprueba automáticamente en `tests/unit/test_architecture.py`: si una capa importa algo prohibido, los tests fallan.

## Estructura

```
src/moovi/
├── domain/
│   ├── models.py      # SiteInfo, Course, Section, Module, Role, Participant, Assignment
│   ├── values.py      # Token (repr redactado)
│   └── errors.py      # errores de dominio
├── logic/
│   ├── ports.py       # MoodleGateway, TokenStore (Protocol)
│   ├── session.py     # MoodleSession: token, login y reintento
│   └── services/      # AuthService, CatalogService, PeopleService, AssignmentService
├── network/
│   ├── rest.py        # MoodleRestClient(MoodleGateway)
│   ├── params.py      # flatten a notación Moodle
│   ├── mappers.py     # JSON de Moodle → modelos de dominio
│   └── errors.py      # errorcode de Moodle → error de dominio
├── infra/
│   ├── settings.py    # .env + entorno, validación de URL
│   └── token_store.py # fichero 0600
└── cli/
    ├── main.py        # parser y composition root
    ├── context.py     # build_services()
    ├── commands/      # un módulo por grupo de comandos
    ├── render.py      # tablas, JSON, HTML → texto
    └── exit_codes.py  # error de dominio → código de salida
```

## Flujo de una orden

Ejemplo con `moovi courses --json`:

1. `cli/main.py` construye el parser y carga `Settings` con `load_settings()`.
2. `cli/context.py` instancia `MoodleRestClient`, `FileTokenStore` y `MoodleSession`; es el único punto de composición.
3. `CatalogService.list_courses()` pide la sesión.
4. `MoodleSession` resuelve el token: `MOOVI_TOKEN` → caché → login.
5. Si Moodle responde `invalidtoken`, la sesión hace **un** login nuevo y reintenta.
6. `MoodleRestClient` llama a `core_enrol_get_users_courses`, mapea el JSON a `Course` y devuelve el resultado.
7. `cli/commands/courses.py` limita la lista y `render.py` emite JSON o tabla.

La lógica no imprime nada: los servicios devuelven objetos de dominio y la CLI decide el formato.

## Puertos y adaptadores

```python
class MoodleGateway(Protocol):
    def login(self, username: str, password: str) -> Token: ...
    def site_info(self, token: Token) -> SiteInfo: ...
    def users_courses(self, token: Token, user_id: int) -> list[Course]: ...
    def course_contents(self, token: Token, course_id: int) -> list[Section]: ...
    def enrolled_users(self, token: Token, course_id: int) -> list[Participant]: ...
    def assignments(self, token: Token, course_ids: Sequence[int]) -> list[Assignment]: ...

class TokenStore(Protocol):
    def load(self, site: str, username: str) -> Token | None: ...
    def save(self, site: str, username: str, token: Token) -> None: ...
    def clear(self, site: str, username: str) -> None: ...
```

- `MoodleRestClient` implementa `MoodleGateway`.
- `FileTokenStore` implementa `TokenStore`.
- Los tests unitarios sustituyen ambos por dobles en memoria.

## Errores

| Error de dominio | Origen | Código de salida |
|---|---|---|
| `ConfigError` | Falta configuración o URL inválida. | 2 |
| `InvalidCredentialsError` | `invalidlogin`. | 2 |
| `InvalidTokenError` | `invalidtoken` (tras reintentar). | 2 |
| `AuthorizationError` | `accessexception`, `nopermissions`... | 4 |
| `ReadOnlyViolation` | Función fuera de la allowlist. | 4 |
| `NetworkError` | HTTP 5xx, DNS, timeout. | 3 |
| `ApiError` | Cualquier otro `errorcode`. | 3 |

Moodle devuelve **HTTP 200** en sus errores; el discriminante es `errorcode` (o `exception`). Esa traducción vive en `network/errors.py`.

## Ciclo de vida del token

1. `MOOVI_TOKEN` (entorno o `.env`) tiene prioridad.
2. Si no hay token explícito, se lee `~/.cache/moovi/token.json` (o `$XDG_CACHE_HOME/moovi/token.json`).
3. Si no hay token y sí contraseña, se llama a `POST /login/token.php` con `service=moodle_mobile_app`.
4. El token se guarda en el fichero con permisos `0600`; la contraseña nunca se persiste.
5. Ante `invalidtoken`, `MoodleSession` hace un único login nuevo y reintenta la operación.
6. Si no hay contraseña para renovar, se propaga `ConfigError` con instrucciones.

## Modo de solo lectura

`network/rest.py` declara `READ_ONLY_FUNCTIONS`. `MoodleRestClient.call()` rechaza cualquier función que no esté ahí, aunque un comando futuro la invoque por error. La CLI no expone ningún comando de escritura en esta fase.

Para añadir una función hay que hacerlo en tres sitios: la allowlist, el puerto y el adaptador, y el caso de uso. No hay atajo de `call` genérico.

## Añadir un comando

1. Añade el método tipado al puerto `MoodleGateway` (`logic/ports.py`).
2. Impleméntalo en `MoodleRestClient` y añade el mapeo en `network/mappers.py`.
3. Añade el caso de uso en `logic/services/` (o amplía uno existente).
4. Registra el subcomando en `cli/commands/` y renderiza en `cli/render.py`.
5. Añade la función a `READ_ONLY_FUNCTIONS`.
6. Tests: unitario del mapeo, integración contra el Moodle falso y e2e de la CLI.
7. Actualiza `README.md` y este documento si cambia el flujo o la arquitectura.

## Tests

- **Unitarios:** dominio, lógica con dobles, mapeo, parámetros, configuración y permisos del token. Incluyen el test de arquitectura.
- **Integración:** `MoodleRestClient` contra un `ThreadingHTTPServer` local que emula `login/token.php` y `rest/server.php`.
- **E2E:** la CLI real en subprocess contra ese servidor falso, con `HOME` y `XDG_CACHE_HOME` temporales. Comprueban login, JSON, tablas, reintento de token, permisos, códigos de salida y que el token no se filtre.
- **Live:** `pytest -m live` con `MOOVI_E2E=1` y un `.env` real; desactivados por defecto.

## Decisiones de diseño

| Decisión | Motivo |
|---|---|
| Sin dependencias en runtime | Portabilidad y superficie mínima; solo stdlib. |
| Token en fichero `0600` | Predecible en cualquier Linux, sin depender del keyring del escritorio. |
| Allowlist de solo lectura | Un agente no puede escalar a escrituras por error. |
| Errores de dominio | La CLI traduce a códigos; la lógica no conoce `argparse`. |
| Moodle falso en tests | E2E deterministas y sin credenciales reales. |
| `conda` | Entorno reproducible elegido por el usuario. |
