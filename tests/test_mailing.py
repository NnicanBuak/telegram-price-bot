import os
import pytest
import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_e2e_bot_broadcast():
    token = os.getenv("BOT_TOKEN")
    group_ids_str = os.getenv("TEST_GROUP_IDS", "")

    if not token or not group_ids_str.strip():
        pytest.skip("TEST_GROUP_IDS or BOT_TOKEN not set")

    group_ids = [g.strip() for g in group_ids_str.split(",") if g.strip()]
    if not group_ids:
        pytest.skip("No group IDs provided")

    bot = Bot(token=token, parse_mode="HTML")

    available_groups = []

    for gid in group_ids:
        try:
            chat = await bot.get_chat(gid)
            print(f"[OK] Доступ к чату {gid}: {chat.title}")
            available_groups.append(gid)
        except TelegramUnauthorizedError:
            print(f"[SKIP] Нет доступа к чату {gid}")
        except TelegramBadRequest:
            print(f"[ERR] Чат {gid} не найден")
        await asyncio.sleep(0.5)  # чтобы не спамить API

    if not available_groups:
        pytest.skip("Нет доступных групп для теста")

    # Отправляем тестовое сообщение в каждую доступную группу
    for gid in available_groups:
        try:
            await bot.send_message(gid, "🚀 Тестовое сообщение (E2E)")
            print(f"[SEND] Сообщение отправлено в {gid}")
        except Exception as e:
            pytest.fail(f"Ошибка при отправке в {gid}: {e}")

    # Имитация рассылки
    for gid in available_groups:
        try:
            await bot.send_message(gid, "📢 Тестовая рассылка завершена успешно.")
            print(f"[BROADCAST] Успех в {gid}")
        except Exception as e:
            pytest.fail(f"Ошибка рассылки в {gid}: {e}")

    await bot.session.close()
