# AGENTS.md

## Antes de tocar código

- Lee `docs/architecture.md` y respeta la regla de dependencias entre capas.
- Lee `README.md` para conocer la interfaz que ve el usuario.

## Reglas

- Solo lectura por defecto. No añadas comandos de escritura sin decisión explícita.
- No añadas dependencias en runtime sin justificarlo.
- No dupliques documentación: `README.md` es el manual de usuario; `docs/architecture.md` es la referencia técnica.

## Al terminar

- Ejecuta `pytest` (los tests `live` se saltan por defecto).
- Si cambia el comportamiento, comandos o salida: actualiza `README.md`.
- Si cambian capas, puertos, flujo, errores o añades un comando: actualiza `docs/architecture.md`.
- Si añades una dependencia: actualiza `environment.yml` y `pyproject.toml`.
