


import asyncio
from EdgeGPT import Chatbot
import sys


from numpy import argsort
async def main():
    """
    Main function
    """

    print("Initializing...")
    bot = Chatbot(cookie_path='cookies.json')
    while True:
        prompt = input("\nYou:\n")
        if prompt == "!exit":
            break
        elif prompt == "!help":
            print(
                """
            !help - Show this help message
            !exit - Exit the program
            !reset - Reset the conversation
            """,
            )
            continue
        elif prompt == "!reset":
            await bot.reset()
            continue
        print("Bot:")
        if argsort:
            print(
                (await bot.ask(prompt=prompt))["item"]["messages"][1]["adaptiveCards"][
                    0
                ]["body"][0]["text"],
            )
        else:
            wrote = 0
            async for final, response in bot.ask_stream(prompt=prompt):
                if not final:
                    print(response[wrote:], end="")
                    wrote = len(response)
                    sys.stdout.flush()
            print()
        sys.stdout.flush()
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())