from core.intelligence import IntelligenceModule
from core.session_manager import SessionManager


class Orchestrator:

    def __init__(self, session: SessionManager):
        self.intelligence = IntelligenceModule()
        self.session = session

    def handle(self, user_input: str) -> str:
        # FIX: was get_context() — correct method is get_conversation_history()
        raw_context = self.session.get_conversation_history()

        # FIX: strip out 'topic' key so ollama only receives 'role' and 'content'
        context = [{"role": m["role"], "content": m["content"]} for m in raw_context]

        identity_triggers = [
            "who are you",
            "what are you",
            "identify yourself",
            "introduce yourself"
        ]

        if user_input.lower().strip() in identity_triggers:
            return (
                "I am Nandhi — your locally running AI core brain."
            )

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

        return self._identity_guard(response)

    def _identity_guard(self, response: str) -> str:
        banned_phrases = [
            "artificial intelligence",
            "ai language model",
            "as an ai",
            "i am an ai"
        ]

        for phrase in banned_phrases:
            if phrase in response.lower():
                return (
                    "I am Nandhi — your locally running AI core brain."
                )

        return response
