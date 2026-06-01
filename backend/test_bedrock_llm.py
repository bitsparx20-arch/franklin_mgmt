"""Test Bedrock connectivity. Run: python test_bedrock_llm.py"""
import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from bedrock_llm import complete_chat, status


async def main():
    print(status())
    reply = await complete_chat(
        "You are a helpful assistant. Reply in one short sentence.",
        [],
        "Say hello from Franklin CRM.",
    )
    print("Reply:", reply[:500])


if __name__ == "__main__":
    asyncio.run(main())
