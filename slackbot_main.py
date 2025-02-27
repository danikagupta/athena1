import os
import time
from dotenv import load_dotenv
from slack_bot import SlackWordCountBot

import random

import logging

load_dotenv()

# Initialize Slack bot tokens
slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
slack_app_token = os.getenv("SLACK_APP_TOKEN")
provider = os.getenv("PROVIDER")
model = os.getenv("MODEL")
api_key = os.getenv("API_KEY")

import os
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_PROJECT"]="AgentAgentAgent"
os.environ['LANGCHAIN_ENDPOINT']="https://api.smith.langchain.com"

if not slack_bot_token or not slack_app_token:
    raise ValueError("Missing required Slack tokens in .env file")

slack_bot = SlackWordCountBot(slack_bot_token, slack_app_token,provider,model,api_key)
slack_bot.start()

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    logging.info("Shutting down Slack Bot...")