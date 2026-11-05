---
name: Moovi
description: Consulta Moovi (Moodle de la Universidade de Vigo) en solo lectura mediante la CLI `moovi`: identidad, cursos, contenidos, alumnado y tareas. Úsalo cuando el usuario pida información de sus asignaturas en Moovi.
---

# Moovi

CLI de solo lectura sobre la API oficial de Moovi. No usa scraping y no modifica nada en la plataforma.

## Requisitos

- La CLI `moovi` debe estar disponible en el entorno conda `moovi`.
- Si cada comando se ejecuta en una shell nueva, no uses `conda activate`: usa
  `conda run -n moovi --no-capture-output moovi ...`.
- Debe haber un token válido en `~/.cache/moovi/token.json` (se crea con `moovi login`) o `MOOVI_TOKEN` en el entorno. `.env` solo necesita `MOOVI_URL` y, opcionalmente, `MOOVI_USER`.
- Ejecuta desde la raíz del repositorio para que se lea `.env`, o exporta las variables `MOOVI_*`.
- **Nunca pidas la contraseña por chat ni imprimas `.env` o el token.** Si no hay sesión, pide al usuario que ejecute `moovi login` en su terminal. No uses `--no-input` salvo que las credenciales ya estén en el entorno.

## Flujo

1. Comprueba la sesión:

   ```bash
   moovi whoami --json
   ```

   Si falla con “No hay sesión válida”, pide al usuario que ejecute `moovi login` en su terminal. No le pidas la contraseña.

2. Localiza el curso por su shortname o nombre:

   ```bash
   moovi courses --json
   ```

3. Consulta lo que pida el usuario:

   ```bash
   moovi contents <course_id> --json
   moovi participants <course_id> --json   # incluye groups y roles
   moovi assignments <course_id> --json
   moovi announcements <course_id> --json   # foro de noticias de Moovi
   moovi announcement-content <announcement_id> --json
   ```

4. Resume el resultado. No vuelques listados completos si basta con un resumen.

## Reglas

- Usa `--json` (o `--format json`) cuando vayas a procesar la salida; para mostrar al usuario puede bastar la tabla.
- No pidas filtros nuevos: usa `--format raw` (CSV) con `grep`/`sort`/`cut`/`awk`, o `--json` con `jq`. Hay ejemplos en la sección “Filosofía” del README.
- Usa `--limit N` en listados largos.
- No incluyas correos del alumnado salvo que el usuario lo pida: `participants` los omite por defecto; `--emails` los añade.
- No consultes datos personales que no necesites (GDPR).
- No intentes escrituras: no existen comandos para ello.
- `announcements` es específico del foro de noticias de Moovi. Si el comando pide `--forum-id`, usa el id de un candidato; no inventes ids.
- Si un comando falla, mira el código de salida antes de reintentar:
  - `2`: configuración, credenciales o token.
  - `3`: red o API.
  - `4`: permisos.

## Referencias

- `references/workflows.md`: recetas concretas (buscar curso, listar alumnado, tareas).
- `references/api.md`: endpoint, autenticación, funciones y errores de Moodle.
- `README.md`, en la raíz del repositorio: manual de usuario de la CLI.
