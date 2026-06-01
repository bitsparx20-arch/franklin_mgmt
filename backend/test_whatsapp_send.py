"""Quick WhatsApp/SMS test via SpringEdge. Run: python test_whatsapp_send.py"""
import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from springedge import is_configured, send_whatsapp


async def main():
    phone = __import__("os").environ.get("SPRINGEDGE_TEST_PHONE", "+919820531826")
    print("SpringEdge configured:", is_configured())
    print("Sending to:", phone)
    result = await send_whatsapp(phone, "Franklin CRM WhatsApp test message")
    for k in ("status", "channel", "to", "message_id", "note", "error"):
        if result.get(k):
            print(f"  {k}: {result[k]}")


if __name__ == "__main__":
    asyncio.run(main())
