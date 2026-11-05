from moovi.cli.formats.base import Formatter
from moovi.cli.formats.csv import CsvFormatter
from moovi.cli.formats.json import JsonFormatter
from moovi.cli.formats.table import TableFormatter
from moovi.cli.tables import (
    AnnouncementContentTable,
    AnnouncementsTable,
    AssignmentsTable,
    ContentsTable,
    CoursesTable,
    ParticipantsTable,
    SiteInfoTable,
)
from moovi.cli.tables.base import Table


def test_tables_declare_the_table_protocol() -> None:
    for table_class in (
        SiteInfoTable,
        CoursesTable,
        ContentsTable,
        ParticipantsTable,
        AssignmentsTable,
        AnnouncementsTable,
        AnnouncementContentTable,
    ):
        assert Table in table_class.__mro__, table_class.__name__


def test_formatters_declare_the_formatter_protocol() -> None:
    for formatter_class in (TableFormatter, JsonFormatter, CsvFormatter):
        assert Formatter in formatter_class.__mro__, formatter_class.__name__
