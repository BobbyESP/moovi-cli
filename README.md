# Moovi CLI

Herramienta de línea de comandos para consultar **Moovi**, la plataforma Moodle de la Universidade de Vigo, en **modo de solo lectura** y a través de su API oficial de servicios web.

Permite listar tus cursos, ver el contenido de una asignatura, consultar el alumnado matriculado y revisar las tareas. No hace *scraping* y no modifica nada en Moovi.

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

Comprueba que funciona:

```bash
moovi --version
moovi --help
```

## Configuración

Copia el fichero de ejemplo y rellena tus datos:

```bash
cp .env.example .env
```

```dotenv
MOOVI_URL=https://moovi.uvigo.gal
MOOVI_USER=tu_usuario
MOOVI_PASSWORD=tu_contrasena
```

`.env` está en `.gitignore`: no se sube al repositorio. La contraseña nunca se pasa por argumentos de línea de comandos ni se guarda en la caché del token.

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
moovi login
moovi courses
moovi contents 12345
moovi students 12345
moovi assignments 12345

# Para componer con herramientas Unix
moovi courses --format raw | grep -i "matemáticas"
```

## Comandos

### `moovi login`

Autentica contra Moovi, valida el token y lo guarda en `~/.cache/moovi/token.json` con permisos `0600`.

```bash
moovi login
moovi login --force   # ignora el token guardado
```

### `moovi whoami`

Muestra tu identidad y la versión de Moodle.

```bash
moovi whoami
```

```
Usuario: Nombre Apellido (usuario, id 12345)
Sitio: Moovi — 4.5 (Build: 20241007)
Funciones disponibles: 138
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
## Tema 1
   Introducción
  - [forum] Foro de avisos
  - [resource] Apuntes (oculta)
```

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

## Opciones comunes

| Opción | Descripción |
|---|---|
| `--format table` | Salida legible para humanos. Es el formato por defecto. |
| `--format json` | JSON por `stdout`, pensado para agentes y scripts. |
| `--format raw` | CSV plano, pensado para componer con `grep`, `sort`, `cut` o `awk`. |
| `--json` | Alias de `--format json`. |
| `--limit N` | Limita el número de elementos de los listados. |

Con `--format json`, la estructura usa los nombres del dominio (`short_name`, `full_name`, `due_date`...). Los resúmenes de Moodle se devuelven tal cual, incluido el HTML; la salida de tabla los limpia.

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
| `contents` | `section_id, section_name, module_id, module_name, mod_name, visible, url` |
| `students` | `id, first_name, last_name, groups, roles, last_access, email` |
| `assignments` | `id, course_id, name, due_date, cutoff_date, max_grade` |

En `contents`, se genera una fila por módulo. Las secciones sin módulos aparecen con los campos de módulo vacíos. En `students`, la columna `email` existe siempre y queda vacía salvo que uses `--emails`.

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

**`Credenciales incorrectas`**

Revisa `MOOVI_USER` y `MOOVI_PASSWORD`. Si tu cuenta solo usa SSO, configura `MOOVI_TOKEN` como se explica arriba.

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
- El cliente limita las funciones a una lista de solo lectura.
- `students` oculta los correos salvo que uses `--emails`.
- Los datos de alumnado que consultes pueden acabar en el contexto de un agente o en los registros de tu terminal. Pide solo lo necesario y no vuelques listados completos sin motivo.

## Desarrollo

```bash
pytest                # unitarios, integración y e2e con Moodle falso
pytest -m live        # contra Moovi real (requiere .env y MOOVI_E2E=1)
```

Antes de tocar código, lee [`docs/architecture.md`](docs/architecture.md) y [`AGENTS.md`](AGENTS.md).
