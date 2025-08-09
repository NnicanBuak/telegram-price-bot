# tests/test_e2e.py
import os
import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from src.menu_system import create_mailing  # или твоя функция создания рассылки


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_bot_workflow():
    token = os.getenv("TEST_BOT_TOKEN")
    group_ids = os.getenv("TEST_GROUP_IDS")

    if not token or not group_ids:
        pytest.skip("TEST_BOT_TOKEN или TEST_GROUP_IDS не заданы")

    bot = Bot(token=token)
    group_ids = [gid.strip() for gid in group_ids.split(",")]

    for gid in group_ids:
        try:
            chat = await bot.get_chat(gid)
            assert chat.type in ("group", "supergroup")
        except TelegramAPIError as e:
            pytest.fail(f"Не удалось получить доступ к группе {gid}: {e}")

        # Проверка возможности отправить сообщение
        try:
            await bot.send_message(gid, "✅ Тестовое сообщение E2E")
        except TelegramAPIError as e:
            pytest.fail(f"Не удалось отправить сообщение в группу {gid}: {e}")

    # Создаём тестовую рассылку
    mailing_id = await create_mailing(
        title="Тестовая рассылка",
        message="Это сообщение отправлено в рамках E2E теста",
        target_groups=group_ids,
    )

    assert mailing_id is not None
