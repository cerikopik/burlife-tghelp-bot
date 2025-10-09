import os
import asyncio
from telegram import Bot
# ⭐ 1. Импортируем новую вспомогательную функцию
from telegram.helpers import escape_markdown
from telegram.ext import Application, MessageHandler, CommandHandler, filters

# --- СЕКРЕТНЫЕ ДАННЫЕ БЕРУТСЯ ИЗ ОКРУЖЕНИЯ ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

if not BOT_TOKEN or not GROUP_CHAT_ID:
    raise ValueError("Не найдены переменные окружения BOT_TOKEN или GROUP_CHAT_ID!")

GROUP_CHAT_ID = int(GROUP_CHAT_ID)
# --- КОНЕЦ БЛОКА С ДАННЫЯМИ ---


async def start(update, context):
    user_name = update.message.from_user.first_name
    welcome_text = (
        f"Здравствуйте, {user_name}!\n\n"
        "Я бот для связи с администрацией сайта. "
        "Вы можете написать здесь свой вопрос или оставить отзыв.\n\n"
        "Просто отправьте сообщение, и я его передам. Вы также можете прикреплять фото."
    )
    await update.message.reply_text(welcome_text)

# ↓↓↓ ИЗМЕНЕНИЯ ТОЛЬКО В ЭТОЙ ФУНКЦИИ ↓↓↓
async def forwarder(update, context):
    """Пересылает сообщение пользователя и добавляет информацию о нем."""
    user = update.message.from_user

    # ⭐ 2. Экранируем все данные от пользователя перед вставкой в строку
    first_name = escape_markdown(user.first_name, version=2)
    last_name = escape_markdown(user.last_name or '', version=2)
    user_id = user.id # ID - это число, его экранировать не нужно
    username = escape_markdown(user.username or 'не указан', version=2)

    # Собираем сообщение, используя уже безопасные переменные
    user_info = (
        f"📩 Новое сообщение от пользователя:\n\n"
        f"👤 Имя: {first_name} {last_name}\n"
        f"🆔 ID: `{user_id}`\n" # Оставляем Markdown для ID
        f"🔗 Юзернейм: @{username}"
    )

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=user_info,
        # ⭐ 3. Используем рекомендованный MarkdownV2
        parse_mode='MarkdownV2'
    )
    await context.bot.forward_message(
        chat_id=GROUP_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
# ↑↑↑ ИЗМЕНЕНИЯ ТОЛЬКО В ЭТОЙ ФУНКЦИИ ↑↑↑

async def reply_to_user(update, context):
    if update.message.chat_id == GROUP_CHAT_ID:
        if update.message.reply_to_message and update.message.reply_to_message.forward_from:
            original_user_id = update.message.reply_to_message.forward_from.id
            await context.bot.copy_message(
                chat_id=original_user_id,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            await update.message.add_reaction("✅")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.REPLY & filters.Chat(chat_id=GROUP_CHAT_ID), reply_to_user))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Chat(chat_id=GROUP_CHAT_ID), forwarder))
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
