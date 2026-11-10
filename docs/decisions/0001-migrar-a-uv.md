# ADR 0001 — Migrar la gestión del entorno de conda a uv

- **Estado:** Aceptada e implementada.
- **Ámbito:** entorno de desarrollo y de ejecución. No cambia el código de `src/`, la interfaz de la CLI ni la arquitectura por capas.

## Contexto

Hasta ahora el proyecto se instalaba con conda:

```bash
conda env create -f environment.yml
conda activate moovi
pip install -e .
```

Esto tenía varios problemas, ninguno grave por separado, pero que suman fricción en un proyecto cuyo uso habitual incluye **agentes y scripts que lanzan cada comando en una shell nueva**:

1. **No era reproducible.** `environment.yml` fijaba `python=3.12` y `pytest` sin versión, y no existía lockfile. Dos instalaciones en fechas distintas podían resolver versiones distintas.
2. **Dos gestores mezclados.** El entorno lo creaba conda, pero el paquete se instalaba con `pip install -e .`. Las dependencias vivían en dos sitios (`environment.yml` y `pyproject.toml`) y había que mantenerlas sincronizadas a mano (así lo pedía `AGENTS.md`).
3. **Dependía de la activación.** Una shell nueva no tiene el entorno activo, lo que obligaba a documentar el workaround `conda run -n moovi --no-capture-output moovi ...` en el README, en `AGENTS.md` y en el skill.
4. **Requisito de instalación pesado.** Había que instalar Miniconda o Anaconda solo para obtener un intérprete de Python y `pytest`.
5. **No aprovechábamos lo que aporta conda.** Su valor diferencial son los paquetes binarios no Python (bibliotecas C, CUDA, etc.). Este proyecto tiene **cero dependencias en runtime** (solo stdlib) y una sola de desarrollo.

## Decisión

Adoptar [uv](https://docs.astral.sh/uv/) como único gestor de entorno, dependencias e intérprete, con estos elementos:

| Elemento | Función |
|---|---|
| `pyproject.toml` | Única fuente de verdad de las dependencias. Las de desarrollo viven en `[dependency-groups] dev` (PEP 735). |
| `uv.lock` | Lockfile multiplataforma versionado. Fija versiones exactas (y hashes) de todo el árbol. |
| `.python-version` | Fija el intérprete a 3.12; uv lo descarga si no está presente. |
| `.venv/` | Entorno local del proyecto, ya ignorado por git. |
| `uv run <cmd>` | Punto de entrada único: sincroniza el entorno con el lock si hace falta y ejecuta el comando. |

`environment.yml` se elimina y la entrada `.conda/` desaparece de `.gitignore`.

## Por qué uv

- **Reproducibilidad real.** `uv.lock` resuelve el problema 1 y `uv sync --locked` permite que una futura CI falle si el lock está desfasado.
- **Una sola herramienta y una sola fuente de verdad.** `pyproject.toml` declara el proyecto, sus dependencias y sus grupos; desaparece la sincronización manual entre `environment.yml` y `pyproject.toml` (problema 2).
- **Sin activación.** `uv run moovi ...` funciona igual en una shell persistente que en una nueva, de modo que el workaround de `conda run` deja de existir (problema 3). Es el caso de uso de los agentes que consumen el skill `moovi`.
- **Arranque sin prerrequisitos de Python.** uv es un binario único que gestiona también el intérprete (`.python-version`); no hace falta instalar Python ni una distribución completa antes (problema 4).
- **Velocidad.** uv está escrito en Rust y usa caché global con enlaces; resolver e instalar el árbol completo de este proyecto (7 paquetes) tardó menos de un segundo en la máquina donde se hizo la migración. No se ha medido una línea base de conda, así que no se afirma una comparativa numérica; el beneficio práctico es que `uv run` puede resincronizar de forma implícita sin penalizar cada ejecución.
- **Encaja con el diseño del proyecto.** El principio «sin dependencias en runtime» (ver `docs/architecture.md`) hace innecesaria la gestión de binarios de conda (problema 5).

## Alternativas consideradas

| Alternativa | Motivo de descarte |
|---|---|
| **Mantener conda** | Conserva los cinco problemas anteriores; su ventaja principal no se usa. |
| **`python -m venv` + `pip`** | Es el mínimo universal, pero no tiene lockfile ni gestiona el intérprete; reproduciría el problema 1. |
| **Poetry / PDM / Hatch** | Resuelven el lockfile, pero añaden su propio flujo y herramientas que este proyecto no necesita y, a diferencia de uv, no gestionan el intérprete de Python. uv cubre lo mismo con menos piezas. |
| **pip-tools** | Genera un `requirements.txt` bloqueado, pero sigue necesitando venv e intérprete aparte. |

## Consecuencias

**Positivas**

- Instalación en un comando (`uv sync`) y ejecución en un comando (`uv run moovi ...`).
- Entornos idénticos entre desarrolladores, agentes y futura CI.
- Menos documentación que mantener: desaparecen el workaround de activación y el fichero `environment.yml`.

**Costes y riesgos aceptados**

- **Nueva herramienta que instalar.** Quien contribuya necesita uv. Mitigación: es un binario único con instaladores para Windows, macOS y Linux.
- **Madurez.** uv es más joven que conda/pip. Mitigación: el proyecto solo usa funciones estables (`sync`, `lock`, `run`, grupos PEP 735), y el resultado sigue siendo un `.venv` estándar, de modo que `pip` sigue funcionando como vía de escape.
- **Sin binarios no Python.** Si en el futuro se necesitara una dependencia con bibliotecas nativas que solo conda proporcione bien, habría que reevaluar esta decisión.
- **`uv.lock` entra en el control de versiones** y aparecerá en los diffs cuando cambien las dependencias.
- **Cambio de comandos en la documentación.** Se actualizaron `README.md`, `AGENTS.md`, el skill `moovi` y `docs/architecture.md`. Quien tenga el entorno conda antiguo puede eliminarlo con `conda env remove -n moovi`.

## Plan de migración (ejecutado)

1. **Declarar las dependencias de desarrollo en `pyproject.toml`.** Se añadió `[dependency-groups] dev = ["pytest>=8"]`. *Por qué:* la información que estaba en `environment.yml` pasa al único fichero que describe el proyecto. Se mantiene `setuptools` como backend de build para limitar el alcance del cambio.
2. **Fijar el intérprete con `.python-version`.** *Por qué:* uv elige y descarga Python 3.12 sin pasos manuales, coherente con `requires-python = ">=3.12"`.
3. **Generar `uv.lock` con `uv lock`.** *Por qué:* es lo que aporta reproducibilidad; se versiona.
4. **Validar antes de documentar.** `uv sync`, `uv run moovi --version` y `uv run pytest`. *Por qué:* confirmar que el port funciona antes de reescribir las instrucciones. Los tests lanzan la CLI con `sys.executable -m moovi`, así que no dependen del gestor de entornos y no hizo falta tocar código ni tests.
5. **Eliminar `environment.yml` y la entrada `.conda/` de `.gitignore`.** *Por qué:* dejar dos fuentes de verdad invitaría a que divergieran.
6. **Actualizar la documentación**, sin duplicarla (el README es el manual de usuario; `docs/architecture.md`, la referencia técnica; este ADR, el porqué):
   - `README.md`: requisitos, instalación, uso rápido, problemas frecuentes y desarrollo.
   - `AGENTS.md` y `.opencode/skills/moovi/SKILL.md`: las instrucciones para agentes pasan de `conda run ...` a `uv run moovi ...`; la regla de «si añades una dependencia» pasa a `uv add`.
   - `docs/architecture.md`: la fila de decisiones de diseño.

## Verificación

- `uv sync` crea `.venv` con Python 3.12 e instala el proyecto en modo editable.
- `uv run moovi --version` devuelve `moovi 0.1.0`.
- `uv run pytest`: 155 tests pasan y 2 se saltan (`live`). Fallan 2 tests que **ya fallaban antes de la migración** y no están relacionados con ella: comprueban que el fichero del token tiene permisos `0600`, y en Windows (NTFS) el sistema de ficheros no expone ese modo (devuelve `0o666`). Conviene tratarlos aparte, por ejemplo saltándolos en `win32`.

## Reversión

Basta con restaurar `environment.yml` y las líneas de documentación desde el historial de git. El código fuente no ha cambiado, así que no hay migración de datos: el token vive en `~/.cache/moovi/token.json`, fuera del entorno.

## Seguimientos opcionales (fuera de este cambio)

- Añadir CI con `uv sync --locked` y `uv run pytest`.
- Valorar `uv_build` como backend de build si se prefiere un único proveedor de herramientas.
- Distribuir la CLI con `uv tool install` / `uvx` si deja de ser solo de uso desde el repositorio.
