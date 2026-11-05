from __future__ import annotations

import pytest

from moovi.domain.errors import (
    AmbiguousForumError,
    ConfigError,
    NoAnnouncementsForumError,
)
from moovi.domain.models import Announcement, AnnouncementContent, Forum
from moovi.logic.services.announcements import AnnouncementService

NEWS = Forum(2217, 101, "Foro de novas", "news", True)
GENERAL = Forum(2218, 101, "Foro xeral", "general", False)
NEWS_2 = Forum(2219, 101, "Avisos", "news", True)
NEWS_OPTIONAL = Forum(2220, 101, "Noticias", "news", False)
ANNOUNCEMENT = Announcement(9001, "Aviso", "Profesor", None, 0, False, False)
CONTENT = AnnouncementContent(9001, 8001, "Aviso", "Profesor", message="<p>Hola</p>")


class FakeSession:
    def __init__(self, forums: list[Forum]) -> None:
        self.forums = forums
        self.calls: list[tuple[int, int]] = []

    def course_forums(self, course_id: int) -> list[Forum]:
        assert course_id == 101
        return self.forums

    def forum_discussions(
        self, forum_id: int, limit: int
    ) -> list[Announcement]:
        self.calls.append((forum_id, limit))
        return [ANNOUNCEMENT]

    def discussion_post(self, post_id: int) -> AnnouncementContent:
        assert post_id == 9001
        return CONTENT


def test_selects_the_single_news_forum() -> None:
    session = FakeSession([NEWS, GENERAL])
    service = AnnouncementService(session)

    result = service.list_announcements(101, limit=5)

    assert result == [ANNOUNCEMENT]
    assert session.calls == [(2217, 5)]


def test_explicit_forum_id_can_select_a_general_forum() -> None:
    session = FakeSession([NEWS, GENERAL])
    service = AnnouncementService(session)

    service.list_announcements(101, forum_id=2218)

    assert session.calls == [(2218, 10)]


def test_explicit_forum_id_must_belong_to_the_course() -> None:
    service = AnnouncementService(FakeSession([NEWS]))

    with pytest.raises(ConfigError, match="no pertenece"):
        service.list_announcements(101, forum_id=9999)


def test_raises_when_there_is_no_news_forum() -> None:
    service = AnnouncementService(FakeSession([GENERAL]))

    with pytest.raises(NoAnnouncementsForumError) as excinfo:
        service.list_announcements(101)

    assert excinfo.value.forums == (GENERAL,)


def test_prefers_the_forced_news_forum_when_there_are_several() -> None:
    session = FakeSession([NEWS_OPTIONAL, NEWS, GENERAL])
    service = AnnouncementService(session)

    service.list_announcements(101)

    assert session.calls == [(2217, 10)]


def test_raises_when_several_news_forums_are_forced() -> None:
    service = AnnouncementService(FakeSession([NEWS, NEWS_2, GENERAL]))

    with pytest.raises(AmbiguousForumError) as excinfo:
        service.list_announcements(101)

    assert excinfo.value.forums == (NEWS, NEWS_2)


def test_raises_when_several_news_forums_are_not_forced() -> None:
    other_optional = Forum(2221, 101, "Noticias 2", "news", False)
    service = AnnouncementService(
        FakeSession([NEWS_OPTIONAL, other_optional])
    )

    with pytest.raises(AmbiguousForumError):
        service.list_announcements(101)


def test_get_content_delegates() -> None:
    service = AnnouncementService(FakeSession([NEWS]))

    assert service.get_content(9001) == CONTENT
