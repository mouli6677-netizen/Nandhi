from llm.ollama_llm import OllamaLLM
from memory.embedder import Embedder
from memory.vector_store import VectorStore
from core.reasoning_loop import ReasoningLoop


class NandhiEngine:
    def __init__(self, model_name="llama3", knowledge_path="Knowledge"):
        self.llm = OllamaLLM(model_name)
        self.knowledge_path = knowledge_path

        self.embedder = Embedder()
        self.vector_store = VectorStore(self.embedder)
        self.reasoning = ReasoningLoop(self.llm)

    # --- Inlined PlannerAgent ---
    def _plan(self, user_input: str) -> str:
        prompt = (
            f"You are a planning assistant. Break the user's request into "
            f"a clear numbered step-by-step plan.\n\n"
            f"User request: {user_input}\n\nPlan:"
        )
        return self.llm.generate(prompt)

    # --- Inlined CriticAgent ---
    def _review(self, answer: str) -> str:
        prompt = (
            f"Review the following answer for accuracy and completeness. "
            f"If it is good, reply with APPROVED. "
            f"If it needs improvement, explain why.\n\nAnswer: {answer}"
        )
        return self.llm.generate(prompt)

    # --- Inlined MemoryAgent ---
    def _retrieve_memories(self, user_input: str) -> list:
        results = self.vector_store.search(user_input, top_k=3)
        return [r["text"] for r in results if "text" in r]

    def generate_reply(self, user_input: str) -> str:
        plan = self._plan(user_input)

        memories = self._retrieve_memories(user_input)

        memory_context = "\n".join(memories) if memories else ""
        prompt = f"{user_input}\nPlan:\n{plan}"
        if memory_context:
            prompt = f"Relevant memories:\n{memory_context}\n\n{prompt}"

        answer, trace = self.reasoning.think(prompt)

        review = self._review(answer)

        if "APPROVED" not in review:
            answer = self.llm.generate(prompt + "\nImprove previous answer.")

        self.vector_store.add(user_input + " " + answer)

        return answer
