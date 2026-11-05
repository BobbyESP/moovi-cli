# API de Moovi

Moovi es Moodle 4.5 y expone los servicios web oficiales. No se usa scraping.

## Endpoints

- Login: `POST https://moovi.uvigo.gal/login/token.php`
  - `username`, `password`, `service=moodle_mobile_app`
  - Respuesta correcta: `{"token": "..."}`
  - Respuesta incorrecta: `{"error": "...", "errorcode": "invalidlogin"}`
- Servicios: `POST https://moovi.uvigo.gal/webservice/rest/server.php`
  - `wstoken`, `wsfunction`, `moodlewsrestformat=json`
  - Parámetros anidados en notación `courseids[0]`, `options[0][name]`.

## Reglas de Moodle que conviene recordar

- Los errores llegan con **HTTP 200** y un cuerpo con `exception` / `errorcode` / `message`.
- `invalidtoken` significa token caducado o revocado: hay que renovarlo y reintentar una vez.
- `accessexception` y `nopermissions` significan falta de capacidad en ese curso.
- Las fechas son timestamps Unix en segundos; `0` significa “sin fecha”.
- Algunos campos (`summary`) contienen HTML.
- En `roles`, el campo `name` puede venir vacío; usa `shortname` como identificador fiable.
- `core_enrol_get_enrolled_users` incluye `groups` con los grupos del curso creados por el profesorado; una persona puede estar en varios.

## Funciones usadas

| Función | Parámetros | Devuelve |
|---|---|---|
| `core_webservice_get_site_info` | — | usuario, sitio, versión, funciones |
| `core_enrol_get_users_courses` | `userid` | cursos del usuario |
| `core_course_get_contents` | `courseid` | secciones y módulos |
| `core_enrol_get_enrolled_users` | `courseid` | personas y roles |
| `mod_assign_get_assignments` | `courseids[0]` | tareas por curso |
| `mod_forum_get_forums_by_courses` | `courseids[0]` | foros del curso, incluido `type="news"` |
| `mod_forum_get_forum_discussions` | `forumid`, `sortorder`, `page`, `perpage` | anuncios del foro de noticias |
| `mod_forum_get_discussion_post` | `postid` | contenido de un anuncio |

Todas están en la allowlist de `network/rest.py`. La CLI no expone un `call` genérico.

## Añadir una función

1. Añádela a `READ_ONLY_FUNCTIONS` en `src/moovi/network/rest.py`.
2. Añade el método al puerto `MoodleGateway` y su implementación.
3. Mapea la respuesta en `network/mappers.py`.
4. Crea el caso de uso y el comando.
5. Añade tests unitarios, de integración y e2e.
6. Actualiza `README.md` y `docs/architecture.md`.

No añadas funciones de escritura sin una decisión explícita del usuario.
