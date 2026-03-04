# main.py

import logging
from core.engine import NandhiEngine

logging.basicConfig(level=logging.INFO)

def main():
    # Initialize Nandhi Engine (Ollama backend)
    engine = NandhiEngine(
        model_name="llama3",
        knowledge_path="Knowledge"
    )

    print("\n==============================")
    print("     NANDHI CORE BRAIN")
    print("==============================")
    print("Just type anything to chat.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("Exiting Nandhi. Goodbye!")
                break

            reply = engine.generate_reply(user_input)
            print(f"Nandhi: {reply}")

        except KeyboardInterrupt:
            print("\nExiting Nandhi. Goodbye!")
            break

        except Exception as e:
            logging.error(f"Chat loop error: {e}")
            print("Nandhi: Something went wrong.")

if __name__ == "__main__":
    main()