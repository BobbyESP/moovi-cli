"""Caso de uso del foro de noticias de Moovi."""

from __future__ import annotations

from moovi.domain.errors import (
    AmbiguousForumError,
    ConfigError,
    NoAnnouncementsForumError,
)
from moovi.domain.models import Announcement, AnnouncementContent, Forum
from moovi.logic.session import MoodleSession

DEFAULT_ANNOUNCEMENTS_LIMIT = 10


class AnnouncementService:
    def __init__(self, session: MoodleSession) -> None:
        self._session = session

    def list_announcements(
        self,
        course_id: int,
        *,
        forum_id: int | None = None,
        limit: int = DEFAULT_ANNOUNCEMENTS_LIMIT,
    ) -> list[Announcement]:
        forums = self._session.course_forums(course_id)
        forum = self._select_forum(course_id, forums, forum_id)
        return self._session.forum_discussions(forum.id, limit)

    def get_content(self, post_id: int) -> AnnouncementContent:
        return self._session.discussion_post(post_id)

    def _select_forum(
        self,
        course_id: int,
        forums: list[Forum],
        forum_id: int | None,
    ) -> Forum:
        if forum_id is not None:
            for forum in forums:
                if forum.id == forum_id:
                    return forum
            raise ConfigError(
                f"El foro {forum_id} no pertenece al curso {course_id}."
            )

        news = [forum for forum in forums if forum.type == "news"]
        if not news:
            raise NoAnnouncementsForumError(course_id, forums)
        if len(news) == 1:
            return news[0]

        forced = [forum for forum in news if forum.force_subscribe]
        if len(forced) == 1:
            return forced[0]

        raise AmbiguousForumError(course_id, news)
