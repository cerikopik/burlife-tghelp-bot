import os # ⭐ Импортируем библиотеку для работы с переменными окружения
import asyncio
from telegram import Bot
from telegram.ext import Application, MessageHandler, CommandHandler, filters

# --- СЕКРЕТНЫЕ ДАННЫЕ БЕРУТСЯ ИЗ ОКРУЖЕНИЯ ---
# ⭐ Убираем токены из кода. Теперь скрипт будет брать их из настроек Render.
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

# Проверка, что переменные были успешно загружены
if not BOT_TOKEN or not GROUP_CHAT_ID:
    raise ValueError("Не найдены переменные окружения BOT_TOKEN или GROUP_CHAT_ID!")

# Преобразуем ID группы в число, так как переменные окружения всегда строки
GROUP_CHAT_ID = int(GROUP_CHAT_ID)
# --- КОНЕЦ БЛОКА С ДАННЫМИ ---


# Функция 1: Приветствует пользователя по команде /start
async def start(update, context):
    user_name = update.message.from_user.first_name
    welcome_text = (
        f"Здравствуйте, {user_name}!\n\n"
        "Я бот для связи с администрацией сайта. "
        "Вы можете написать здесь свой вопрос или оставить отзыв.\n\n"
        "Просто отправьте сообщение, и я его передам. Вы также можете прикреплять фото."
    )
    await update.message.reply_text(welcome_text)

# (Остальные функции forwarder и reply_to_user остаются без изменений)

async def forwarder(update, context):
    user = update.message.from_user
    user_info = (
        f"📩 Новое сообщение от пользователя:\n\n"
        f"👤 Имя: {user.first_name} {user.last_name or ''}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🔗 Юзернейм: @{user.username or 'не указан'}"
    )
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=user_info,
        parse_mode='Markdown'
    )
    await context.bot.forward_message(
        chat_id=GROUP_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )

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