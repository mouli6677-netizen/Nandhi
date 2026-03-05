# core/orchestrator.py

from core.intelligence import IntelligenceModule
from core.session_manager import SessionManager


class Orchestrator:

    def __init__(self, session: SessionManager):
        self.intelligence = IntelligenceModule()
        self.session = session

    def handle(self, user_input: str) -> str:
        identity_triggers = [
            "who are you",
            "what are you",
            "identify yourself",
            "introduce yourself"
        ]

        if user_input.lower().strip() in identity_triggers:
            reply = "I am Nandhi — your locally running AI core brain."
            # FIX: save both sides of the exchange so history stays accurate
            self.session.save_user_message(user_input)
            self.session.save_ai_message(reply)
            return reply

        # FIX: save the user message BEFORE reading history so it is included
        # in the context sent to the model. Previously the user turn was never
        # persisted, so the model only ever saw old assistant messages.
        self.session.save_user_message(user_input)

        raw_context = self.session.get_conversation_history()

        # Strip out 'topic' key so ollama only receives 'role' and 'content'
        context = [{"role": m["role"], "content": m["content"]} for m in raw_context]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Nandhi, a structured local AI core brain. "
                    "Never describe yourself as an artificial intelligence."
                )
            }
        ] + context

        response = self.intelligence.generate(messages)
        response = self._identity_guard(response)

        self.session.save_ai_message(response)
        return response

    def _identity_guard(self, response: str) -> str:
        banned_phrases = [
            "artificial intelligence",
            "ai language model",
            "as an ai",
            "i am an ai"
        ]

        for phrase in banned_phrases:
            if phrase in response.lower():
                return "I am Nandhi — your locally running AI core brain."

        return response
