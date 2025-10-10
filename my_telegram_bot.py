import os
import asyncio
from telegram import Bot
from telegram.helpers import escape_markdown
from telegram.ext import Application, MessageHandler, CommandHandler, filters

# --- СЕКРЕТНЫЕ ДАННЫЕ БЕРУТСЯ ИЗ ОКРУЖЕНИЯ ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

if not BOT_TOKEN or not GROUP_CHAT_ID:
    raise ValueError("Не найдены переменные окружения BOT_TOKEN или GROUP_CHAT_ID!")

GROUP_CHAT_ID = int(GROUP_CHAT_ID)
# --- КОНЕЦ БЛОКА С ДАННЫМИ ---


async def start(update, context):
    """Отправляет приветственное сообщение в ответ на команду /start."""
    user_name = update.message.from_user.first_name
    welcome_text = (
        f"Здравствуйте, {user_name}!\n\n"
        "Я бот для связи с администрацией сайта. "
        "Вы можете написать здесь свой вопрос или оставить отзыв.\n\n"
        "Просто отправьте сообщение, и я его передам. Вы также можете прикреплять фото."
    )
    await update.message.reply_text(welcome_text)


async def forwarder(update, context):
    """Пересылает сообщение пользователя и добавляет информацию о нем."""
    user = update.message.from_user
    first_name = escape_markdown(user.first_name, version=2)
    last_name = escape_markdown(user.last_name or '', version=2)
    user_id = user.id
    username = escape_markdown(user.username or 'не указан', version=2)
    user_info = (
        f"📩 Новое сообщение от пользователя:\n\n"
        f"👤 Имя: {first_name} {last_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"🔗 Юзернейм: @{username}"
    )
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=user_info,
        parse_mode='MarkdownV2'
    )
    await context.bot.forward_message(
        chat_id=GROUP_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    await update.message.reply_text("Спасибо! Ваше сообщение принято. Мы скоро с вами свяжемся.")

# ↓↓↓ ОСНОВНЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ ↓↓↓
async def reply_to_user(update, context):
    """Отправляет ответ админа обратно пользователю или сообщает об ошибке."""
    # Проверяем, что это ответ на сообщение
    if not update.message.reply_to_message:
        return

    replied_to_msg = update.message.reply_to_message

    # ГЛАВНАЯ ПРОВЕРКА: есть ли информация об оригинальном отправителе?
    if replied_to_msg.forward_from:
        # УСПЕХ: отправляем сообщение как обычно
        original_user_id = replied_to_msg.forward_from.id
        await context.bot.copy_message(
            chat_id=original_user_id,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
        await update.message.add_reaction("✅")
    else:
        # НЕУДАЧА: отправляем диагностическое сообщение в группу
        error_text = ""
        # Проверяем, не скрыл ли пользователь свой профиль
        if replied_to_msg.forward_sender_name:
            error_text = "❌ **Ошибка:** Не могу ответить. Пользователь скрыл свой профиль в настройках приватности (Пересылка сообщений). Ответить ему через бота невозможно."
        # Проверяем, не ответили ли мы на сообщение самого бота
        elif replied_to_msg.from_user.is_bot:
            error_text = "❌ **Ошибка:** Вы ответили на служебное сообщение бота, а не на пересланное сообщение пользователя. Пожалуйста, отвечайте на другое сообщение."
        else:
            error_text = "❌ **Ошибка:** Это сообщение не является пересланным от пользователя. Не могу определить, кому отвечать."
        
        await update.message.reply_text(error_text, parse_mode='Markdown')

def main():
    """Запускает бота и настраивает все обработчики."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    # ВАЖНО: reply_handler должен стоять ПЕРЕД forwarder, чтобы он перехватывал ответы в группе
    application.add_handler(MessageHandler(filters.REPLY & filters.Chat(chat_id=GROUP_CHAT_ID), reply_to_user))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Chat(chat_id=GROUP_CHAT_ID), forwarder))
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()
