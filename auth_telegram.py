"""Interactive Telegram authentication script."""

import asyncio

from drug_trafficking_osint.core.config import Settings


async def main():
    settings = Settings.from_environment()

    print("Starting Telegram authentication...")
    print(f"API ID: {settings.telegram.api_id}")
    print(f"Session: {settings.telegram.session_name}")
    print()

    # Create underlying Telethon client directly for auth
    from pathlib import Path

    from telethon import TelegramClient as TelethonClient

    session_path = Path.cwd() / "sessions" / settings.telegram.session_name
    session_path.parent.mkdir(exist_ok=True)

    telethon_client = TelethonClient(
        str(session_path),
        api_id=settings.telegram.api_id,
        api_hash=settings.telegram.api_hash,
    )

    print("Connecting to Telegram...")
    await telethon_client.connect()

    if not await telethon_client.is_user_authorized():
        print("First-time authentication required.")
        print("You will receive a code via Telegram app.")
        print()

        phone = input("Enter your phone number (with country code, e.g., +1234567890): ")
        await telethon_client.send_code_request(phone)

        code = input("Enter the code you received: ")
        try:
            await telethon_client.sign_in(phone, code)
            print("Authentication successful!")
        except Exception as e:
            print(f"Sign in error: {e}")
            # Try 2FA
            password = input("Enter 2FA password (if enabled): ")
            await telethon_client.sign_in(password=password)
            print("Authentication successful!")
    else:
        print("Already authenticated!")

    await telethon_client.disconnect()
    print("Session saved.")


if __name__ == "__main__":
    asyncio.run(main())
