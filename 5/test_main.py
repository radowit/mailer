# pylint: disable=redefined-outer-name,line-too-long,import-outside-toplevel
import json
from shutil import move
from unittest.mock import Mock, patch

import pytest
from factory import Factory

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

    article_id = "6026ec1b3a4653001c012105"
    image_url = "https://cdn.arstechnica.net/wp-content/upload9255078_orig.jpg"
    news_site = "Arstechnica"
    summary = '"It\'s the kind of technology challenge that NASA was built."'
    updated_at = "2021-02-12T20:59:08.034Z"
    featured = False
    launches = []
    events = []

    @classmethod
    def build_as_api_dict(cls, **kwargs):
        article = cls.build(**kwargs)
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
@pytest.mark.freeze_time("2021-02-13")
def data_file_mock():
    move("data/subscribers.json", "data/prod_subscribers.json")
    subscribers = [
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
    with open("data/subscribers.json", "w+") as subscribers_file:
        subscribers_file.write(json.dumps(subscribers))
    yield subscribers
    move("data/prod_subscribers.json", "data/subscribers.json")


@pytest.fixture
def shuffle_mock():
    def _shuffle(alist):
        alist.sort(key=lambda a: a.url)

    return _shuffle


def test_article_from_api():
    article = Article.from_api(
        ArticleFactory.build_as_api_dict(
            published_at="2021-02-12T20:56:59.000Z",
            title="Report: NASA’s only realistic path for humans on Mars is nuclear",
            url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
        )
    )

    assert article == ArticleFactory.build(
        published_at="2021-02-12T20:56:59.000Z",
        title="Report: NASA’s only realistic path for humans on Mars is nuclear",
        url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
    )


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


def test_subscriber_repository(data_file_mock):
    del data_file_mock

    repo = SubscriberRepository()

    subscribers = repo.list()

    assert subscribers == [
        Subscriber(week_day=5, ordering="published_at", email="mark@house.com"),
        Subscriber(week_day=5, ordering="random", email="mark@black.com"),
        Subscriber(week_day=2, ordering="random", email="mark@roberts.com"),
    ]


def test_article_fetcher():
    get_mock = Mock()
    get_mock().json.return_value = [
        ArticleFactory.build_as_api_dict(
            title="Report: NASA’s only realistic path for humans on Mars is nuclear",
            url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
            published_at="2021-02-12T20:56:59.000Z",
        ),
        ArticleFactory.build_as_api_dict(
            title="Despite its small size, Space Force plans",
            url="https://spacenews.com/despite-its-small-size-space-force-plans/",
            published_at="2021-02-12T22:59:04.000Z",
        ),
        ArticleFactory.build_as_api_dict(
            title="Sensors Prepare to Collect Data as Perseverance Enters Mars",
            url="https://mars.nasa.gov/news/8859/",
            published_at="2021-02-12T20:19:00.000Z",
        ),
    ]

    fetcher = ArticleFetcher(get_mock)

    articles = fetcher.fetch()

    assert articles == [
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


def test_newsletter_mailer_send():
    article_fetcher = Mock()
    subscriber_repo = Mock()
    subscriber = Mock(is_sent_today=True)
    subscriber_repo.list.return_value = [
        subscriber,
        Mock(is_sent_today=False),
    ]
    message_formatter_class = Mock()
    message_sender = Mock()

    NewsletterMailer(
        article_fetcher=article_fetcher,
        subscriber_repo=subscriber_repo,
        message_formatter_class=message_formatter_class,
        message_sender=message_sender,
    ).run()

    message_formatter_class().format.assert_called_once()
    message_formatter_class().format.assert_called_with(subscriber)
    message_sender.send.assert_called_once()
    message_sender.send.assert_called_with(
        subscriber, message_formatter_class().format()
    )
