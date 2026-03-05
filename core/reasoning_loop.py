import asyncio

class ReasoningLoop:
    def __init__(self, llm, async_mode=False):
        self.llm = llm
        self.async_mode = async_mode

    def think(self, prompt, max_steps=3):
        current_prompt = prompt
        reasoning_trace = []

        for step in range(max_steps):
            response = self.llm.generate(current_prompt + "\nThink step-by-step.")
            reasoning_trace.append(response)
            if "FINAL ANSWER:" in response:
                break
            current_prompt += "\nContinue reasoning."
        return reasoning_trace[-1], reasoning_trace

    async def think_async(self, prompt, max_steps=3):
        current_prompt = prompt
        reasoning_trace = []

        for step in range(max_steps):
            # Run LLM generate in executor to not block event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm.generate, current_prompt + "\nThink step-by-step.")
            reasoning_trace.append(response)
            if "FINAL ANSWER:" in response:
                break
            current_prompt += "\nContinue reasoning."
        return reasoning_trace[-1], reasoning_trace