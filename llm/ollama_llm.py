import ollama
from llm.base_llm import BaseLLM

class OllamaLLM(BaseLLM):
    def __init__(self, model_name="llama3"):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        try:
            # FIX: was subprocess ["ollama", "query", ...] — "query" is not a valid
            # ollama CLI command. Use the ollama Python library instead, which is
            # already installed (it's how intelligence.py works too).
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            return f"LLM error: {e}"
