from groq import Groq
from config.settings import GROQ_API_KEY


class GroqClient:
    def __init__(self):
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        self.client = Groq(api_key=GROQ_API_KEY)

    def ask(self, user_message: str) -> str:
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
        )

        return response.choices[0].message.content

    def ask_with_tools(self, user_message: str, tools: list):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            tools=tools,
            tool_choice="auto",
        )

        return response