# pylint: disable=redefined-outer-name,line-too-long,import-outside-toplevel
import json
import logging
from unittest.mock import Mock, patch
from tempfile import mkstemp

import pytest
from factory import Factory, Faker

from mailer.main import (
    Article,
    ArticleFetcher,
    EmailSender,
    MessageFormatter,
    NewsletterMailer,
    Subscriber,
    SubscriberRepository,
)


class ArticleFactory(Factory):
    class Meta:
        model = Article

    article_id = Faker("sha1")
    image_url = Faker("image_url")
    news_site = Faker("word")
    summary = Faker("sentence")
    updated_at = Faker("date")
    featured = Faker("boolean")
    launches = []
    events = []

    @classmethod
    def build_as_api_dict(cls, article=None, **kwargs):
        article = article or cls.build(**kwargs)
        return dict(
            id=article.article_id,
            title=article.title,
            url=article.url,
            imageUrl=article.image_url,
            newsSite=article.news_site,
            summary=article.summary,
            publishedAt=article.published_at,
            updatedAt=article.updated_at,
            featured=article.featured,
            launches=article.launches,
            events=article.events,
        )


@pytest.fixture
def shuffle_mock():
    def _shuffle(alist):
        alist.sort(key=lambda a: a.url)

    return _shuffle


def test_article_from_api():
    article_obj = ArticleFactory.build(
        published_at="2021-02-12T20:56:59.000Z",
        title="Report: NASA’s only realistic path for humans on Mars is nuclear",
        url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
    )
    article = Article.from_api(ArticleFactory.build_as_api_dict(article_obj))

    assert article == article_obj


@pytest.mark.freeze_time("2021-02-13")
@pytest.mark.parametrize(
    "week_day_diff,expcected",
    (
        (0, True),
        (-5, False),
        (10, False),
        (2, True),
    ),
)
def test_subscriber_is_sent_today_true(week_day_diff, expcected):
    subscriber = Subscriber(
        week_day=5 + week_day_diff,
        ordering="random",
        email="random@amber.com",
    )

    assert subscriber.is_sent_today is expcected


def test_subscriber_repository():
    subscriber_dicts = [
        {
            "week_day": 5,
            "ordering": "published_at",
            "email": "mark@house.com",
        },
        {
            "week_day": 5,
            "ordering": "random",
            "email": "mark@black.com",
        },
        {
            "week_day": 2,
            "ordering": "random",
            "email": "mark@roberts.com",
        },
    ]
    _, filename = mkstemp()
    with open(filename, "w+") as subscribers_file:
        subscribers_file.write(json.dumps(subscriber_dicts))

    repo = SubscriberRepository(filename)

    subscribers = repo.list()

    assert subscribers == [Subscriber(**s) for s in subscriber_dicts]


def test_article_fetcher():
    article_objs = [
        ArticleFactory.build(
            title="Report: NASA’s only realistic path for humans on Mars is nuclear",
            url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
            published_at="2021-02-12T20:56:59.000Z",
        ),
        ArticleFactory.build(
            title="Despite its small size, Space Force plans",
            url="https://spacenews.com/despite-its-small-size-space-force-plans/",
            published_at="2021-02-12T22:59:04.000Z",
        ),
        ArticleFactory.build(
            title="Sensors Prepare to Collect Data as Perseverance Enters Mars",
            url="https://mars.nasa.gov/news/8859/",
            published_at="2021-02-12T20:19:00.000Z",
        ),
    ]
    get_mock = Mock()
    get_mock().json.return_value = [
        ArticleFactory.build_as_api_dict(ao) for ao in article_objs
    ]

    fetcher = ArticleFetcher(get_mock)

    articles = fetcher.fetch()

    assert articles == article_objs


@pytest.mark.parametrize(
    "ordering,article_order",
    (
        ("title", [1, 0, 2]),
        ("published_at", [2, 0, 1]),
        ("random", [0, 2, 1]),
    ),
)
def test_message_formatter_format_title(ordering, article_order, shuffle_mock):
    articles = [
        ArticleFactory.build(
            title="Report: NASA’s only realistic path for humans on Mars is nuclear",
            url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
            published_at="2021-02-12T20:56:59.000Z",
        ),
        ArticleFactory.build(
            title="Despite its small size, Space Force plans",
            url="https://spacenews.com/despite-its-small-size-space-force-plans/",
            published_at="2021-02-12T22:59:04.000Z",
        ),
        ArticleFactory.build(
            title="Sensors Prepare to Collect Data as Perseverance Enters Mars",
            url="https://mars.nasa.gov/news/8859/",
            published_at="2021-02-12T20:19:00.000Z",
        ),
    ]
    formatter = MessageFormatter(articles)
    subscriber = Subscriber(week_day=5, ordering=ordering, email="mark@house.com")

    with patch("mailer.main.shuffle", shuffle_mock):
        formatted_message = formatter.format(subscriber)

    assert (
        formatted_message
        == f"""
Hello!
Here are your cool space news!

{articles[article_order[0]].title} ({articles[article_order[0]].url}) at {articles[article_order[0]].published_at}
{articles[article_order[1]].title} ({articles[article_order[1]].url}) at {articles[article_order[1]].published_at}
{articles[article_order[2]].title} ({articles[article_order[2]].url}) at {articles[article_order[2]].published_at}

Sincerly,

your Mailman!
"""
    )


def test_email_sender_send():
    smtp = Mock()
    sender = EmailSender(smtp)
    subscriber = Subscriber(week_day=5, ordering="random", email="mark@house.com")

    sender.send(subscriber, "abc")

    smtp.sendmail.assert_called_with(
        "your@mailman.com",
        "mark@house.com",
        b"abc",
    )


def test_newsletter_mailer_send(capsys, caplog):
    caplog.set_level(logging.DEBUG)
    article_fetcher = Mock()
    subscriber_repo = Mock()
    subscriber1 = Mock(email="test1@email.com", is_sent_today=True)
    subscriber2 = Mock(email="test2@email.com", is_sent_today=False)
    subscriber_repo.list.return_value = [subscriber1, subscriber2]
    message_formatter_class = Mock()
    message_sender = Mock()

    NewsletterMailer(
        article_fetcher=article_fetcher,
        subscriber_repo=subscriber_repo,
        message_formatter_class=message_formatter_class,
        message_sender=message_sender,
    ).run()

    message_formatter_class().format.assert_called_once()
    message_formatter_class().format.assert_called_with(subscriber1)
    message_sender.send.assert_called_once()
    message_sender.send.assert_called_with(
        subscriber1, message_formatter_class().format()
    )
    assert capsys.readouterr().out == "All messages sent!\n"
    assert len(caplog.records) == 2
    assert caplog.records[0].msg == "Sending newsletter to %s"
    assert caplog.records[0].args == ("test1@email.com",)
    assert caplog.records[1].msg == "Skipping sending newsletter to %s"
    assert caplog.records[1].args == ("test2@email.com",)
