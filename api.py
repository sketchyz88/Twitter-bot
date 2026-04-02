from flask import Flask, jsonify, request
import yaml
import os
import logging
from dotenv import load_dotenv
from generator import generate_tweet
from poster import post_tweet

load_dotenv()

app = Flask(__name__)
logger = logging.getLogger(__name__)


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def save_config(config):
    with open("config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


@app.route("/topics", methods=["GET"])
def get_topics():
    config = load_config()
    return jsonify({"topics": config.get("topics", [])})


@app.route("/topics", methods=["POST"])
def update_topics():
    data = request.get_json()
    if not data or "topics" not in data:
        return jsonify({"error": "topics field required"}), 400
    config = load_config()
    config["topics"] = data["topics"]
    save_config(config)
    return jsonify({"success": True})


@app.route("/generate", methods=["GET"])
def generate():
    try:
        tweet = generate_tweet()
        return jsonify({"tweet": tweet})
    except Exception as e:
        logger.error("Generate error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/post", methods=["POST"])
def post():
    try:
        tweet = generate_tweet()
        tweet_id = post_tweet(tweet)
        return jsonify({"tweet": tweet, "tweet_id": tweet_id, "success": tweet_id is not None})
    except Exception as e:
        logger.error("Post error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/config", methods=["GET"])
def get_config():
    config = load_config()
    return jsonify({"interval_hours": config.get("interval_hours", 4)})


@app.route("/config", methods=["POST"])
def update_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    config = load_config()
    if "interval_hours" in data:
        config["interval_hours"] = int(data["interval_hours"])
    save_config(config)
    return jsonify({"success": True})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5000, debug=False)
