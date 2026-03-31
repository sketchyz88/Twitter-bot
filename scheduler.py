import datetime
import logging
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from generator import generate_tweet
from poster import post_tweet

logger = logging.getLogger(__name__)


def run_cycle():
    logger.info("Starting tweet cycle")
    tweet_text = generate_tweet()
    logger.info("Generated: %s", tweet_text)
    post_tweet(tweet_text)


def start():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    interval_hours = config.get("interval_hours", 4)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_cycle,
        "interval",
        hours=interval_hours,
        next_run_time=datetime.datetime.now(),
    )
    logger.info("Scheduler started. Posting every %s hour(s).", interval_hours)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
