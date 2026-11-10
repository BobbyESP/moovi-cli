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
| `domain` | Modelos, value objects, errores e invariantes. Sin I/O. `Participant` guarda `id_number`, `first_name`, `last_name` y `groups`; `full_name` es una propiedad derivada. | Solo stdlib. |
| `logic` | Casos de uso, sesión autenticada y puertos. | `domain`, `logic`. |
| `network` | Cliente REST de Moodle, mapeo de respuestas y errores. | `domain`, `logic`, stdlib. |
| `infra` | Configuración (`.env`) y persistencia del token. | `domain`, `logic`, stdlib. |
| `cli` | `argparse`, renderizado y composition root. | Todo. |

La regla se comprueba automáticamente en `tests/unit/test_architecture.py`: si una capa importa algo prohibido, los tests fallan.

## Estructura

```
src/moovi/
├── domain/
│   ├── models.py      # SiteInfo, Course, Section, Module, Role, Participant, Assignment, Forum, Announcement
│   ├── values.py      # Token (repr redactado)
│   └── errors.py      # errores de dominio
├── logic/
│   ├── ports.py       # MoodleGateway, TokenStore (Protocol)
│   ├── session.py     # MoodleSession: token, login y reintento
│   └── services/      # AuthService, CatalogService, PeopleService, AssignmentService, AnnouncementService
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
    ├── text.py        # HTML → texto, aplanado
    ├── tables/        # adaptadores dominio → tabla de datos
    │   ├── base.py    # Column, RichValue, Table
    │   ├── roles.py   # etiquetas de roles
    │   └── ...        # una tabla por entidad
    ├── formats/       # renderizadores genéricos
    │   ├── base.py    # Protocol Formatter
    │   ├── table.py   # tabla para humanos
    │   ├── json.py    # JSON para agentes
    │   └── csv.py     # raw (CSV) para grep/sort/awk
    ├── errors.py      # errores de presentación
    └── exit_codes.py  # error de dominio → código de salida
```

## Flujo de una orden

Ejemplo con `moovi courses --json`:

1. `cli/main.py` construye el parser y carga `Settings` con `load_settings()`.
2. `cli/context.py` instancia `MoodleRestClient`, `FileTokenStore` y `MoodleSession`; es el único punto de composición.
3. `CatalogService.list_courses()` pide la sesión.
4. `MoodleSession` resuelve el token: `MOOVI_TOKEN` → caché (con su usuario) → login con credenciales del entorno.
5. Si Moodle responde `invalidtoken`, la sesión hace **un** login nuevo y reintenta.
6. `MoodleRestClient` llama a `core_enrol_get_users_courses`, mapea el JSON a `Course` y devuelve el resultado.
7. `cli/commands/courses.py` limita la lista, la envuelve en `CoursesTable` y llama a `formatter.render(table)`.

La lógica no imprime nada: los servicios devuelven objetos de dominio y la CLI decide el formato.

## Tablas de datos y formatters

El formato es una **estrategia de presentación**, no un puerto de la arquitectura. Los casos de uso no saben si el resultado se pinta como tabla, JSON o CSV.

Los comandos construyen una **tabla de datos** que implementa `Table`:

```python
class Table(Protocol):
    columns: Sequence[Column]   # key, header y visibilidad por formato
    rows: Sequence[Sequence[object]]
    single_row: bool
```

- Las columnas nombran; las filas contienen valores en orden.
- Los valores son objetos, no strings: enteros, fechas, listas o `RichValue`.
- `RichValue` aporta `raw` para JSON, `text` para tabla y `csv_text` para CSV.
- Los formatters solo saben renderizar una `Table`; no conocen entidades concretas.

`Formatter` queda cerrado:

```python
class Formatter(Protocol):
    def render(self, table: Table) -> None: ...
```

- **Añadir un comando** = crear una tabla nueva. No se toca ningún formatter.
- **Añadir un formato** = crear una clase nueva que implemente `render`. No se toca ninguna tabla.
- Las implementaciones oficiales heredan explícitamente de `Table`/`Formatter` para que el contrato sea visible; el tipado sigue siendo estructural para los dobles de test.
- Los tests de arquitectura comprueban que `formats/` no importa dominio ni `HTMLParser`, y que `tables/` no importa `formats/`.

`--json` es un alias de `--format json`. `--format raw` genera CSV con cabecera, fechas ISO-8601, booleanos `true`/`false` y listas separadas por `;` (grupos y roles). En la columna `groups`, un `;` dentro de un nombre se sustituye por `#` para no romper el campo.

No se añaden filtros de conveniencia (`--role`, `--search`, `--sort`): se resuelven con `grep`, `sort`, `cut`, `awk` o `jq` sobre `raw`/`json`.

## Puertos y adaptadores

```python
class MoodleGateway(Protocol):
    def login(self, username: str, password: str) -> Token: ...
    def site_info(self, token: Token) -> SiteInfo: ...
    def users_courses(self, token: Token, user_id: int) -> list[Course]: ...
    def course_contents(self, token: Token, course_id: int) -> list[Section]: ...
    def enrolled_users(self, token: Token, course_id: int) -> list[Participant]: ...
    def assignments(self, token: Token, course_ids: Sequence[int]) -> list[Assignment]: ...
    def course_forums(self, token: Token, course_id: int) -> list[Forum]: ...
    def forum_discussions(
        self, token: Token, forum_id: int, limit: int
    ) -> list[Announcement]: ...
    def discussion_post(
        self, token: Token, post_id: int
    ) -> AnnouncementContent: ...

class TokenStore(Protocol):
    def load(self, site: str, username: str | None = None) -> Token | None: ...
    def load_username(self, site: str) -> str | None: ...
    def save(self, site: str, username: str, token: Token) -> None: ...
    def clear(self, site: str, username: str | None = None) -> None: ...
```

- `MoodleGateway` es el **puerto de salida** del núcleo.
- `MoodleRestClient(MoodleGateway)` es su **adaptador** REST.
- `TokenStore` es el puerto de persistencia del token.
- `FileTokenStore(TokenStore)` es su adaptador en fichero.
- `MoodleSession` consume el puerto `MoodleGateway`; `cli/context.py` inyecta el adaptador.
- Las implementaciones oficiales heredan explícitamente del `Protocol` para que la relación puerto/adaptador sea visible; el tipado sigue siendo estructural para los dobles de test.
- Los tests unitarios sustituyen ambos puertos por dobles en memoria.

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
| `NoAnnouncementsForumError` | La materia no tiene foro de noticias. | 2 |
| `AmbiguousForumError` | Varios foros de noticias sin desempate. | 2 |

Moodle devuelve **HTTP 200** en sus errores; el discriminante es `errorcode` (o `exception`). Esa traducción vive en `network/errors.py`.

## Ciclo de vida del token

1. `MOOVI_TOKEN` (entorno o `.env`) tiene prioridad.
2. Si no hay token explícito, se lee `~/.cache/moovi/token.json` (o `$XDG_CACHE_HOME/moovi/token.json`). Si no hay `MOOVI_USER`, se adopta el usuario guardado junto al token.
3. Si no hay token y hay usuario/contraseña en el entorno, se llama a `POST /login/token.php` con `service=moodle_mobile_app`.
4. `moovi login` permite introducir usuario y contraseña por terminal. La contraseña se lee con `getpass` y no se persiste; solo se guarda el token.
5. `moovi login --no-input` usa `MOOVI_USER`/`MOOVI_PASSWORD` del entorno para scripts y CI.
6. El token se guarda en el fichero con permisos `0600`.
7. Ante `invalidtoken`, `MoodleSession` hace un único login nuevo y reintenta la operación si hay credenciales.
8. Si no hay credenciales para renovar, se propaga `ConfigError` indicando que se ejecute `moovi login`.

## Foro de noticias de Moovi

`AnnouncementService` localiza el foro de noticias por `type == "news"`, nunca por el nombre. Si hay varios candidatos, prefiere el que tiene `forcesubscribe == 1`; si el empate persiste, pide `--forum-id`. Un id explícito también permite consultar otro foro del curso.

La lectura usa `mod_forum_get_forums_by_courses` y `mod_forum_get_forum_discussions`, ambas en la allowlist de solo lectura. El contenido de un anuncio se obtiene con `mod_forum_get_discussion_post` usando el id del post que muestra el listado. La publicación queda fuera de esta fase: sería `mod_forum_add_discussion` desde una superficie de escritura separada.

## Modo de solo lectura

`network/rest.py` declara `READ_ONLY_FUNCTIONS`. `MoodleRestClient.call()` rechaza cualquier función que no esté ahí, aunque un comando futuro la invoque por error. La CLI no expone ningún comando de escritura en esta fase.

Para añadir una función hay que hacerlo en tres sitios: la allowlist, el puerto y el adaptador, y el caso de uso. No hay atajo de `call` genérico.

## Añadir un comando

1. Añade el método tipado al puerto `MoodleGateway` (`logic/ports.py`).
2. Impleméntalo en `MoodleRestClient` y añade el mapeo en `network/mappers.py`.
3. Añade el caso de uso en `logic/services/` (o amplía uno existente).
4. Crea la tabla de datos en `cli/tables/` (`columns`, `rows`, `single_row`).
5. Registra el subcomando en `cli/commands/` y llama a `formatter.render(tabla)`.
6. Añade la función a `READ_ONLY_FUNCTIONS`.
7. Tests: tabla, mapeo, integración contra el Moodle falso y e2e de la CLI.
8. Actualiza `README.md` y este documento si cambia el flujo o la arquitectura.

## Contenido HTML

La regla es única:

- **JSON** conserva el HTML original de Moodle.
- **Tabla** convierte HTML a texto conservando párrafos.
- **CSV** convierte HTML a texto y lo aplana a una línea.
- Si un campo necesita versión legible en JSON, se añade como `<campo>_text` sin sustituir el HTML original.

La conversión vive en `cli/text.py` (`html_to_text`, `flatten_text`). Las tablas usan `RichValue(raw, text, csv_text, json_text)` para dar las representaciones necesarias; los formatters no implementan parsing propio.

## Tests

- **Unitarios:** dominio, lógica con dobles, mapeo, parámetros, configuración, permisos del token, selección del foro de noticias, tablas de datos y formatters genéricos con `StringIO`. Incluyen el test de arquitectura.
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
| Tablas de datos + formatters genéricos | Añadir un comando no toca formatters; añadir un formato no toca tablas. |
| Valores de fila como objetos | JSON conserva números, fechas y listas; tabla/CSV los convierten a texto. |
| JSON conserva el HTML original | La tabla y el CSV usan texto legible; los campos `<campo>_text` son adicionales. |
| Sin filtros de conveniencia | Se componen con `grep`/`sort`/`awk` sobre `--format raw` o `jq` sobre JSON. |
| Moodle falso en tests | E2E deterministas y sin credenciales reales. |
| `uv` + `uv.lock` | Entorno reproducible y rápido sin necesidad de binarios no Python. Ver [ADR 0001](decisions/0001-migrar-a-uv.md). |
