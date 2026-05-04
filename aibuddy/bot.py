"""
bot.py - AiBuddyBot: Microsoft Bot Framework ActivityHandler powered by Groq Llama 3.

Architecture decisions:
- Conversation history is stored in-process (dict keyed by user ID).  For a
  multi-instance deployment this should be replaced with a shared store (e.g.
  Redis), but for a single-container Koyeb free-tier deployment an in-process
  dict is sufficient and avoids an extra dependency.
- History is capped at the last 10 messages to keep token usage predictable.
- All external I/O (Groq API) is done with async/await so the aiohttp event
  loop is never blocked.
"""

import logging
from typing import Dict, List

from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount
from groq import AsyncGroq

from config import Config

logger = logging.getLogger(__name__)

# Maximum number of conversation turns (user + assistant messages) kept per user
MAX_HISTORY = 10

# System prompt injected at the start of every Groq request
SYSTEM_PROMPT = (
    "You are AiBuddy, a helpful, friendly AI assistant in Microsoft Teams. "
    "Provide clear, concise, and useful responses. "
    "Use markdown formatting when appropriate. "
    "Keep responses focused and avoid unnecessary verbosity."
)


class AiBuddyBot(ActivityHandler):
    """Main bot class.  Handles incoming messages and lifecycle events.

    Attributes:
        config: Application configuration object.
        groq_client: Async Groq client used to call the Llama 3 API.
        conversation_history: Per-user chat history (user_id → message list).
    """

    def __init__(self, config: Config) -> None:
        """Initialise the bot with the given configuration.

        Args:
            config: Populated :class:`~config.Config` instance.
        """
        super().__init__()
        self.config = config
        self.groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)
        # {user_id: [{"role": "user"/"assistant", "content": "..."}, ...]}
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        logger.info("AiBuddyBot initialised with model: %s", config.GROQ_MODEL)

    # ------------------------------------------------------------------
    # Bot Framework lifecycle callbacks
    # ------------------------------------------------------------------

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle an incoming message from a Teams user.

        Routes special commands to dedicated helpers and all other input
        to the Groq Llama 3 API, maintaining per-user conversation history.

        Args:
            turn_context: The current turn context provided by the framework.
        """
        user_message: str = (turn_context.activity.text or "").strip()
        user_id: str = turn_context.activity.from_property.id

        if not user_message:
            await turn_context.send_activity(
                MessageFactory.text("Please type a message and I'll be happy to help! 😊")
            )
            return

        # ---- Special commands (case-insensitive) ----
        command = user_message.lower()

        if command == "help":
            await self._send_help(turn_context)
            return

        if command == "about":
            await self._send_about(turn_context)
            return

        if command in ("clear", "reset"):
            self.conversation_history.pop(user_id, None)
            await turn_context.send_activity(
                MessageFactory.text(
                    "🗑️ Conversation history cleared! Starting fresh. How can I help you?"
                )
            )
            return

        # ---- Regular message: call Groq API ----
        # Inform the user we are working on it
        await turn_context.send_activity(MessageFactory.text("🤔 Thinking..."))

        # Retrieve or create history for this user
        history = self.conversation_history.setdefault(user_id, [])

        # Append the new user message
        history.append({"role": "user", "content": user_message})

        # Keep only the last MAX_HISTORY messages to control token usage
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]
            self.conversation_history[user_id] = history

        try:
            # Build the full message list: system prompt + history
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

            logger.debug(
                "Calling Groq API for user %s with %d history messages",
                user_id,
                len(history),
            )

            response = await self.groq_client.chat.completions.create(
                model=self.config.GROQ_MODEL,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )

            ai_reply: str = response.choices[0].message.content

            # Append AI response to history
            history.append({"role": "assistant", "content": ai_reply})

            await turn_context.send_activity(MessageFactory.text(ai_reply))

        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "Error calling Groq API for user %s: %s",
                user_id,
                exc,
                exc_info=True,
            )
            # Remove the unanswered user message so history stays consistent
            history.pop()
            await turn_context.send_activity(
                MessageFactory.text(
                    "❌ Sorry, I couldn't get a response right now. "
                    "Please try again in a moment."
                )
            )

    async def on_members_added_activity(
        self,
        members_added: List[ChannelAccount],
        turn_context: TurnContext,
    ) -> None:
        """Send a welcome message whenever the bot or a new user joins.

        Args:
            members_added: List of accounts that were added to the conversation.
            turn_context: The current turn context provided by the framework.
        """
        for member in members_added:
            # Don't welcome the bot itself
            if member.id != turn_context.activity.recipient.id:
                welcome_text = (
                    "👋 Hi! I'm **AiBuddy**, your AI assistant powered by Llama 3.\n\n"
                    "Ask me anything! For example:\n"
                    '• "Help me write a professional email"\n'
                    '• "Explain machine learning simply"\n'
                    '• "Give me 5 productivity tips"\n\n'
                    "**Commands:**\n"
                    "• `help` - Show all commands\n"
                    "• `about` - Learn about AiBuddy\n"
                    "• `clear` - Clear conversation history"
                )
                await turn_context.send_activity(MessageFactory.text(welcome_text))

    # ------------------------------------------------------------------
    # Command helpers
    # ------------------------------------------------------------------

    async def _send_help(self, turn_context: TurnContext) -> None:
        """Send a formatted help message listing all available commands.

        Args:
            turn_context: The current turn context provided by the framework.
        """
        help_text = (
            "🤖 **AiBuddy Help**\n\n"
            "I'm an AI assistant powered by Llama 3. Here's what you can do:\n\n"
            "**Commands:**\n"
            "• `help` — Show this help message\n"
            "• `about` — Learn about AiBuddy\n"
            "• `clear` or `reset` — Clear your conversation history\n\n"
            "**Tips:**\n"
            "• Ask me anything — writing, coding, analysis, brainstorming, and more\n"
            "• I remember the last 10 messages for context\n"
            "• Use `clear` to start a fresh conversation\n\n"
            "**Example questions:**\n"
            '• "Summarise this text: …"\n'
            '• "Write a Python function that …"\n'
            '• "What are the pros and cons of …"\n'
        )
        await turn_context.send_activity(MessageFactory.text(help_text))

    async def _send_about(self, turn_context: TurnContext) -> None:
        """Send an informational message about AiBuddy.

        Args:
            turn_context: The current turn context provided by the framework.
        """
        about_text = (
            "ℹ️ **About AiBuddy**\n\n"
            "**Version:** 1.0.0\n\n"
            "**AI Engine:** Llama 3 via [Groq](https://groq.com) — "
            "ultra-fast inference for responsive conversations.\n\n"
            "**Built with:**\n"
            "• Microsoft Bot Framework SDK (Python)\n"
            "• Groq Llama 3 API\n"
            "• aiohttp async web server\n"
            "• Deployed on Koyeb free tier\n\n"
            "**Links:**\n"
            "• 🔒 [Privacy Policy](https://aswintechie.github.io/AiBuddy/privacy)\n"
            "• 🛟 [Support](https://aswintechie.github.io/AiBuddy/support)\n"
            "• 💻 [Source Code](https://github.com/Aswintechie/AiBuddy)\n"
        )
        await turn_context.send_activity(MessageFactory.text(about_text))
