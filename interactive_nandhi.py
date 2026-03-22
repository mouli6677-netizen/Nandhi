# interactive_nandhi.py
# FIX: the original wrapped a synchronous input() loop inside async def and
# called asyncio.run(main()). input() blocks the event loop entirely, making
# the async wrapper pointless and potentially confusing on some platforms.
# Converted to a plain synchronous loop.  If genuine async I/O is needed
# in future (e.g. async readline), the structure can be revisited then.

from core.engine_instance import engine


def interactive_loop():
    print("=== Nandhi AI Assistant Interactive ===")
    print("Type 'exit' to quit.")
    print("You can also type 'analyze_image <path>' or 'analyze_video <path>'\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
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


if __name__ == "__main__":
    interactive_loop()