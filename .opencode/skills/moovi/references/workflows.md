# Recetas

Todas las recetas usan la CLI `moovi` en modo de solo lectura.

## Verificar la sesión

```bash
moovi whoami --json
```

Si falla con código 2, revisa `.env`; no pidas la contraseña al usuario.

## Buscar el ID de un curso

```bash
moovi courses --json \
  | jq -r '.[] | select(.short_name == "M1") | "\(.id)\t\(.full_name)"'
```

También se puede buscar por nombre:

```bash
moovi courses --json \
  | jq -r '.[] | select(.full_name | test("Matemáticas"; "i")) | "\(.id)\t\(.full_name)"'
```

## Ver el contenido de un curso

```bash
moovi contents 12345 --json
```

Para un resumen legible:

```bash
moovi contents 12345
```

Cada sección trae `name`, `summary` y `modules`; cada módulo trae `mod_name`, `name`, `visible` y `url`.

## Listar alumnado sin correos

```bash
moovi students 12345 --json
```

Con correos, solo si el usuario lo pide:

```bash
moovi students 12345 --emails --json
```

Cada persona incluye `groups` (grupos del curso creados por el profesorado) y `roles`.

## Alumnado de un grupo

```bash
moovi students 12345 --format raw | grep ',PROII_1 (Laboratorio),'
```

En `--format raw`, los grupos van en la columna `groups` separados por `;`.

## Ver tareas y fechas de entrega

```bash
moovi assignments 12345 --json
```

Ordenar por fecha de entrega:

```bash
moovi assignments 12345 --json \
  | jq 'sort_by(.due_date // "9999")'
```

## Mostrar un resumen al usuario

1. Ejecuta el comando con `--json`.
2. Extrae solo los campos relevantes.
3. Responde en texto, sin pegar el JSON completo si no aporta.
