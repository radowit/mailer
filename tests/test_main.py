# pylint: disable=redefined-outer-name,line-too-long,import-outside-toplevel
import json
from dataclasses import asdict
from datetime import datetime
from shutil import move
from unittest.mock import Mock, patch

import pytest

from mailer.main import (
    Article,
    ArticleFetcher,
    EmailSender,
    MessageFormatter,
    NewsletterMailer,
    Subscriber,
    SubscriberRepository,
)


@pytest.fixture
def data_file_mock():
    now = datetime.now()
    move("data/subscribers.json", "data/prod_subscribers.json")
    subscribers = [
        {
            "week_day": now.weekday(),
            "ordering": "published_at",
            "email": "mark@house.com",
        },
        {
            "week_day": now.weekday(),
            "ordering": "random",
            "email": "mark@black.com",
        },
        {
            "week_day": 7 - now.weekday(),
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
        alist.sort(key=lambda a: a.summary)

    return _shuffle


def test_article_from_api():
    article = Article.from_api(
        {
            "events": [],
            "featured": False,
            "id": "6026ec1b3a4653001c012105",
            "imageUrl": "https://cdn.arstechnica.net/wp-content/upload9255078_orig.jpg",
            "launches": [],
            "newsSite": "Arstechnica",
            "publishedAt": "2021-02-12T20:56:59.000Z",
            "summary": '"It\'s the kind of technology challenge that NASA was built."',
            "title": "Report: NASA’s only realistic path for humans on Mars is nuclear",
            "updatedAt": "2021-02-12T20:59:08.034Z",
            "url": "https://arstechnica.com/science/2021/02/report-nasas-only-/",
        }
    )

    assert asdict(article) == {
        "article_id": "6026ec1b3a4653001c012105",
        "events": [],
        "featured": False,
        "image_url": "https://cdn.arstechnica.net/wp-content/upload9255078_orig.jpg",
        "launches": [],
        "news_site": "Arstechnica",
        "published_at": "2021-02-12T20:56:59.000Z",
        "summary": '"It\'s the kind of technology challenge that NASA was built."',
        "title": "Report: NASA’s only realistic path for humans on Mars is nuclear",
        "updated_at": "2021-02-12T20:59:08.034Z",
        "url": "https://arstechnica.com/science/2021/02/report-nasas-only-/",
    }


def test_subscriber_is_sent_today_true():
    now = datetime.now()
    subscriber = Subscriber(
        week_day=now.weekday(),
        ordering="random",
        email="random@amber.com",
    )

    assert subscriber.is_sent_today


def test_subscriber_is_sent_today_false():
    now = datetime.now()
    subscriber = Subscriber(
        week_day=7 - now.weekday(),
        ordering="random",
        email="random@amber.com",
    )

    assert not subscriber.is_sent_today


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
        {
            "id": "6026ec1b3a4653001c012105",
            "title": "Report: NASA’s only realistic path for humans on Mars is nuclear",
            "url": "https://arstechnica.com/science/2021/02/report-nasas-only-/",
            "imageUrl": "https://cdn.arstechnica.net/wp-content/upload9255078_orig.jpg",
            "newsSite": "Arstechnica",
            "summary": '"It\'s the kind of technology challenge that NASA was built."',
            "publishedAt": "2021-02-12T20:56:59.000Z",
            "updatedAt": "2021-02-12T20:59:08.034Z",
            "featured": False,
            "launches": [],
            "events": [],
        },
        {
            "id": "602708383a4653001c012106",
            "title": "Despite its small size, Space Force plans",
            "url": "https://spacenews.com/despite-its-small-size-space-force-plans/",
            "imageUrl": "https://spacenews.com/wp-content/uploads/2021/02/6428324.jpg",
            "newsSite": "SpaceNews",
            "summary": "The Space Force is by far the smallest branch of the U.S. .",
            "publishedAt": "2021-02-12T22:59:04.000Z",
            "updatedAt": "2021-02-12T22:59:04.249Z",
            "featured": False,
            "launches": [],
            "events": [],
        },
        {
            "id": "6026e2bc3a4653001c012104",
            "title": "Sensors Prepare to Collect Data as Perseverance Enters Mars",
            "url": "https://mars.nasa.gov/news/8859/",
            "imageUrl": "https://mars.nasa.gov/system/news_i/8859_medli2_web_image.jpg",
            "newsSite": "NASA",
            "summary": "Technology will collect critical data about the harsh entry",
            "publishedAt": "2021-02-12T20:19:00.000Z",
            "updatedAt": "2021-02-12T20:19:08.638Z",
            "featured": False,
            "launches": [],
            "events": [],
        },
    ]

    fetcher = ArticleFetcher(get_mock)

    articles = fetcher.fetch()

    assert articles == [
        Article(
            article_id="6026ec1b3a4653001c012105",
            title="Report: NASA’s only realistic path for humans on Mars is nuclear",
            url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
            image_url="https://cdn.arstechnica.net/wp-content/upload9255078_orig.jpg",
            news_site="Arstechnica",
            summary='"It\'s the kind of technology challenge that NASA was built."',
            published_at="2021-02-12T20:56:59.000Z",
            updated_at="2021-02-12T20:59:08.034Z",
            featured=False,
            launches=[],
            events=[],
        ),
        Article(
            article_id="602708383a4653001c012106",
            title="Despite its small size, Space Force plans",
            url="https://spacenews.com/despite-its-small-size-space-force-plans/",
            image_url="https://spacenews.com/wp-content/uploads/2021/02/6428324.jpg",
            news_site="SpaceNews",
            summary="The Space Force is by far the smallest branch of the U.S. .",
            published_at="2021-02-12T22:59:04.000Z",
            updated_at="2021-02-12T22:59:04.249Z",
            featured=False,
            launches=[],
            events=[],
        ),
        Article(
            article_id="6026e2bc3a4653001c012104",
            title="Sensors Prepare to Collect Data as Perseverance Enters Mars",
            url="https://mars.nasa.gov/news/8859/",
            image_url="https://mars.nasa.gov/system/news_i/8859_medli2_web_image.jpg",
            news_site="NASA",
            summary="Technology will collect critical data about the harsh entry",
            published_at="2021-02-12T20:19:00.000Z",
            updated_at="2021-02-12T20:19:08.638Z",
            featured=False,
            launches=[],
            events=[],
        ),
    ]


def test_message_formatter_format_title():
    formatter = MessageFormatter(
        [
            Article(
                article_id="6026ec1b3a4653001c012105",
                title="Report: NASA’s only realistic path for humans on Mars is nuclear",
                url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
                image_url="https://cdn.arstechnica.net/wp-content/upload9255078_orig.jpg",
                news_site="Arstechnica",
                summary='"It\'s the kind of technology challenge that NASA was built."',
                published_at="2021-02-12T20:56:59.000Z",
                updated_at="2021-02-12T20:59:08.034Z",
                featured=False,
                launches=[],
                events=[],
            ),
            Article(
                article_id="602708383a4653001c012106",
                title="Despite its small size, Space Force plans",
                url="https://spacenews.com/despite-its-small-size-space-force-plans/",
                image_url="https://spacenews.com/wp-content/uploads/2021/02/6428324.jpg",
                news_site="SpaceNews",
                summary="The Space Force is by far the smallest branch of the U.S. .",
                published_at="2021-02-12T22:59:04.000Z",
                updated_at="2021-02-12T22:59:04.249Z",
                featured=False,
                launches=[],
                events=[],
            ),
            Article(
                article_id="6026e2bc3a4653001c012104",
                title="Sensors Prepare to Collect Data as Perseverance Enters Mars",
                url="https://mars.nasa.gov/news/8859/",
                image_url="https://mars.nasa.gov/system/news_i/8859_medli2_web_image.jpg",
                news_site="NASA",
                summary="Technology will collect critical data about the harsh entry",
                published_at="2021-02-12T20:19:00.000Z",
                updated_at="2021-02-12T20:19:08.638Z",
                featured=False,
                launches=[],
                events=[],
            ),
        ]
    )
    subscriber = Subscriber(week_day=5, ordering="title", email="mark@house.com")

    formatted_message = formatter.format(subscriber)

    assert (
        formatted_message
        == """
Hello!
Here are your cool space news!

Despite its small size, Space Force plans (https://spacenews.com/despite-its-small-size-space-force-plans/) at 2021-02-12T22:59:04.000Z
Report: NASA’s only realistic path for humans on Mars is nuclear (https://arstechnica.com/science/2021/02/report-nasas-only-/) at 2021-02-12T20:56:59.000Z
Sensors Prepare to Collect Data as Perseverance Enters Mars (https://mars.nasa.gov/news/8859/) at 2021-02-12T20:19:00.000Z

Sincerly,

your Mailman!
"""
    )


def test_message_formatter_format_published_at():
    formatter = MessageFormatter(
        [
            Article(
                article_id="6026ec1b3a4653001c012105",
                title="Report: NASA’s only realistic path for humans on Mars is nuclear",
                url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
                image_url="https://cdn.arstechnica.net/wp-content/upload9255078_orig.jpg",
                news_site="Arstechnica",
                summary='"It\'s the kind of technology challenge that NASA was built."',
                published_at="2021-02-12T20:56:59.000Z",
                updated_at="2021-02-12T20:59:08.034Z",
                featured=False,
                launches=[],
                events=[],
            ),
            Article(
                article_id="602708383a4653001c012106",
                title="Despite its small size, Space Force plans",
                url="https://spacenews.com/despite-its-small-size-space-force-plans/",
                image_url="https://spacenews.com/wp-content/uploads/2021/02/6428324.jpg",
                news_site="SpaceNews",
                summary="The Space Force is by far the smallest branch of the U.S. .",
                published_at="2021-02-12T22:59:04.000Z",
                updated_at="2021-02-12T22:59:04.249Z",
                featured=False,
                launches=[],
                events=[],
            ),
            Article(
                article_id="6026e2bc3a4653001c012104",
                title="Sensors Prepare to Collect Data as Perseverance Enters Mars",
                url="https://mars.nasa.gov/news/8859/",
                image_url="https://mars.nasa.gov/system/news_i/8859_medli2_web_image.jpg",
                news_site="NASA",
                summary="Technology will collect critical data about the harsh entry",
                published_at="2021-02-12T20:19:00.000Z",
                updated_at="2021-02-12T20:19:08.638Z",
                featured=False,
                launches=[],
                events=[],
            ),
        ]
    )
    subscriber = Subscriber(week_day=5, ordering="published_at", email="mark@house.com")

    formatted_message = formatter.format(subscriber)

    assert (
        formatted_message
        == """
Hello!
Here are your cool space news!

Sensors Prepare to Collect Data as Perseverance Enters Mars (https://mars.nasa.gov/news/8859/) at 2021-02-12T20:19:00.000Z
Report: NASA’s only realistic path for humans on Mars is nuclear (https://arstechnica.com/science/2021/02/report-nasas-only-/) at 2021-02-12T20:56:59.000Z
Despite its small size, Space Force plans (https://spacenews.com/despite-its-small-size-space-force-plans/) at 2021-02-12T22:59:04.000Z

Sincerly,

your Mailman!
"""
    )


def test_message_formatter_format_random(shuffle_mock):
    formatter = MessageFormatter(
        [
            Article(
                article_id="6026ec1b3a4653001c012105",
                title="Report: NASA’s only realistic path for humans on Mars is nuclear",
                url="https://arstechnica.com/science/2021/02/report-nasas-only-/",
                image_url="https://cdn.arstechnica.net/wp-content/upload9255078_orig.jpg",
                news_site="Arstechnica",
                summary='"It\'s the kind of technology challenge that NASA was built."',
                published_at="2021-02-12T20:56:59.000Z",
                updated_at="2021-02-12T20:59:08.034Z",
                featured=False,
                launches=[],
                events=[],
            ),
            Article(
                article_id="602708383a4653001c012106",
                title="Despite its small size, Space Force plans",
                url="https://spacenews.com/despite-its-small-size-space-force-plans/",
                image_url="https://spacenews.com/wp-content/uploads/2021/02/6428324.jpg",
                news_site="SpaceNews",
                summary="The Space Force is by far the smallest branch of the U.S. .",
                published_at="2021-02-12T22:59:04.000Z",
                updated_at="2021-02-12T22:59:04.249Z",
                featured=False,
                launches=[],
                events=[],
            ),
            Article(
                article_id="6026e2bc3a4653001c012104",
                title="Sensors Prepare to Collect Data as Perseverance Enters Mars",
                url="https://mars.nasa.gov/news/8859/",
                image_url="https://mars.nasa.gov/system/news_i/8859_medli2_web_image.jpg",
                news_site="NASA",
                summary="Technology will collect critical data about the harsh entry",
                published_at="2021-02-12T20:19:00.000Z",
                updated_at="2021-02-12T20:19:08.638Z",
                featured=False,
                launches=[],
                events=[],
            ),
        ]
    )
    subscriber = Subscriber(week_day=5, ordering="random", email="mark@house.com")

    with patch("mailer.main.shuffle", shuffle_mock):
        formatted_message = formatter.format(subscriber)

    assert (
        formatted_message
        == """
Hello!
Here are your cool space news!

Report: NASA’s only realistic path for humans on Mars is nuclear (https://arstechnica.com/science/2021/02/report-nasas-only-/) at 2021-02-12T20:56:59.000Z
Sensors Prepare to Collect Data as Perseverance Enters Mars (https://mars.nasa.gov/news/8859/) at 2021-02-12T20:19:00.000Z
Despite its small size, Space Force plans (https://spacenews.com/despite-its-small-size-space-force-plans/) at 2021-02-12T22:59:04.000Z

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
