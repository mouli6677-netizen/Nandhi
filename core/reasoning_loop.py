class ReasoningLoop:
    def __init__(self, llm):
        self.llm = llm

    def think(self, prompt, max_steps=3):
        current_prompt = prompt
        reasoning_trace = []

        for step in range(max_steps):
            response = self.llm.generate(
                current_prompt + "\nThink step-by-step."
            )

            reasoning_trace.append(response)

            if "FINAL ANSWER:" in response:
                break

            current_prompt += "\nContinue reasoning."

        return reasoning_trace[-1], reasoning_trace