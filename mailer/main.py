import json
from datetime import datetime
from logging import getLogger
from operator import itemgetter
from random import shuffle
from smtplib import SMTP

from requests import get

logger = getLogger(__name__)


def get_subscribers():
    with open("data/subscribers.json") as subscribers_file:
        subscribers = json.load(subscribers_file)
        logger.info("Sending newsletter to %s subscribers.", len(subscribers))
    return subscribers


def get_articles(ordering):
    response = get("https://spaceflightnewsapi.net/api/v2/articles")
    articles = response.json()
    if ordering == "random":
        shuffle(articles)
    else:
        articles.sort(key=itemgetter(ordering))

    return articles


def format_message(articles):
    space_news = "\n".join(
        [f"{a['title']} ({a['url']}) at {a['publishedAt']}" for a in articles]
    )

    return f"""
Hello!
Here are your cool space news!

{space_news}

Sincerly,

your Mailman!
"""


def send_message(smtp, to_email, email_message):
    smtp.sendmail(
        "your@mailman.com",
        to_email,
        email_message.encode("utf8"),
    )
    logger.info("newsletter sent to %s.", to_email)


def run_mailer() -> None:
    now = datetime.now()
    with SMTP(host="localhost", port=1025) as smtp:
        for subscriber in get_subscribers():

            if subscriber["week_day"] in ["*", now.weekday()]:
                articles = get_articles(subscriber["ordering"])

                email_message = format_message(articles)

                send_message(smtp, subscriber["email"], email_message)


if __name__ == "__main__":
    run_mailer()
