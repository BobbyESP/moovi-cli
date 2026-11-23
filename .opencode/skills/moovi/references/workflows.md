# Recetas

Todas las recetas usan la CLI `moovi` en modo de solo lectura. Ejecútalas desde la raíz del repositorio.

## Verificar la sesión

```bash
uv run moovi whoami --json
```

Si falla con código 2, pide al usuario que ejecute `uv run moovi login` en su terminal, desde la raíz del repositorio. No pidas la contraseña por chat.

## Buscar el ID de un curso

```bash
uv run moovi courses --json \
  | jq -r '.[] | select(.short_name == "M1") | "\(.id)\t\(.full_name)"'
```

También se puede buscar por nombre:

```bash
uv run moovi courses --json \
  | jq -r '.[] | select(.full_name | test("Matemáticas"; "i")) | "\(.id)\t\(.full_name)"'
```

## Ver el contenido de un curso

```bash
uv run moovi contents 12345 --json
```

Para un resumen legible:

```bash
uv run moovi contents 12345
```

Cada sección trae `name`, `summary` y `modules`; cada módulo trae `mod_name`, `name`, `visible` y `url`.

## Descargar archivos y carpetas

```bash
# Ver qué hay y cuánto ocupa (bytes)
uv run moovi files 12345 --json | jq '{archivos: length, bytes: (map(.size) | add)}'

# Descargar un módulo concreto y revisar lo que no se completó
uv run moovi download 12345 678 -o apuntes --json \
  | jq '.[] | select(.status == "conflict" or .status == "failed")'
```

Código de salida `1`: descarga parcial. Mira `status` y `error` de cada archivo.

## Listar alumnado sin correos

```bash
uv run moovi participants 12345 --json
```

Con correos, solo si el usuario lo pide:

```bash
uv run moovi participants 12345 --emails --json
```

Cada persona incluye `groups` (grupos del curso creados por el profesorado) y `roles`.

## Leer el foro de noticias de Moovi

Moovi crea automáticamente un foro de noticias por materia. No lo busques por nombre: el comando lo localiza por tipo.

```bash
uv run moovi announcements 12345 --json
```

Si hay varios foros de noticias, el comando muestra los ids y pide elegir:

```bash
uv run moovi announcements 12345 --forum-id 2217 --json
```

Para leer un anuncio concreto, usa el id de la columna `ID`:

```bash
uv run moovi announcement-content 63251 --json
```

En JSON, `message` es el HTML original y `message_text` el texto limpio. En tabla/CSV se usa el texto limpio.

## Alumnado de un grupo

```bash
uv run moovi participants 12345 --format raw | grep ',PROII_1 (Laboratorio),'
```

En `--format raw`, los grupos van en la columna `groups` separados por `;`.

## Ver tareas y fechas de entrega

```bash
uv run moovi assignments 12345 --json
```

Ordenar por fecha de entrega:

```bash
uv run moovi assignments 12345 --json \
  | jq 'sort_by(.due_date // "9999")'
```

## Mostrar un resumen al usuario

1. Ejecuta el comando con `--json`.
2. Extrae solo los campos relevantes.
3. Responde en texto, sin pegar el JSON completo si no aporta.
