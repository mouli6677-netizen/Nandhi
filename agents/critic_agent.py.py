class CriticAgent:
    def __init__(self, llm):
        self.llm = llm

    def review(self, answer):
        prompt = f"""
You are a strict AI critic.
Review the following answer.
If incorrect, explain error.
If correct, say APPROVED.

Answer:
{answer}
"""
        return self.llm.generate(prompt)