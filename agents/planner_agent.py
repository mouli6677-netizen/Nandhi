# agents/planner_agent.py

class PlannerAgent:
    def __init__(self, llm):
        self.llm = llm

    def plan(self, user_input: str) -> str:
        prompt = (
            f"You are a planning assistant. Given the user's request, "
            f"break it down into a clear, numbered step-by-step plan.\n\n"
            f"User request: {user_input}\n\n"
            f"Plan:"
        )
        return self.llm.generate(prompt)
