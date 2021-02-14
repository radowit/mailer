import json
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from operator import attrgetter
from random import shuffle
from smtplib import SMTP
from typing import List, Type

from requests import get

logger = getLogger(__name__)


@dataclass
class Article:
    article_id: str
    title: str
    url: str
    image_url: str
    news_site: str
    summary: str
    published_at: str
    updated_at: str
    featured: str
    launches: List[str]
    events: List[str]

    @classmethod
    def from_api(cls, kwargs):
        return cls(
            article_id=kwargs["id"],
            title=kwargs["title"],
            url=kwargs["url"],
            image_url=kwargs["imageUrl"],
            news_site=kwargs["newsSite"],
            summary=kwargs["summary"],
            published_at=kwargs["publishedAt"],
            updated_at=kwargs["updatedAt"],
            featured=kwargs["featured"],
            launches=kwargs["launches"],
            events=kwargs["events"],
        )


@dataclass
class Subscriber:
    week_day: int
    ordering: str
    email: str

    @property
    def is_sent_today(self):
        now = datetime.now()
        return self.week_day in [now.weekday(), 7]


class SubscriberRepository:
    def __init__(self, filename: str) -> None:
        self._filename = filename

    def list(self):
        with open(self._filename) as subscribers_file:
            return [Subscriber(**s) for s in json.load(subscribers_file)]


class ArticleFetcher:
    def __init__(self, get_function):
        self._get_function = get_function

    def fetch(self) -> List[Article]:
        return [
            Article.from_api(a)
            for a in self._get_function(
                "https://spaceflightnewsapi.net/api/v2/articles"
            ).json()
        ]


class MessageFormatter:
    def __init__(self, articles: List[Article]):
        self._articles = articles

    def format(self, subscriber: Subscriber) -> str:
        articles = self._articles.copy()
        if subscriber.ordering == "random":
            shuffle(articles)
        else:
            articles.sort(key=attrgetter(subscriber.ordering))

        space_news = "\n".join(
            [f"{a.title} ({a.url}) at {a.published_at}" for a in articles]
        )

        return f"""
Hello!
Here are your cool space news!

{space_news}

Sincerly,

your Mailman!
"""


class EmailSender:
    def __init__(self, smtp_obj: SMTP):
        self._smtp = smtp_obj

    def send(self, subscriber: Subscriber, email_message: str):
        self._smtp.sendmail(
            "your@mailman.com",
            subscriber.email,
            email_message.encode("utf8"),
        )
        logger.info("newsletter sent to %s.", subscriber.email)


class NewsletterMailer:
    def __init__(
        self,
        article_fetcher: ArticleFetcher,
        subscriber_repo: SubscriberRepository,
        message_formatter_class: Type[MessageFormatter],
        message_sender: EmailSender,
    ):
        self._article_fetcher = article_fetcher
        self._subscriber_repo = subscriber_repo
        self._message_formatter_class = message_formatter_class
        self._message_sender = message_sender

    def run(self) -> None:
        articles = self._article_fetcher.fetch()
        article_formatter = self._message_formatter_class(articles)

        for subscriber in self._subscriber_repo.list():
            if subscriber.is_sent_today:
                logger.info("Sending newsletter to %s", subscriber.email)
                formatted_articles = article_formatter.format(subscriber)

                self._message_sender.send(subscriber, formatted_articles)
            else:
                logger.info("Skipping sending newsletter to %s", subscriber.email)

        print("All messages sent!")


if __name__ == "__main__":
    with SMTP(host="localhost", port=1025) as smtp:
        NewsletterMailer(
            article_fetcher=ArticleFetcher(get),
            subscriber_repo=SubscriberRepository("data/subscribers.json"),
            message_formatter_class=MessageFormatter,
            message_sender=EmailSender(smtp),
        ).run()
