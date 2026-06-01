"""CLI: load lively CRM demo data (existing DB)."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).parent / ".env")


async def main() -> None:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    from seeds_demo_data import seed_lively_demo

    result = await seed_lively_demo(db, replace=True)
    print(result)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
