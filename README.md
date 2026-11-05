# Moovi CLI

Herramienta de línea de comandos para consultar **Moovi**, la plataforma Moodle de la Universidade de Vigo, en **modo de solo lectura** y a través de su API oficial de servicios web.

Permite listar tus cursos, ver el contenido de una asignatura, consultar el alumnado matriculado, revisar las tareas y leer el foro de noticias. No hace *scraping* y no modifica nada en Moovi.

> Documentación técnica: [`docs/architecture.md`](docs/architecture.md).

## Requisitos

- [conda](https://docs.conda.io/) (Miniconda o Anaconda).
- Una cuenta de Moovi con contraseña propia. Si tu cuenta solo admite SSO, consulta la sección [Token manual](#token-manual-sso).

## Instalación

```bash
conda env create -f environment.yml
conda activate moovi
pip install -e .
```

> **Entorno activo:** `moovi` solo está disponible dentro del entorno conda.
> Si trabajas en una shell persistente, usa `conda activate moovi`.
> Si cada comando se ejecuta en una shell nueva (agentes, scripts, CI), usa
> `conda run -n moovi --no-capture-output moovi ...`.

Comprueba que funciona:

```bash
conda activate moovi
moovi --version
moovi --help
```

O sin activar el entorno:

```bash
conda run -n moovi --no-capture-output moovi --version
```

## Configuración

Copia el fichero de ejemplo:

```bash
cp .env.example .env
```

La forma recomendada es dejar solo la URL y, opcionalmente, el usuario. **No hace falta guardar la contraseña**: `moovi login` la pide por terminal y guarda únicamente el token.

```dotenv
MOOVI_URL=https://moovi.uvigo.gal
# MOOVI_USER=tu_usuario
```

- Si defines `MOOVI_USER`, se usa como valor por defecto al preguntar.
- Si no lo defines, la CLI recuerda el usuario guardado con el token.
- `MOOVI_PASSWORD` solo es necesaria para `moovi login --no-input` en scripts o CI. No la guardes si vas a usar el login interactivo.

`.env` está en `.gitignore`: no se sube al repositorio. La contraseña nunca se pasa por argumentos de línea de comandos ni se guarda en disco.

`moovi` lee `.env` del directorio desde el que se ejecuta. Ejecútalo desde la raíz del repositorio o exporta las variables `MOOVI_*` en el entorno.

También puedes definir esas variables en el entorno; tienen prioridad sobre `.env`.

### Token manual (SSO)

Si el login por contraseña no funciona porque tu cuenta usa SSO:

1. Entra en Moovi con el navegador.
2. Abre <https://moovi.uvigo.gal/user/managetoken.php>.
3. Copia el token del servicio **Moodle mobile**.
4. Añádelo a `.env`:

```dotenv
MOOVI_TOKEN=el_token_copiado
```

Con `MOOVI_TOKEN` no hace falta `MOOVI_PASSWORD`.

## Uso rápido

```bash
conda activate moovi   # o usa `conda run -n moovi --no-capture-output moovi ...`
moovi login
moovi courses
moovi contents 12345
moovi students 12345
moovi assignments 12345
moovi announcements 12345

# Para componer con herramientas Unix
moovi courses --format raw | grep -i "matemáticas"
```

## Comandos

### `moovi login`

Autentica contra Moovi, valida el token y lo guarda en `~/.cache/moovi/token.json` con permisos `0600`.

Si no hay una sesión válida, pide usuario y contraseña por terminal. La contraseña se introduce sin eco y no se guarda.

```bash
moovi login             # interactivo si no hay token válido
moovi login --force     # vuelve a pedir credenciales
moovi login --no-input  # usa MOOVI_USER/MOOVI_PASSWORD del entorno (scripts/CI)
```

Si ya hay un token válido, `moovi login` no pregunta nada. Usa `--force` para cambiar de cuenta o renovar la sesión.

### `moovi whoami`

Muestra tu identidad y la versión de Moodle.

```bash
moovi whoami
```

```
ID: 12345
USUARIO: usuario
NOMBRE: Nombre Apellido
SITIO: Moovi — 4.5 (Build: 20241007)
VERSIÓN: 4.5 (Build: 20241007)
FUNCIONES: 138
```

### `moovi courses`

Lista los cursos en los que estás matriculado.

```bash
moovi courses
moovi courses --limit 10
moovi courses --json
```

```
ID     SHORTNAME  NOMBRE                 VISIBLE
-----  ---------  ---------------------  -------
12345  M1         Matemáticas I          sí
12346  M2         Matemáticas II         no
```

### `moovi contents COURSE_ID`

Muestra las secciones y actividades de un curso.

```bash
moovi contents 12345
moovi contents 12345 --json
```

```
ID  SECCIÓN  RESUMEN       MÓDULOS
--  -------  ------------  ------------------------
1   Tema 1   Introducción  [forum] Foro de avisos
                           [resource] Apuntes (oculta)
```

En JSON, cada sección mantiene sus módulos como objetos, y el resumen incluye `summary` (HTML) y `summary_text` (texto).

### `moovi students COURSE_ID`

Lista las personas matriculadas y sus roles. **Por defecto omite el correo electrónico.**

```bash
moovi students 12345
moovi students 12345 --emails
moovi students 12345 --json
```

```
ID   NOMBRE    APELLIDOS    GRUPOS                                      ROLES        ÚLTIMO ACCESO
---  --------  -----------  ------------------------------------------  -----------  -------------------
7    Ana       Alumna       PROII_1 (Laboratorio); MODALIDAD_GLOBAL     Alumno/a     2023-11-14 22:13 UTC
8    Profesor  Uno          PROII_A (Teoría)                            Profesor/a   2023-11-14 22:13 UTC
```

Los grupos son los que el profesorado crea en *Participantes > Grupos*. Una persona puede estar en varios.

En JSON, los nombres van separados, `full_name` se calcula y los grupos son una lista de objetos:

```json
{
  "first_name": "Ana",
  "last_name": "Alumna",
  "full_name": "Ana Alumna",
  "groups": [{"id": 146, "name": "PROII_1 (Laboratorio)"}],
  "roles": [{"id": 5, "short_name": "student", "name": ""}]
}
```

La CLI usa `name` del rol si viene informado y, si no, traduce `short_name` para la tabla. Moovi deja `name` vacío en roles como `student` o `editingteacher`.

### `moovi assignments COURSE_ID`

Lista las tareas del curso con sus fechas.

```bash
moovi assignments 12345
moovi assignments 12345 --json
```

```
ID   NOMBRE       ENTREGA              CIERRE  NOTA MÁX.
---  -----------  -------------------  ------  ----------
501  Práctica 1   2024-01-01 00:00 UTC  —       100
```

## Manejo del foro de noticias de Moovi

Moovi crea automáticamente en cada materia un foro de noticias al que se suscriben obligatoriamente todos los participantes. Se usa para enviar avisos al alumnado.

`moovi announcements` localiza ese foro por su tipo (`news`), no por su nombre, porque el nombre cambia con el idioma o puede renombrarse. No es un gestor genérico de foros: está pensado para el foro de noticias de Moovi.

```bash
moovi announcements 12345
moovi announcements 12345 --limit 20
moovi announcements 12345 --json
moovi announcements 12345 --format raw
```

Sin `--limit`, muestra los 10 anuncios más recientes. Si una materia no tiene foro de noticias, el comando lo indica y lista los foros disponibles para usar con `--forum-id`.

```
ID     FECHA                 AUTOR                 ASUNTO                                RESPUESTAS
-----  --------------------  --------------------  ------------------------------------  ----------
63251  2026-07-13 08:51 UTC  Daniel González Peña  PROII: Notas finales de la convocatoria  0
```

En Moovi el foro suele llamarse `Foro de novas` o `Foro de anuncios`, pero el nombre no es fiable. El identificador estable es `type = "news"` y, como refuerzo, `forcesubscribe = 1`.

Si hay varios foros de noticias y no se puede elegir uno solo, el comando muestra los candidatos y pide elegir con `--forum-id`:

```bash
moovi announcements 12345 --forum-id 2217
```

También puedes usar `--forum-id` si la materia no tiene un foro `news` y quieres consultar otro foro concreto.

### `moovi announcement-content ANNOUNCEMENT_ID`

Muestra el contenido de un anuncio. El id es el que aparece en la columna `ID` de `moovi announcements`.

```bash
moovi announcement-content 63251
moovi announcement-content 63251 --json
moovi announcement-content 63251 --format raw
```

```
ID: 63251
DISCUSIÓN: 48026
ASUNTO: PROII: Notas finales de la convocatoria de julio
AUTOR: Daniel González Peña
FECHA: 2026-07-13 08:51 UTC
MODIFICADO: 2026-07-13 08:51 UTC
MENSAJE: Se han publicado en Moovi las notas...
  La revisión será...
```

En JSON se incluyen las dos versiones del mensaje:

- `message`: HTML original de Moodle.
- `message_text`: texto limpio, con párrafos.

En `--format raw` se usa `message_text` aplanado a una línea para no romper el CSV.

## Opciones comunes

| Opción | Descripción |
|---|---|
| `--format table` | Salida legible para humanos. Es el formato por defecto. |
| `--format json` | JSON por `stdout`, pensado para agentes y scripts. |
| `--format raw` | CSV plano, pensado para componer con `grep`, `sort`, `cut` o `awk`. |
| `--json` | Alias de `--format json`. |
| `--limit N` | Limita el número de elementos de los listados. |

Con `--format json`, la estructura usa los nombres del dominio (`short_name`, `full_name`, `due_date`...). **El HTML de Moodle se conserva tal cual**; la tabla y el CSV lo convierten a texto. Cuando un campo HTML necesita una versión legible en JSON, se añade como `<campo>_text` sin sustituir al original (`summary_text`, `message_text`).

## Filosofía: la CLI no filtra, tú compones

`moovi` no incluye `--role`, `--search` ni `--sort`. Todo eso se resuelve con `grep`, `sort`, `cut` o `jq` sobre `--format raw` o `--format json`. Así la CLI se mantiene pequeña y predecible.

```bash
# Buscar un curso por nombre
moovi courses --format raw | grep -i "matemáticas"

# Alumnado de un curso (la columna roles usa los shortname de Moodle)
moovi students 1686 --format raw | grep ',student'

# Profesorado
moovi students 1686 --format raw | grep -E ',(editingteacher|teacher)'

# Alumnado de un grupo concreto
moovi students 1686 --format raw | grep ',PROII_1 (Laboratorio),'

# Alumnado ordenado por apellidos
moovi students 1686 --format raw | tail -n +2 | sort -t, -k3

# Tareas ordenadas por fecha de entrega
moovi assignments 1686 --format raw | tail -n +2 | sort -t, -k4

# Quedarse solo con el shortname de los cursos
moovi courses --format raw | tail -n +2 | cut -d, -f2

# Filtro estructurado con jq
moovi students 1686 --json \
  | jq -r '.[] | select(any(.roles[]; .short_name == "student")) | [.id, .full_name] | @tsv'
```

`--format raw` genera CSV con cabecera, fechas ISO-8601, booleanos `true`/`false` y los roles separados por `;`. Las comas dentro de un campo se entrecomillan; para consultas complejas sobre nombres con comas, `--format json` + `jq` es más robusto que `cut`.

Columnas de `--format raw`:

| Comando | Columnas |
|---|---|
| `whoami` / `login` | `user_id, username, full_name, site_name, release, functions_count` |
| `courses` | `id, short_name, full_name, visible, start_date` |
| `contents` | `section_id, section_name, summary_text, modules` |
| `students` | `id, first_name, last_name, groups, roles, last_access, email` |
| `assignments` | `id, course_id, name, due_date, cutoff_date, max_grade` |
| `announcements` | `id, created, author, subject, num_replies, pinned, locked` |
| `announcement-content` | `id, discussion_id, subject, author, created, modified, message_text` |

En `contents`, se genera una fila por sección y la columna `modules` une los módulos con `;` en formato `mod_name:nombre:1|0`. En `students`, la columna `email` existe siempre y queda vacía salvo que uses `--emails`.

La columna `groups` une los grupos con `;`. Si un nombre de grupo contuviera `;`, se sustituye por `#` para que no rompa el campo. Las comas, comillas y saltos de línea se entrecomillan según el estándar CSV.

## Códigos de salida

| Código | Significado |
|---|---|
| `0` | Correcto. |
| `2` | Error de configuración o autenticación (`.env`, credenciales, token). |
| `3` | Error de la API o de red. |
| `4` | Moovi ha denegado el acceso (permisos insuficientes). |

Con `--format json` (o `--json`), los errores se escriben en `stderr` como:

```json
{"error": {"type": "AuthorizationError", "code": null, "message": "..."}}
```

## Problemas frecuentes

**`moovi: command not found`**

El entorno no está activo. Usa `conda activate moovi` o, desde una shell nueva:

```bash
conda run -n moovi --no-capture-output moovi courses --json
```

Si sigue fallando, entra en el entorno y ejecuta `pip install -e .`.

**`Credenciales incorrectas`**

Revisa el usuario y la contraseña que introduces en `moovi login`. Si tu cuenta solo usa SSO, configura `MOOVI_TOKEN` como se explica arriba.

**`No hay sesión válida. Ejecuta moovi login`**

No hay token cacheado y la CLI no tiene credenciales para renovarlo:

```bash
moovi login
```

**`El token de Moovi no es válido o ha caducado`**

Fuerza un login nuevo:

```bash
moovi login --force
```

Si no tienes contraseña, renueva `MOOVI_TOKEN`.

**`Moovi ha denegado el acceso`**

La cuenta no tiene permisos para esa función en ese curso (por ejemplo, no eres profesor del curso). Comprueba el rol en Moovi.

**Error de red o HTTP 5xx**

Moovi no responde o está en mantenimiento. La CLI reintenta una vez los errores 5xx; si persiste, espera y vuelve a intentarlo.

## Seguridad y datos personales

- El token se guarda en `~/.cache/moovi/token.json` con permisos `0600`; la contraseña no se guarda.
- `moovi login` pide la contraseña por terminal con `getpass`, sin eco y sin dejarla en el historial.
- Un agente no debe pedirte la contraseña por chat: si no hay sesión, debe indicarte que ejecutes `moovi login`.
- El cliente limita las funciones a una lista de solo lectura.
- `students` oculta los correos salvo que uses `--emails`.
- Los datos de alumnado que consultes pueden acabar en el contexto de un agente o en los registros de tu terminal. Pide solo lo necesario y no vuelques listados completos sin motivo.

## Desarrollo

```bash
pytest                # unitarios, integración y e2e con Moodle falso
pytest -m live        # contra Moovi real (requiere .env y MOOVI_E2E=1)
```

Antes de tocar código, lee [`docs/architecture.md`](docs/architecture.md) y [`AGENTS.md`](AGENTS.md).
