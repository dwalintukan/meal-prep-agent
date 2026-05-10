from agent.workflows import Workflow


class ChatWorkflow(Workflow):
    async def run(self) -> str:
        return (
            "I can help you plan meals and add recipes. "
            "Try saying: 'Plan my meals', 'What should I eat this week', 'Make me a meal plan'"
        )
