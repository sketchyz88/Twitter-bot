import tweepy
import os
import logging

logger = logging.getLogger(__name__)


def post_tweet(text: str) -> str | None:
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )

    try:
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        logger.info("Posted tweet %s: %s", tweet_id, text)
        return tweet_id
    except tweepy.TweepyException as e:
        logger.error("Failed to post tweet: %s", e)
        return None
