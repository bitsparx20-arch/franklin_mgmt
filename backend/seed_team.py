"""CLI: upsert Franklin sales team into an existing database."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

load_dotenv(Path(__file__).parent / ".env")


def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


async def main() -> None:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    from seeds_team import ensure_team_users

    result = await ensure_team_users(db, hash_password=hash_password, remove_legacy=True)
    print(result)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
