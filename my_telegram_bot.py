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

    # ⭐ 1. Создаем инлайн-кнопку
    keyboard = [
        [InlineKeyboardButton("Ответить шаблоном", callback_data=f"reply_to_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ⭐ 2. Отправляем сообщение с прикрепленной кнопкой
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=user_info,
        parse_mode='MarkdownV2',
        reply_markup=reply_markup  # Прикрепляем нашу кнопку
    )
    
    await context.bot.forward_message(
        chat_id=GROUP_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    
    await update.message.reply_text("Спасибо! Ваше сообщение принято. Мы скоро с вами свяжемся.")


# ⭐ 3. НОВАЯ ФУНКЦИЯ для обработки нажатий на кнопку
async def button_handler(update, context):
    """Обрабатывает нажатия на инлайн-кнопки."""
    query = update.callback_query
    await query.answer()  # Обязательно "отвечаем" на нажатие

    # Разбираем данные из кнопки, например "reply_to_123456"
    data = query.data
    if data.startswith("reply_to_"):
        user_id = int(data.split("_")[2])

        # Здесь находится ваш шаблонный ответ
        preset_message = "Здравствуйте! Ваше обращение получено и принято в обработку. Спасибо!"

        try:
            # Отправляем шаблон пользователю
            await context.bot.send_message(chat_id=user_id, text=preset_message)
            
            # Редактируем исходное сообщение в группе, чтобы убрать кнопку и добавить пометку
            await query.edit_message_text(
                text=query.message.text + "\n\n✅ **Ответ-шаблон успешно отправлен.**",
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            # Если не удалось отправить (например, пользователь заблокировал бота), сообщаем админу
            await query.edit_message_text(
                text=query.message.text + f"\n\n❌ **Не удалось отправить ответ.** Ошибка: {e}",
                parse_mode='MarkdownV2'
            )


def main():
    """Запускает бота и настраивает все обработчики."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))  # ⭐ 4. Добавляем обработчик кнопок
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Chat(chat_id=GROUP_CHAT_ID), forwarder))
    
    print("Бот запущен (с кнопками)...")
    application.run_polling()


if __name__ == '__main__':
    main()
