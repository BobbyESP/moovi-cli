# AGENTS.md

## Si solo usas la CLI

- Lee `README.md` y carga el skill `moovi` antes de improvisar.
- Comprueba que `moovi` está disponible. Si tu shell no conserva la activación, usa `conda run -n moovi --no-capture-output moovi ...`.
- Ejecuta desde la raíz del repositorio para que se lea `.env`, o exporta las variables `MOOVI_*`.
- No hagas scraping ni llames a la API a mano: usa `moovi` con `--json` o `--format raw`.
- Si no hay sesión, no pidas la contraseña por chat: indica al usuario que ejecute `moovi login` en su terminal. No uses `--no-input` salvo que las credenciales ya estén en el entorno.
- Si una tarea te costó más de lo razonable, no te quedes con el workaround:
  - si faltaba una receta o un ejemplo de uso, propón mejorar el skill;
  - si faltaba un dato, un formato o un comando, propón un cambio en la CLI.
- Explica la fricción concreta: qué intentaste, qué falló y qué esperabas.
- Si tu tarea era solo usar la CLI, no modifiques código: deja la propuesta al usuario.

## Si vas a tocar código

- Lee `docs/architecture.md` y respeta la regla de dependencias entre capas.
- Lee `README.md` para conocer la interfaz que ve el usuario.
- Solo lectura por defecto. No añadas comandos de escritura sin decisión explícita.
- No añadas dependencias en runtime sin justificarlo.
- No dupliques documentación: `README.md` es el manual de usuario; `docs/architecture.md` es la referencia técnica.

## Al terminar de tocar código

- Ejecuta `pytest` (los tests `live` se saltan por defecto).
- Si cambia el comportamiento, comandos o salida: actualiza `README.md`.
- Si cambian capas, puertos, flujo, errores o añades un comando: actualiza `docs/architecture.md`.
- Si añades una dependencia: actualiza `environment.yml` y `pyproject.toml`.
