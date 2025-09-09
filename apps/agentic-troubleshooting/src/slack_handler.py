"""Simple Slack handler for the K8s troubleshooting agent."""

import logging
import asyncio
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from src.config.settings import Config
from src.agents.agent_orchestrator import OrchestratorAgent
# from src.agents.k8s_orchestrator import K8sOrchestrator

logger = logging.getLogger(__name__)


class SlackHandler:
    """Handles Slack events and routes them to the K8s agent."""
    
    def __init__(self):
        """Initialize Slack handler and K8s agent."""
        # Validate configuration
        Config.validate()
        
        # Initialize Slack app
        self.app = App(
            token=Config.SLACK_BOT_TOKEN,
            signing_secret=Config.SLACK_SIGNING_SECRET
        )
        
        # Initialize K8s orchestrator
        self.orchestrator = OrchestratorAgent()
        
        # Track threads where bot has responded
        self.active_threads = set()
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register Slack event handlers."""
        # Get bot user ID once during initialization
        bot_user_id = self.app.client.auth_test()['user_id']
        logger.info(f"Bot user ID: {bot_user_id} - Registering event handlers...")
        
        # Handle messages (excluding bot messages)
        @self.app.event("message")
        def handle_message(event, say, client: WebClient):
            """Handle incoming messages."""
            try:
                # Skip if this is a message_changed or message_deleted event
                subtype = event.get("subtype")
                if subtype:
                    logger.info(f"Skipping message with subtype: {subtype}")
                    return
                
                text = event.get("text", "")
                user = event.get("user", "")
                channel = event.get("channel", "")
                thread_ts = event.get("thread_ts", event.get("ts"))
                bot_id = event.get("bot_id")
                
                logger.info(f"Message received - User: {user}, Bot ID: {bot_id}, Channel: {channel}")
                
                # Skip if message is from any bot (including this one)
                if bot_id:
                    logger.info(f"Skipping message from bot: {bot_id}")
                    return
                
                # Skip if message is from the bot itself (belt and suspenders)
                if user and user == bot_user_id:
                    logger.info("Skipping bot's own message (by user ID)")
                    return
                
                # Skip if no user (some bot messages don't have user field)
                if not user:
                    logger.info("Skipping message with no user field")
                    return
                
                # Check if bot is mentioned - if so, skip here as app_mention will handle it
                is_mention = f"<@{bot_user_id}>" in text
                if is_mention:
                    logger.info("Message contains mention - will be handled by app_mention event")
                    return
                
                # Check if this is a reply in an active thread
                is_active_thread = False
                if thread_ts and thread_ts != event.get("ts"):
                    # This is a threaded message
                    thread_key = f"{channel}:{thread_ts}"
                    is_active_thread = thread_key in self.active_threads
                    if is_active_thread:
                        logger.info(f"Message is in active thread: {thread_key}")
                
                # Check if agent should respond
                should_respond = self.orchestrator.should_respond(text, is_mention) or is_active_thread
                logger.info(f"Agent should respond: {should_respond} for message: '{text[:50]}...' (active_thread: {is_active_thread})")
                if not should_respond:
                    logger.info("Agent decided not to respond to this message")
                    return
                
                # Get thread context if enabled
                context = None
                if Config.ENABLE_THREAD_CONTEXT and thread_ts != event.get("ts"):
                    try:
                        result = client.conversations_replies(
                            channel=channel,
                            ts=thread_ts,
                            limit=Config.MAX_CONTEXT_MESSAGES
                        )
                        messages = result.get("messages", [])
                        context = "\n".join([
                            f"{msg.get('user', 'User')}: {msg.get('text', '')}"
                            for msg in messages[:-1]  # Exclude current message
                        ])
                    except Exception as e:
                        logger.error(f"Error getting thread context: {e}")
                
                # Add delay to avoid appearing too eager
                if Config.RESPONSE_DELAY_SECONDS > 0:
                    asyncio.run(asyncio.sleep(Config.RESPONSE_DELAY_SECONDS))
                
                # Get response from agent with thread_id for memory
                thread_key = f"{channel}:{thread_ts}"
                logger.info("Generating response from agent...")
                response = self.orchestrator.respond(text, thread_key, context)
                logger.info(f"Agent response generated: {len(response)} characters")
                
                # Send response in thread
                logger.info(f"Sending response to thread: {thread_ts}")
                say(
                    text=response,
                    thread_ts=thread_ts
                )
                logger.info("Response sent successfully")
                
                # Mark this thread as active
                thread_key = f"{channel}:{thread_ts}"
                self.active_threads.add(thread_key)
                logger.info(f"Added thread to active threads: {thread_key}")
                
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                say(
                    text="Sorry, I encountered an error processing your message.",
                    thread_ts=thread_ts
                )
        
        # Handle app mentions
        @self.app.event("app_mention")
        def handle_mention(event, say):
            """Handle direct mentions."""
            try:
                text = event.get("text", "")
                user = event.get("user", "")
                thread_ts = event.get("thread_ts", event.get("ts"))
                
                logger.info(f"App mention received - User: {user}, Text: {text[:50]}...")
                
                # Skip if mention is from the bot itself (shouldn't happen, but just in case)
                if user == bot_user_id:
                    logger.info("Skipping bot's own mention")
                    return
                
                # Remove mention from text
                text = text.replace(f"<@{bot_user_id}>", "").strip()
                
                # Get response from agent with thread_id for memory
                channel = event.get("channel", "")
                thread_key = f"{channel}:{thread_ts}"
                logger.info("Generating response for mention...")
                response = self.orchestrator.respond(text, thread_key)
                logger.info(f"Mention response generated: {len(response)} characters")
                
                # Ensure response is not empty
                if not response or not response.strip():
                    logger.warning("Empty response detected, using fallback")
                    response = "I'm here to help with Kubernetes troubleshooting. How can I assist you?"
                
                # Send response in thread
                logger.info(f"Sending mention response to thread: {thread_ts}")
                say(
                    text=response,
                    thread_ts=thread_ts
                )
                logger.info("Mention response sent successfully")
                
                # Mark this thread as active
                channel = event.get("channel", "")
                thread_key = f"{channel}:{thread_ts}"
                self.active_threads.add(thread_key)
                logger.info(f"Added thread to active threads: {thread_key}")
                
            except Exception as e:
                logger.error(f"Error handling mention: {e}")
                say(
                    text="Sorry, I encountered an error processing your request.",
                    thread_ts=thread_ts
                )
    
    def start(self):
        """Start the Slack handler."""
        try:
            # Start socket mode handler
            handler = SocketModeHandler(self.app, Config.SLACK_APP_TOKEN)
            logger.info("Starting Slack handler...")
            handler.start()
        except Exception as e:
            logger.error(f"Error starting Slack handler: {e}")
            raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the handler
    handler = SlackHandler()
    handler.start()
