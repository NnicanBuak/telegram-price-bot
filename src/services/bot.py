import logging
from typing import Union, Dict, Any
from aiogram import types

logger = logging.getLogger(__name__)


async def show_main_menu(
    target: Union[types.Message, types.CallbackQuery],
    user_id: int,
    menu_manager,
    context: Dict[str, Any] = None,
) -> bool:
    """
    Показать главное меню пользователю (через событие)

    Args:
        target: Message или CallbackQuery для отправки
        user_id: ID пользователя
        menu_manager: Менеджер меню
        context: Дополнительный контекст

    Returns:
        bool: Успешность операции
    """
    try:
        success = await menu_manager.navigate_to("main", target, user_id, context)
        if success:
            logger.info(f"Главное меню отправлено пользователю {user_id}")
        return success
    except Exception as e:
        logger.error(f"Ошибка отправки главного меню: {e}")
        return False


async def get_help_text() -> str:
    """Получить текст справки"""
    return """📋 <b>Справка по боту</b>

<b>🔹 Основные функции:</b>
- <b>Шаблоны</b> - создание сообщений с файлами и текстом
- <b>Группы</b> - объединение чатов для рассылки
- <b>Рассылка</b> - отправка по выбранным группам
- <b>История</b> - статистика и мониторинг отправок

<b>🔹 Команды:</b>
/start - главное меню
/help - эта справка
/id - получить ID чата
/config - информация о конфигурации
/status - статус системы

<b>🔹 Как начать:</b>
1. Создайте шаблон сообщения
2. Добавьте группы чатов (получите ID командой /id в чатах)
3. Запустите рассылку

<b>💡 Совет:</b> Добавьте бота в чаты как администратора для корректной работы."""


def get_chat_info(message: types.Message) -> str:
    """Получить информацию о чате"""
    chat_type_names = {
        "private": "Приватный чат",
        "group": "Группа",
        "supergroup": "Супергруппа",
        "channel": "Канал",
    }

    info = (
        f"💬 <b>Информация о чате</b>\n\n"
        f"🔢 <b>ID чата:</b> <code>{message.chat.id}</code>\n"
        f"📱 <b>Тип:</b> {chat_type_names.get(message.chat.type, message.chat.type)}\n"
        f"👤 <b>Ваш ID:</b> <code>{message.from_user.id}</code>\n"
    )

    if message.chat.title:
        info += f"📝 <b>Название:</b> {message.chat.title}\n"
    if message.from_user.username:
        info += f"📮 <b>Username:</b> @{message.from_user.username}\n"

    info += "\n💡 <i>Используйте ID чата для добавления в группы рассылки</i>"

    return info


async def send_startup_notification(user_id: int, bot) -> bool:
    """
    Отправить уведомление о запуске бота

    Args:
        user_id: ID пользователя
        bot: Экземпляр бота

    Returns:
        bool: Успешность отправки
    """
    try:
        await bot.send_message(
            chat_id=user_id,
            text="🚀 <b>Бот запущен</b>\n\nВсе системы готовы к работе!",
            parse_mode="HTML",
        )
        return True
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        return False
