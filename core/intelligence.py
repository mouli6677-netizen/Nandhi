import ollama

class IntelligenceModule:
    def __init__(self, model="llama3"):
        self.model = model

    def generate(self, messages):
        response = ollama.chat(
            model=self.model,
            messages=messages
        )

        return response["message"]["content"]