import anthropic
import yaml
import random
import os


def generate_tweet() -> str:
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    topic = random.choice(config["topics"])
    system_prompt = config.get("system_prompt", "You are a concise, engaging Twitter copywriter.")
    user_prompt = (
        f"Write a single tweet about: {topic}. "
        "Max 280 characters. No hashtag spam. Return only the tweet text."
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    tweet_text = message.content[0].text.strip()

    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."

    return tweet_text
