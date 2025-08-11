#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

project_root = Path(__file__).parent
src_path = project_root / "src"

sys.path.insert(0, str(src_path))


def start():
    from src.main import main

    asyncio.run(main())


if __name__ == "__main__":
    print("🚀 Запуск Telegram Price Bot...")

    env = os.getenv("ENVIRONMENT", "production").lower()

    try:
        if env == "development":
            try:
                from watchfiles import run_process

                print("♻️  Режим hot reload активирован (ENVIRONMENT=development)")
                run_process(src_path, target=start)
            except ImportError:
                print("⚠️  watchfiles не установлен — запуск без hot reload")
                start()
        else:
            start()

    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        sys.exit(1)
