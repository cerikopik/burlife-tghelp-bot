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
        "Пожалуйста, введите ваш код (4 символа) или отправьте фотографию."
    )
    await update.message.reply_text(welcome_text)


async def forwarder(update, context):
    """Проверяет сообщение (код или фото) и, если оно верное, пересылает его."""
    user = update.message.from_user
    message = update.message

    # ⭐ 3. Исправлена и переписана логика проверки
    is_valid = False
    if message.photo:
        is_valid = True
    elif message.text:
        # Проверяем, что текст состоит из 4 символов и содержит только латинские буквы и цифры
        if len(message.text) == 4 and message.text.isascii() and message.text.isalnum():
            is_valid = True

    if is_valid:
        # --- УСПЕХ: Сообщение верное, выполняем все старые действия ---
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

        # ⭐ 1. Исправлено расположение кнопок (одна под другой)
        keyboard = [
            [InlineKeyboardButton("✅ Ответить шаблоном", callback_data=f"reply_to_{user_id}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_to_{user_id}")]
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
            from_chat_id=message.chat_id,
            message_id=message.message_id
        )
        
        await message.reply_text("Спасибо! Ваше сообщение принято. Мы скоро с вами свяжемся.")
    
    else:
        # --- НЕУДАЧА: Сообщение неверное, отправляем ошибку пользователю ---
        error_message = "❗️ **Ошибка.** Пожалуйста, отправьте код, состоящий ровно из 4 символов (латинские буквы и цифры), или фотографию."
        await message.reply_text(error_message, parse_mode='Markdown')


async def button_handler(update, context):
    """Обрабатывает нажатия на инлайн-кнопки."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[2])
    
    try:
        # ⭐ 2. Исправлена логика отправки для кнопки "Отклонить"
        if data.startswith("reply_to_"):
            preset_message = "📧 Ваша [ПРИГЛАСИТЕЛЬНАЯ ССЫЛКА](https://t\\.me/\\+k2dfZY9KPAowNjM6) в телеграм канал\\. После перехода по ссылке нажмите подать заявку, и она будет одобрена автоматически 👌"
            await context.bot.send_message(
                chat_id=user_id,
                text=preset_message,
                parse_mode='MarkdownV2'
            )
            await query.message.set_reaction(reaction=ReactionTypeEmoji("👍"))

        elif data.startswith("decline_to_"):
            preset_message = "К сожалению, ваша заявка была отклонена. Попробуйте позже."
            # Отправляем как простой текст, без parse_mode
            await context.bot.send_message(
                chat_id=user_id,
                text=preset_message
            )
            await query.message.set_reaction(reaction=ReactionTypeEmoji("👎"))
        
        # Убираем обе кнопки в любом успешном случае
        await query.edit_message_reply_markup(reply_markup=None)

    except Exception as e:
        await query.edit_message_reply_markup(reply_markup=None)
        print(f"Не удалось отправить ответ пользователю {user_id}. Ошибка: {e}")


def main():
    """Запускает бота и настраивает все обработчики."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), chat_id=~int(GROUP_CHAT_ID), callback=forwarder))
    
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()
