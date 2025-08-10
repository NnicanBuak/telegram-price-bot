#!/usr/bin/env python3
"""
Telegram Price Bot - Запуск из корня проекта
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем src в path для импортов
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Импорты из src
from src.main import main


if __name__ == "__main__":
    print("🚀 Запуск Telegram Price Bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        sys.exit(1)
