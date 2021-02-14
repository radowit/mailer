import json
from datetime import datetime
from logging import getLogger
from operator import itemgetter
from random import shuffle
from smtplib import SMTP

from requests import get

logger = getLogger(__name__)


def run_mailer() -> None:
    with open("data/subscribers.json") as subscribers_file:
        subscribers = json.load(subscribers_file)
        logger.info("Sending newsletter to %s subscribers.", len(subscribers))

    now = datetime.now()
    with SMTP(host="localhost", port=1025) as smtp:
        for subscriber in subscribers:
            if subscriber["week_day"] in ["*", now.weekday()]:
                response = get("https://spaceflightnewsapi.net/api/v2/articles")
                articles = response.json()

                newsletter_articles = []
                if subscriber["ordering"] == "random":
                    shuffle(articles)
                else:
                    articles.sort(key=itemgetter(subscriber["ordering"]))

                for article in articles:
                    newsletter_articles.append(
                        {
                            "title": article["title"],
                            "url": article["url"],
                            "summary": article["summary"],
                            "publishedAt": article["publishedAt"],
                        }
                    )

                space_news = "\n".join(
                    [
                        f"{a['title']} ({a['url']}) at {a['publishedAt']}"
                        for a in articles
                    ]
                )

                newsletter = f"""
Hello!
Here are your cool space news!

{space_news}

Sincerly,

your Mailman!
            """

                smtp.sendmail(
                    "your@mailman.com", subscriber["email"], newsletter.encode("utf8")
                )
                logger.info("newsletter sent to %s.", subscriber["email"])
                print(".")


if __name__ == "__main__":
    run_mailer()
