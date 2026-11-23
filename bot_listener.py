import os
import time
from dotenv import load_dotenv

load_dotenv()

from scraper import sync_subscribers


def main():
    print("🤖 Telegram Bot Real-Time Listener is running!")
    print("Checking for new subscribers every 3 seconds. Press Ctrl+C to stop.")
    while True:
        try:
            sync_subscribers()
        except Exception as e:
            print(f"Sync error: {e}")
        time.sleep(3)


if __name__ == "__main__":
    main()
