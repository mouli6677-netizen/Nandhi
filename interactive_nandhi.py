# interactive_nandhi.py

import asyncio
from core.engine_instance import engine  # Singleton engine from engine_instance.py

async def interactive_loop():
    print("=== Nandhi AI Assistant Interactive ===")
    print("Type 'exit' to quit.")
    print("You can also type 'analyze_image <path>' or 'analyze_video <path>'\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Exiting Nandhi interactive session...")
            break

        if user_input.startswith("analyze_image "):
            path = user_input[len("analyze_image "):].strip()
            response = engine.analyze_image(path)
        elif user_input.startswith("analyze_video "):
            path = user_input[len("analyze_video "):].strip()
            response = engine.analyze_video(path)
        else:
            response = engine.generate_reply(user_input)

        print(f"Nandhi: {response}\n")
        print(f"Memory Count: {engine.memory_count()}\n")


async def main():
    await interactive_loop()

if __name__ == "__main__":
    asyncio.run(main())