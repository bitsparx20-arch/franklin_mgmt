"""Run: python seed_whatsapp_demo.py"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from seeds_whatsapp import seed_whatsapp_samples

load_dotenv(Path(__file__).parent / ".env")


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    result = await seed_whatsapp_samples(db)
    print(result)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
