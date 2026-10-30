---
name: Moovi
description: Consulta Moovi (Moodle de la Universidade de Vigo) en solo lectura mediante la CLI `moovi`: identidad, cursos, contenidos, alumnado y tareas. Úsalo cuando el usuario pida información de sus asignaturas en Moovi.
---

# Moovi

CLI de solo lectura sobre la API oficial de Moovi. No usa scraping y no modifica nada en la plataforma.

## Requisitos

- La CLI `moovi` debe estar disponible (entorno conda `moovi` activo o paquete instalado).
- Debe existir un `.env` en la raíz del repositorio con `MOOVI_USER` y `MOOVI_PASSWORD` (o `MOOVI_TOKEN`).
- **Nunca imprimas el contenido de `.env` ni el token.** No los pidas por chat.

## Flujo

1. Comprueba la sesión:

   ```bash
   moovi whoami --json
   ```

2. Localiza el curso por su shortname o nombre:

   ```bash
   moovi courses --json
   ```

3. Consulta lo que pida el usuario:

   ```bash
   moovi contents <course_id> --json
   moovi students <course_id> --json
   moovi assignments <course_id> --json
   ```

4. Resume el resultado. No vuelques listados completos si basta con un resumen.

## Reglas

- Usa `--json` (o `--format json`) cuando vayas a procesar la salida; para mostrar al usuario puede bastar la tabla.
- No pidas filtros nuevos: usa `--format raw` (CSV) con `grep`/`sort`/`cut`/`awk`, o `--json` con `jq`. Hay ejemplos en la sección “Filosofía” del README.
- Usa `--limit N` en listados largos.
- No incluyas correos del alumnado salvo que el usuario lo pida: `students` los omite por defecto; `--emails` los añade.
- No consultes datos personales que no necesites (GDPR).
- No intentes escrituras: no existen comandos para ello.
- Si un comando falla, mira el código de salida antes de reintentar:
  - `2`: configuración, credenciales o token.
  - `3`: red o API.
  - `4`: permisos.

## Referencias

- `references/workflows.md`: recetas concretas (buscar curso, listar alumnado, tareas).
- `references/api.md`: endpoint, autenticación, funciones y errores de Moodle.
- `README.md`, en la raíz del repositorio: manual de usuario de la CLI.
