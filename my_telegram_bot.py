import os
import re
import asyncio
from telegram import Bot, ReactionTypeEmoji, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackQueryHandler

# --- СЕКРЕТНЫЕ ДАННЫЕ БЕРУТСЯ ИЗ ОКРУЖЕНИЯ ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

if not BOT_TOKEN or not GROUP_CHAT_ID:
    raise ValueError("Не найдены переменные окружения BOT_TOKEN или GROUP_CHAT_ID!")

GROUP_CHAT_ID = int(GROUP_CHAT_ID)
# --- КОНЕЦ БЛОКА С ДАННЫЯМИ ---


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
    """Пересылает сообщение пользователя и добавляет информацию о нем с кнопкой."""
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

    keyboard = [
        [InlineKeyboardButton("Ответить шаблоном", callback_data=f"reply_to_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=user_info,
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )
    
    await context.bot.forward_message(
        chat_id=GROUP_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    
    await update.message.reply_text("Спасибо! Ваше сообщение принято. Мы скоро с вами свяжемся.")


# ↓↓↓ ИЗМЕНЕНИЯ ЗДЕСЬ ↓↓↓
async def button_handler(update, context):
    """Обрабатывает нажатия на инлайн-кнопки."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("reply_to_"):
        user_id = int(data.split("_")[2])

        preset_message = "Здравствуйте! Ваше обращение получено и принято в обработку. Спасибо!"

        try:
            await context.bot.send_message(chat_id=user_id, text=preset_message)
            
            # ⭐ Вместо изменения текста, просто убираем клавиатуру (кнопку)
            await query.edit_message_reply_markup(reply_markup=None)
            
            # Опционально: можно уведомить админа короткой подсказкой
            await query.answer(text="✅ Ответ-шаблон успешно отправлен!")

        except Exception as e:
            # В случае ошибки также убираем кнопку и сообщаем об ошибке
            await query.edit_message_reply_markup(reply_markup=None)
            await query.answer(text=f"❌ Не удалось отправить ответ. Ошибка: {e}", show_alert=True)


def main():
    """Запускает бота и настраивает все обработчики."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Chat(chat_id=GROUP_CHAT_ID), forwarder))
    
    print("Бот запущен (с удалением кнопок)...")
    application.run_polling()


if __name__ == '__main__':
    main()
