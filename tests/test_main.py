# pylint: disable=redefined-outer-name,line-too-long,import-outside-toplevel
import json
from datetime import datetime
from shutil import move
from unittest.mock import Mock, patch

import pytest

from mailer.main import format_message, get_subscribers, send_message


@pytest.fixture
def get_mock():
    return Mock()


@pytest.fixture
def shuffle_mock():
    def _shuffle(alist):
        alist.sort(key=lambda d: d["summary"])

    return _shuffle


@pytest.fixture
def run_mailer(send_message_mock, get_articles):
    with patch("mailer.main.get_articles", get_articles):
        with patch("mailer.main.format_message"):
            with patch("mailer.main.send_message", send_message_mock):
                with patch("mailer.main.SMTP"):
                    from mailer.main import run_mailer

                    yield run_mailer


@pytest.fixture
def data_file_mock():
    now = datetime.now()
    move("data/subscribers.json", "data/prod_subscribers.json")
    subscribers = [
        {
            "week_day": now.weekday(),
            "ordering": "publishedAt",
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
def get_articles(get_mock, shuffle_mock):
    with patch("mailer.main.get", get_mock):
        with patch("mailer.main.shuffle", shuffle_mock):
            from mailer.main import get_articles

            yield get_articles


@pytest.fixture
def send_message_mock():
    return Mock()


def test_get_subscribers(data_file_mock):
    subscribers = get_subscribers()

    assert subscribers == data_file_mock


def test_get_articles_by_title(get_articles, get_mock):
    get_mock.return_value.json.return_value = [
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
    articles = get_articles("title")

    assert articles == [
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


def test_get_articles_by_published_at(get_articles, get_mock):
    get_mock.return_value.json.return_value = [
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
    articles = get_articles("publishedAt")

    assert articles == [
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
    ]


def test_get_articles_sorted_randomly(get_articles, get_mock):
    get_mock.return_value.json.return_value = [
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
    articles = get_articles("random")

    assert articles == [
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
    ]


def test_format_message():
    formatted_message = format_message(
        [
            {
                "title": "Water on Mars",
                "url": "http://water.mars",
                "publishedAt": "now",
            },
            {
                "title": "Space medusas attack!",
                "url": "http://news.hoax/space-medusas",
                "publishedAt": "yesterday",
            },
            {
                "title": "Cats on mars",
                "url": "http://cats.bebop/mars",
                "publishedAt": "?",
            },
        ]
    )

    assert (
        formatted_message
        == """
Hello!
Here are your cool space news!

Water on Mars (http://water.mars) at now
Space medusas attack! (http://news.hoax/space-medusas) at yesterday
Cats on mars (http://cats.bebop/mars) at ?

Sincerly,

your Mailman!
"""
    )


def test_send_message():
    smtp = Mock()
    send_message(smtp, "jeremy@stone.com", "abc")

    smtp.sendmail.assert_called_with(
        "your@mailman.com",
        "jeremy@stone.com",
        b"abc",
    )


def test_run_mailer(run_mailer, data_file_mock, get_mock, send_message_mock):
    del data_file_mock

    get_mock.return_value.json.return_value = [
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

    run_mailer()

    sent_to = {c.args[1] for c in send_message_mock.call_args_list}

    assert sent_to == {"mark@house.com", "mark@black.com"}
