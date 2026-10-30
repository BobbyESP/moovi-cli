from moovi.cli.render import role_label
from moovi.domain.models import Role


def test_translates_known_short_names() -> None:
    assert role_label(Role(5, "student", "")) == "Alumno/a"
    assert role_label(Role(3, "editingteacher", "")) == "Profesor/a"
    assert role_label(Role(4, "teacher", "")) == "Profesor/a"
    assert role_label(Role(1, "manager", "")) == "Gestor/a"


def test_prefers_role_name() -> None:
    assert (
        role_label(Role(10, "guestteacher", "Profesor Invitado"))
        == "Profesor Invitado"
    )


def test_falls_back_to_short_name_or_id() -> None:
    assert role_label(Role(99, "custom_role", "")) == "custom_role"
    assert role_label(Role(99, "", "")) == "Rol 99"
