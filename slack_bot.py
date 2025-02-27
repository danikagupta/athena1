import logging
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.errors import SlackApiError

from typing import Dict,List

from slackbot_agent import FirstAgent
import random

from slack_integration import get_user_information, get_sessions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SlackWordCountBot')

class SlackWordCountBot:

    def __init__(self, bot_token: str, app_token: str,provider:str,model:str,api_key:str):
        """Initialize the bot with both bot token and app-level token."""
        logger.info("[SlackBot] Initializing bot with provided tokens")
        self.client = WebClient(token=bot_token)
        self.socket_client = SocketModeClient(
            app_token=app_token,
            web_client=self.client
        )
        logger.info("[SlackBot] Initialization complete")
        self.app = FirstAgent(provider,model,api_key)
        thread_id=random.randint(1000, 9999)
        self.thread={"configurable":{"thread_id":thread_id}}

    def call_agent_graph(self,inp,user_profile:Dict,channel_history:List,message_ts:str):
        print(f"CALL AGENT GRAPH: {inp=}")
        for s in self.app.graph.stream({'message': inp,'profile':user_profile,'channel_history':channel_history,'message_ts':message_ts}, self.thread):
            for k,v in s.items():
                if resp := v.get("responseToUser"):
                    print(f"MAIN LOOP: {resp=}")
                    return resp

    def count_words(self, text: str) -> int:
        """Count words in a message."""
        return len(text.split())
    
    def handle_message(self, channel: str, user: str, text: str,user_profile:Dict,channel_history:List,message_ts:str):
        """Handle incoming message and respond with word count."""
        logger.info(f"[SlackBot] Processing message: '{text[:50]}...' from user {user}")
        word_count = self.count_words(text)
        #call_agent_graph(text)
        try:
            #response = f"Your message contains {word_count} words."
            response=self.call_agent_graph(text,user_profile,channel_history,message_ts)
            logger.info(f"[SlackBot] Sending response to channel {channel}")
            self.client.chat_postMessage(
                channel=channel,
                text=response,
                thread_ts=None  # Will create a new message, not a thread
            )
            logger.info("[SlackBot] Response sent successfully")
        except SlackApiError as e:
            error_msg = e.response['error']
            logger.error(f"[SlackBot] Error sending message: {error_msg}")
            raise  # Re-raise to allow proper error handling
            
    def process_event(self, client: SocketModeClient, req: SocketModeRequest):
        """Process incoming Socket Mode events."""
        logger.info(f"[SlackBot] Received event: {req.type}")
        logger.debug(f"[SlackBot] Full event payload: {req.payload}")
        
        if req.type == "events_api":
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)
            logger.info("[SlackBot] Acknowledged event request")
            
            # Process the event
            event = req.payload["event"]
            logger.info(f"[SlackBot] Event type: {event.get('type')}")
            
            if event["type"] == "message" and "subtype" not in event:
                channel = event.get("channel")
                user = event.get("user")
                text = event.get("text")
                
                # Get bot's own user ID if we haven't stored it yet
                if not hasattr(self, 'bot_user_id'):
                    try:
                        auth_response = self.client.auth_test()
                        self.bot_user_id = auth_response["user_id"]
                        logger.info(f"[SlackBot] Bot user ID: {self.bot_user_id}")
                    except Exception as e:
                        logger.error(f"[SlackBot] Error getting bot user ID: {str(e)}")
                        self.bot_user_id = None

                # Ignore messages from the bot itself
                if user == self.bot_user_id:
                    logger.info("[SlackBot] Ignoring message from self")
                    return
                
                if channel and user and text:
                    logger.info(f"[SlackBot] Processing message: '{text}' from user {user} in channel {channel}")
                    #user_info = self.client.users_info(user=user)
                    #user_data = user_info.get("user", {})
                    #user_profile = user_data.get("profile", {})
                    user_profile=get_user_information(self.client,user)
                    
                    # Get channel name
                    #channel_info = self.client.conversations_info(channel=channel)
                    #channel_data = channel_info.get("channel", {})
                    #channel_name = channel_data.get("name", "unknown-channel")
                    channel_history=get_sessions(self.client,channel)
                    
                    # Get message details
                    word_count = self.count_words(text)
                    message_ts = event.get("ts")
                    # Run handle_message directly
                    self.handle_message(channel, user, text,user_profile,channel_history,message_ts)
                else:
                    logger.warning(f"[SlackBot] Incomplete message event received: channel={channel}, user={user}, has_text={bool(text)}")
            else:
                logger.info(f"[SlackBot] Skipping non-message event or message with subtype: {event.get('subtype', 'no subtype')}")
                    
    def start(self):
        """Start the Socket Mode client."""
        logger.info("[SlackBot] Starting Socket Mode client...")
        try:
            self.socket_client.socket_mode_request_listeners.append(self.process_event)
            logger.info("[SlackBot] Added event listener")
            self.socket_client.connect()
            logger.info("[SlackBot] Socket Mode connection initiated")
        except Exception as e:
            logger.error(f"[SlackBot] Failed to start Socket Mode client: {str(e)}")
            raise