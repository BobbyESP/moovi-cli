from __future__ import annotations

from moovi.cli.tables import ParticipantsTable
from moovi.cli.tables.base import RichValue
from moovi.domain.models import Group, Participant, Role


def participant() -> Participant:
    return Participant(
        7,
        "Ana",
        "Alumna",
        groups=(Group(146, "met_part"), Group(147, "Grupo;Raro")),
        roles=(Role(5, "student", ""), Role(3, "editingteacher", "")),
        email="ana@uvigo.gal",
    )


def test_columns_and_hidden_full_name() -> None:
    table = ParticipantsTable([participant()], include_email=False)

    columns = {column.key: column for column in table.columns}
    assert columns["full_name"].table is False
    assert columns["full_name"].csv is False
    assert columns["email"].table is False
    assert columns["email"].csv is True


def test_groups_and_roles_have_raw_text_and_csv() -> None:
    table = ParticipantsTable([participant()], include_email=True)
    row = table.rows[0]

    groups = row[4]
    roles = row[5]
    assert isinstance(groups, RichValue)
    assert groups.raw == participant().groups
    assert groups.text == "met_part; Grupo;Raro"
    assert groups.csv_text == "met_part;Grupo#Raro"

    assert isinstance(roles, RichValue)
    assert roles.raw == participant().roles
    assert roles.text == "Alumno/a, Profesor/a"
    assert roles.csv_text == "student;editingteacher"


def test_email_column_is_visible_in_table_only_when_requested() -> None:
    without_email = ParticipantsTable([participant()], include_email=False)
    with_email = ParticipantsTable([participant()], include_email=True)

    email_without = next(
        column for column in without_email.columns if column.key == "email"
    )
    email_with = next(
        column for column in with_email.columns if column.key == "email"
    )

    assert email_without.table is False
    assert email_with.table is True
