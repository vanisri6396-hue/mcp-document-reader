from llm.groq_client import GroqClient


def main():

    llm = GroqClient()

    response = llm.ask(
        "Explain MCP in related to agents AI one simple sentence."
    )

    print("\n" + "=" * 60)
    print("LLM RESPONSE")
    print("=" * 60)

    print(response)

    print("\n" + "=" * 60)
    print("LLM CONNECTION SUCCESSFUL")
    print("=" * 60)


if __name__ == "__main__":
    main()