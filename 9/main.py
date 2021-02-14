import json
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from operator import attrgetter
from random import Random
from smtplib import SMTP
from typing import List, Optional

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
    def __init__(self, random: Random) -> None:
        self._random = random
        self._articles: Optional[List[Article]] = None

    def set_articles(self, articles: List[Article]) -> None:
        self._articles = articles

    def format(self, subscriber: Subscriber) -> str:
        if self._articles is None:
            raise NotImplementedError("Formatter needs articles to work!")

        articles = self._articles.copy()
        if subscriber.ordering == "random":
            self._random.shuffle(articles)
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
        message_formatter: MessageFormatter,
        message_sender: EmailSender,
    ):
        self._article_fetcher = article_fetcher
        self._subscriber_repo = subscriber_repo
        self._message_formatter = message_formatter
        self._message_sender = message_sender

    def run(self) -> None:
        articles = self._article_fetcher.fetch()
        self._message_formatter.set_articles(articles)

        for subscriber in self._subscriber_repo.list():
            if subscriber.is_sent_today:
                logger.info("Sending newsletter to %s", subscriber.email)
                formatted_articles = self._message_formatter.format(subscriber)

                self._message_sender.send(subscriber, formatted_articles)
            else:
                logger.info("Skipping sending newsletter to %s", subscriber.email)

        print("All messages sent!")


if __name__ == "__main__":
    with SMTP(host="localhost", port=1025) as smtp:
        NewsletterMailer(
            article_fetcher=ArticleFetcher(get),
            subscriber_repo=SubscriberRepository("data/subscribers.json"),
            message_formatter=MessageFormatter(Random(datetime.now())),
            message_sender=EmailSender(smtp),
        ).run()
