"""Adaptación de roles a texto de presentación."""

from __future__ import annotations

from moovi.domain.models import Role

_ROLE_LABELS = {
    "student": "Alumno/a",
    "editingteacher": "Profesor/a",
    "teacher": "Profesor/a",
    "guestteacher": "Profesor/a invitado/a",
    "manager": "Gestor/a",
    "coursecreator": "Creador/a de cursos",
    "guest": "Invitado/a",
}


def role_label(role: Role) -> str:
    if role.name:
        return role.name
    if role.short_name:
        return _ROLE_LABELS.get(role.short_name, role.short_name)
    return f"Rol {role.id}" if role.id else "—"


def role_key(role: Role) -> str:
    if role.short_name:
        return role.short_name
    if role.name:
        return role.name
    return f"role_{role.id}" if role.id else ""
