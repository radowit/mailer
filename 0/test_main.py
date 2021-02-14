# pylint: disable=redefined-outer-name,line-too-long
import json
from datetime import datetime
from shutil import move
from unittest.mock import Mock, call, patch

import pytest


@pytest.fixture
def smtp_mock():
    smtp_mock = Mock()
    smtp_mock().__enter__ = lambda _: smtp_mock
    smtp_mock().__exit__ = lambda _, *args: None
    return smtp_mock


@pytest.fixture
def get_mock():
    return Mock()


@pytest.fixture
def shuffle_mock():
    def _shuffle(alist):
        alist.sort(key=lambda d: d["summary"])

    return _shuffle


@pytest.fixture
def run_mailer(smtp_mock, get_mock, shuffle_mock):
    with patch("smtplib.SMTP", smtp_mock):
        with patch("requests.get", get_mock):
            with patch("random.shuffle", shuffle_mock):
                from mailer.main import (  # pylint: disable=import-outside-toplevel
                    run_mailer,
                )

                return run_mailer


@pytest.fixture(autouse=True)
def test_data_file():
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
    yield
    move("data/prod_subscribers.json", "data/subscribers.json")


def test_run_mailer(run_mailer, smtp_mock, get_mock):
    get_mock.return_value.json.return_value = [
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

    run_mailer()

    get_mock.assert_called_with("https://spaceflightnewsapi.net/api/v2/articles")
    get_mock.assert_called_with("https://spaceflightnewsapi.net/api/v2/articles")
    assert smtp_mock.sendmail.call_args_list == [
        call(
            "your@mailman.com",
            "mark@house.com",
            b"\n".join(
                [
                    b"",
                    b"Hello!",
                    b"Here are your cool space news!",
                    b"",
                    b"Sensors Prepare to Collect Data as Perseverance Enters Mars (https://mars.nasa.gov/news/8859/) at 2021-02-12T20:19:00.000Z",
                    b"Report: NASA\xe2\x80\x99s only realistic path for humans on Mars is nuclear (https://arstechnica.com/science/2021/02/report-nasas-only-/) at 2021-02-12T20:56:59.000Z",
                    b"Despite its small size, Space Force plans (https://spacenews.com/despite-its-small-size-space-force-plans/) at 2021-02-12T22:59:04.000Z",
                    b"",
                    b"Sincerly,",
                    b"",
                    b"your Mailman!",
                    b"            ",
                ]
            ),
        ),
        call(
            "your@mailman.com",
            "mark@black.com",
            b"\n".join(
                [
                    b"",
                    b"Hello!",
                    b"Here are your cool space news!",
                    b"",
                    b"Report: NASA\xe2\x80\x99s only realistic path for humans on Mars is nuclear (https://arstechnica.com/science/2021/02/report-nasas-only-/) at 2021-02-12T20:56:59.000Z",
                    b"Sensors Prepare to Collect Data as Perseverance Enters Mars (https://mars.nasa.gov/news/8859/) at 2021-02-12T20:19:00.000Z",
                    b"Despite its small size, Space Force plans (https://spacenews.com/despite-its-small-size-space-force-plans/) at 2021-02-12T22:59:04.000Z",
                    b"",
                    b"Sincerly,",
                    b"",
                    b"your Mailman!",
                    b"            ",
                ]
            ),
        ),
    ]
