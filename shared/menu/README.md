# 🏗️ Система меню для Telegram ботов

Полноценная система сборки, рендеринга и навигации между меню для aiogram ботов.

## 📋 Содержание

- [Возможности](#-возможности)
- [Быстрый старт](#-быстрый-старт)
- [Основные компоненты](#-основные-компоненты)
- [Создание меню](#-создание-меню)
- [Навигация](#-навигация)
- [Обработчики](#-обработчики)
- [Продвинутые возможности](#-продвинутые-возможности)
- [API Reference](#-api-reference)
- [Примеры](#-примеры)

## ✨ Возможности

- 🏗️ **Флуентный API** для создания меню
- 🧭 **Автоматическая навигация** между меню
- 💾 **Управление состоянием** пользователей
- 🔐 **Права доступа** (admin-only меню/кнопки)
- 📱 **Адаптивные клавиатуры** с колонками
- 🎨 **Готовые шаблоны** (CRUD, подтверждения)
- 🔄 **История навигации** с кнопкой "Назад"
- 🎯 **Декораторы** для упрощения кода
- 📊 **Контекст пользователей** для передачи данных

## 🚀 Быстрый старт

### 1. Подключение

```python
from menu import create_menu_system, MenuBuilder

# Создаем систему меню
menu_manager, menu_registry = create_menu_system([123456789])  # ID админов
```

### 2. Создание меню

```python
# Простое меню
main_menu = (MenuBuilder("main")
    .title("🏠 Главное меню")
    .description("Выберите нужный раздел:")
    .add_menu_link("Настройки", "settings", "⚙️")
    .add_action("Помощь", "help", "❓")
    .no_back_button()  # Главное меню без кнопки назад
    .build())

# Регистрируем меню
menu_manager.register_menu(main_menu)
```

### 3. Обработка в коде

```python
from aiogram import Router, types, F
from shared.menu import menu_handler

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Показать главное меню"""
    await menu_manager.navigate_to("main", message, message.from_user.id)

@router.callback_query(F.data.startswith("menu_"))
async def handle_navigation(callback: types.CallbackQuery):
    """Автоматическая навигация между меню"""
    await menu_manager.handle_callback(callback)

@menu_handler(menu_manager, "help")
async def show_help(callback: types.CallbackQuery, context: dict):
    """Обработчик кнопки помощи"""
    await callback.message.answer("Это справка по боту!")
```

## 🧩 Основные компоненты

### MenuBuilder

Флуентный API для создания меню:

```python
menu = (MenuBuilder("menu_id")
    .title("Заголовок")                    # Заголовок меню  
    .description("Описание")               # Описание под заголовком
    .columns(2)                            # Количество колонок (1-3)
    .admin_only(True)                      # Только для админов
    .add_action("Текст", "callback", "🔥") # Кнопка действия
    .add_menu_link("Настройки", "settings", "⚙️") # Ссылка на меню
    .add_url("Сайт", "https://example.com", "🌐")  # URL кнопка
    .back_button("main")                   # Кнопка назад
    .build())
```

### MenuManager

Управление навигацией и состоянием:

```python
# Переход к меню
await menu_manager.navigate_to("settings", callback, user_id)

# Возврат назад
await menu_manager.go_back(callback, user_id)

# Работа с контекстом
menu_manager.set_user_context(user_id, selected_item=123)
context = menu_manager.get_user_context(user_id)

# Текущее меню пользователя
current = menu_manager.get_current_menu(user_id)
```

## 🏗️ Создание меню

### Типы кнопок

#### 1. Кнопка действия

```python
.add_action("Создать", "create_item", "➕", admin_only=False)
```

#### 2. Ссылка на другое меню

```python
.add_menu_link("Настройки", "settings", "⚙️", admin_only=True)
# Автоматически создает callback_data="menu_settings"
```

#### 3. URL кнопка

```python
.add_url("Документация", "https://docs.example.com", "📖")
```

#### 4. Подтверждение/Отмена

```python
.add_confirm_cancel(
    confirm_text="✅ Да", 
    cancel_text="❌ Нет",
    confirm_callback="confirm_delete",
    cancel_callback="cancel_delete"
)
```

### Готовые шаблоны

#### CRUD меню

```python
from shared.menu import create_crud_menu

templates_menu = (create_crud_menu("templates", "Шаблоны сообщений")
    .add_action("Экспорт", "export_all", "📤", admin_only=True)
    .build())

# Автоматически создает кнопки:
# ➕ Создать -> templates_create
# 📋 Список -> templates_list  
# ◀️ Назад -> menu_main
```

#### Меню подтверждения

```python
from shared.menu import create_confirmation_menu

confirm_menu = (create_confirmation_menu(
    "confirm_delete",
    "⚠️ Удалить элемент?",
    "delete_confirmed", 
    "delete_cancelled"
).build())
```

#### Простое меню

```python
from shared.menu import create_simple_menu

about_menu = (create_simple_menu("about", "ℹ️ О боте", "Информация о боте")
    .add_action("Версия", "show_version", "🔢")
    .add_url("GitHub", "https://github.com/user/repo", "🐙")
    .build())
```

## 🧭 Навигация

### Автоматическая навигация

Система автоматически обрабатывает переходы:

```python
# В любом меню кнопка с target_menu="settings" 
# создает callback_data="menu_settings"

@router.callback_query(F.data.startswith("menu_"))
async def handle_navigation(callback: types.CallbackQuery):
    """Обрабатывает все переходы menu_* автоматически"""
    success = await menu_manager.handle_callback(callback)
    if not success:
        await callback.answer("❌ Меню не найдено")
```

### Ручная навигация

```python
# Переход к конкретному меню
await menu_manager.navigate_to("settings", message, user_id)

# С передачей контекста
context = {"selected_template": 123, "action": "edit"}
await menu_manager.navigate_to("templates", callback, user_id, context)

# Возврат назад
await menu_manager.go_back(callback, user_id)
```

### История навигации

```python
# Автоматически ведется история до 10 последних меню
# Кнопка "Назад" использует эту историю

# Получить историю
state = menu_manager._get_user_state(user_id)
print(f"История: {state.history}")

# Очистить навигацию
menu_manager.clear_navigation(user_id)
```

## 🎯 Обработчики

### Декоратор для callback'ов

```python
from shared.menu import menu_handler

@menu_handler(menu_manager, "help")
async def handle_help(callback: types.CallbackQuery, context: dict):
    """Обработчик кнопки помощи"""
    await callback.message.answer("Справка по боту")
    await callback.answer()

@menu_handler(menu_manager, "create_*")  # Поддержка wildcards
async def handle_create(callback: types.CallbackQuery, context: dict):
    """Обработчик всех create_* действий"""
    action = callback.data  # "create_template", "create_group", etc.
```

### Декоратор для открытия меню

```python
from shared.menu import menu_opener

@menu_opener(menu_manager, "settings")
async def on_settings_open(target, user_id: int, context: dict):
    """Вызывается при открытии меню настроек"""
    print(f"Пользователь {user_id} открыл настройки")
    
    # Можно добавить проверки, логирование, etc.
    if context.get('is_admin'):
        print("Администратор получил доступ к настройкам")
```

### Ручная регистрация

```python
async def custom_handler(callback: types.CallbackQuery, context: dict):
    await callback.message.answer("Кастомный обработчик")

menu_manager.register_callback_handler("custom_action", custom_handler)
```

## 🔧 Продвинутые возможности

### Контекст пользователей

```python
# Сохранение данных между меню
menu_manager.set_user_context(user_id, 
    selected_template=123,
    edit_mode=True,
    original_message_id=callback.message.message_id
)

# Получение в обработчике
@menu_handler(menu_manager, "save_changes")
async def save_changes(callback: types.CallbackQuery, context: dict):
    template_id = context.get('selected_template')
    edit_mode = context.get('edit_mode', False)
    
    if edit_mode and template_id:
        # Логика сохранения
        pass
```

### Права доступа

```python
# Меню только для админов
admin_menu = (MenuBuilder("admin_panel")
    .title("👨‍💼 Админ-панель")
    .admin_only(True)  # Весь меню только для админов
    .add_action("Обычная функция", "normal_action")
    .add_action("Админ функция", "admin_action", admin_only=True)  # Конкретная кнопка
    .build())
```

### Динамическое содержимое

```python
# В описании можно использовать переменные
menu = (MenuBuilder("profile")
    .title("👤 Профиль")
    .description("Добро пожаловать, {user_name}!\nВаш ID: {user_id}")
    .build())

# При отображении передать контекст
context = {"user_name": "Иван", "user_id": 123456789}
await menu_manager.navigate_to("profile", callback, user_id, context)
```

### Кастомный рендеринг

```python
def custom_renderer(menu_structure, context):
    # Кастомная логика рендеринга
    text = f"🎨 {menu_structure.config.title}\n\nКастомный рендеринг!"
    
    # Можно создать свою клавиатуру
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Кастомная кнопка", callback_data="custom")]
    ])
    
    return MenuResponse(text=text, keyboard_markup=keyboard)

# Регистрация кастомного рендерера
menu_manager.renderer.register_custom_renderer("special_menu", custom_renderer)
```

### Группировка меню

```python
# Организация меню по группам
menu_registry.register_menu_group("features", ["templates", "groups", "mailing"])
menu_registry.register_menu_group("admin", ["settings", "logs", "backup"])
```

## 📚 API Reference

### MenuBuilder

| Метод | Описание | Параметры |
|-------|----------|-----------|
| `title(title)` | Заголовок меню | `title: str` |
| `description(desc)` | Описание | `desc: str` |
| `columns(count)` | Колонки (1-3) | `count: int` |
| `admin_only(flag)` | Только админы | `flag: bool = True` |
| `add_action(text, callback, icon, admin_only)` | Кнопка действия | См. параметры ниже |
| `add_menu_link(text, target, icon, admin_only)` | Ссылка на меню | См. параметры ниже |
| `add_url(text, url, icon, admin_only)` | URL кнопка | См. параметры ниже |
| `add_confirm_cancel()` | Подтверждение/отмена | См. параметры ниже |
| `back_button(target, text)` | Кнопка назад | `target: str, text: str = "◀️ Назад"` |
| `no_back_button()` | Отключить кнопку назад | - |
| `build()` | Собрать меню | Возвращает `MenuStructure` |

#### Параметры кнопок

- `text: str` - Текст кнопки
- `callback/target/url: str` - Данные кнопки  
- `icon: str = ""` - Иконка (эмодзи)
- `admin_only: bool = False` - Только для админов

### MenuManager

| Метод | Описание |
|-------|----------|
| `register_menu(menu)` | Регистрация меню |
| `navigate_to(menu_id, target, user_id, context)` | Переход к меню |
| `go_back(target, user_id, context)` | Возврат назад |
| `handle_callback(callback, context)` | Обработка callback |
| `get_current_menu(user_id)` | Текущее меню |
| `set_user_context(user_id, **context)` | Установить контекст |
| `get_user_context(user_id)` | Получить контекст |
| `clear_navigation(user_id)` | Очистить навигацию |

## 💡 Примеры

### Полный пример CRUD системы

```python
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from shared.menu import (
    create_menu_system, MenuBuilder, create_crud_menu,
    menu_handler, menu_opener
)

# Инициализация
menu_manager, menu_registry = create_menu_system([123456789])
router = Router()

class TemplateStates(StatesGroup):
    waiting_name = State()
    waiting_text = State()

# === СОЗДАНИЕ МЕНЮ ===

def setup_menus():
    # Главное меню
    main_menu = (MenuBuilder("main")
        .title("🏠 Главное меню")
        .description("Telegram Bot для управления шаблонами")
        .add_menu_link("Шаблоны", "templates", "📄")
        .add_menu_link("Настройки", "settings", "⚙️", admin_only=True)
        .add_action("Помощь", "help", "❓")
        .no_back_button()
        .build())
    
    # CRUD меню для шаблонов
    templates_menu = (create_crud_menu("templates", "Шаблоны сообщений")
        .add_action("Экспорт", "export_templates", "📤", admin_only=True)
        .build())
    
    # Меню настроек
    settings_menu = (MenuBuilder("settings")
        .title("⚙️ Настройки")
        .admin_only(True)
        .add_action("Логи", "show_logs", "📋")
        .add_action("Статистика", "show_stats", "📊")
        .back_button("main")
        .build())
    
    # Регистрация
    for menu in [main_menu, templates_menu, settings_menu]:
        menu_manager.register_menu(menu)

# === ОБРАБОТЧИКИ ===

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await menu_manager.navigate_to("main", message, message.from_user.id)

@router.callback_query(F.data.startswith("menu_") | F.data == "back")
async def handle_navigation(callback: types.CallbackQuery):
    await menu_manager.handle_callback(callback)

@menu_handler(menu_manager, "help")
async def show_help(callback: types.CallbackQuery, context: dict):
    help_text = """❓ <b>Справка по боту</b>

🔹 <b>Шаблоны</b> - создание и управление шаблонами сообщений
🔹 <b>Настройки</b> - конфигурация бота (только админы)

<b>Команды:</b>
/start - главное меню
/help - эта справка"""
    
    await callback.message.edit_text(help_text)
    await callback.answer()

@menu_handler(menu_manager, "templates_create")
async def create_template(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ <b>Создание шаблона</b>\n\n"
        "Введите название шаблона:"
    )
    await state.set_state(TemplateStates.waiting_name)
    await callback.answer()

@router.message(TemplateStates.waiting_name)
async def process_template_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    
    if len(name) < 3:
        await message.answer("❌ Название слишком короткое")
        return
    
    await state.update_data(name=name)
    await message.answer(f"✅ Название: {name}\n\nТеперь введите текст шаблона:")
    await state.set_state(TemplateStates.waiting_text)

@router.message(TemplateStates.waiting_text)
async def process_template_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Здесь сохранение в БД
    # template = await database.create_template(data['name'], message.text)
    
    await message.answer(
        f"✅ <b>Шаблон создан!</b>\n\n"
        f"📝 Название: {data['name']}\n"
        f"📄 Текст: {message.text[:50]}..."
    )
    
    await state.clear()
    
    # Возвращаемся к меню шаблонов
    await menu_manager.navigate_to("templates", message, message.from_user.id)

@menu_opener(menu_manager, "settings")
async def on_settings_open(target, user_id: int, context: dict):
    print(f"Админ {user_id} открыл настройки")

# Инициализация
setup_menus()
```

### Пример с пагинацией

```python
@menu_handler(menu_manager, "templates_list")
async def show_templates_list(callback: types.CallbackQuery, context: dict):
    # Получаем шаблоны из БД
    templates = await database.get_templates()
    page = context.get('page', 0)
    
    if not templates:
        await callback.message.edit_text(
            "📄 <b>Список шаблонов</b>\n\n❌ Шаблоны не найдены",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Создать", callback_data="templates_create")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_templates")]
            ])
        )
        return
    
    # Пагинация
    items_per_page = 5
    start = page * items_per_page
    end = start + items_per_page
    page_templates = templates[start:end]
    
    text = f"📄 <b>Список шаблонов</b>\n\n📊 Найдено: {len(templates)}\n\n"
    
    keyboard = []
    
    # Кнопки шаблонов
    for template in page_templates:
        icon = "📎" if template.file_id else "📄"
        keyboard.append([InlineKeyboardButton(
            text=f"{icon} {template.name}",
            callback_data=f"view_template_{template.id}"
        )])
    
    # Навигация по страницам
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️", callback_data=f"templates_list_page_{page-1}"
        ))
    
    if end < len(templates):
        nav_row.append(InlineKeyboardButton(
            text="▶️", callback_data=f"templates_list_page_{page+1}"
        ))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Дополнительные кнопки
    keyboard.extend([
        [InlineKeyboardButton(text="➕ Создать", callback_data="templates_create")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_templates")]
    ])
    
    await callback.message.edit_text(
        text, 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

# Обработчик пагинации
@menu_handler(menu_manager, "templates_list_page_*")
async def handle_templates_page(callback: types.CallbackQuery, context: dict):
    page = int(callback.data.split("_")[-1])
    context['page'] = page
    await show_templates_list(callback, context)
```

## 🐛 Troubleshooting

### Частые проблемы

**1. Меню не отображается**

```python
# Проверьте регистрацию меню
if not menu_manager.has_menu("my_menu"):
    print("Меню не зарегистрировано!")

# Проверьте права доступа
menu = menu_manager.get_menu("admin_menu")
if menu.config.admin_only:
    print("Меню только для админов")
```

**2. Callback не обрабатывается**

```python
# Убедитесь, что зарегистрирован обработчик навигации
@router.callback_query(F.data.startswith("menu_"))
async def handle_navigation(callback: types.CallbackQuery):
    success = await menu_manager.handle_callback(callback)
    if not success:
        print(f"Необработанный callback: {callback.data}")
```

**3. Кнопки не работают**

```python
# Проверьте callback_data
button = MenuButton(
    text="Тест",
    button_type=ButtonType.ACTION,
    callback_data="test_action"  # Должно быть установлено!
)

# Зарегистрируйте обработчик
@menu_handler(menu_manager, "test_action")
async def handle_test(callback, context):
    await callback.answer("Работает!")
```

### Отладка

```python
# Статистика системы меню
stats = menu_manager.get_menu_statistics()
print(f"Меню: {stats['total_menus']}")
print(f"Активные пользователи: {stats['active_users']}")

# Состояние пользователя
state = menu_manager.export_navigation_state(user_id)
print(f"Текущее меню: {state['current_menu']}")
print(f"История: {state['history']}")

# Список зарегистрированных меню
print(f"Доступные меню: {list(menu_manager._menus.keys())}")
```
